from __future__ import annotations
import asyncio
import logging
import time
from typing import Awaitable, Callable, Optional
from urllib.parse import urlparse

from nats.aio.client import Client as NATS
from nats.js.api import StreamConfig, ConsumerConfig, AckPolicy, DeliverPolicy
from nats.js import errors as js_err

from .config import NatsConfig
from .message import BusMessage, ReceivedMessage, H_MESSAGE_TYPE

log = logging.getLogger("natbus.client")

Handler = Callable[[ReceivedMessage], Awaitable[None]]


def _split_servers(s: str | list[str]) -> list[str]:
    if isinstance(s, str):
        return [p.strip() for p in s.split(",") if p.strip()]
    return [str(p).strip() for p in s if str(p).strip()]

def _normalize_servers(servers: list[str]) -> list[str]:
    if not servers:
        return ["nats://127.0.0.1:4222"]
    out: list[str] = []
    schemes: set[str] = set()
    for raw in servers:
        url = raw if "://" in raw else f"nats://{raw}"
        scheme = urlparse(url).scheme.lower()
        if scheme not in {"nats", "tls", "ws", "wss"}:
            raise ValueError(f"Unsupported NATS scheme: {scheme} in {raw}")
        schemes.add(scheme)
        out.append(url)
    if not (schemes <= {"nats", "tls"} or schemes <= {"ws", "wss"}):
        raise ValueError("Mixed WebSocket and TCP endpoints are not allowed")
    return out

def _norm_queue(q: Optional[str]) -> Optional[str]:
    if q is None:
        return None
    q = q.strip()
    return q or None

def _resolve_deliver_policy(val) -> DeliverPolicy:
    if isinstance(val, DeliverPolicy):
        return val
    if not val:
        return DeliverPolicy.NEW
    s = str(val).strip().lower()
    mapping = {
        "new": DeliverPolicy.NEW,
        "all": DeliverPolicy.ALL,
        "last": DeliverPolicy.LAST,
        "by_start_sequence": DeliverPolicy.BY_START_SEQUENCE,
        "by_start_time": DeliverPolicy.BY_START_TIME,
    }
    return mapping.get(s, DeliverPolicy.NEW)


class PullSubscription:
    def __init__(self, sub):
        self._sub = sub

    async def fetch(self, batch: int = 1, timeout: Optional[float] = None, no_wait: bool = False):
        if no_wait:
            nmsgs = await self._sub.fetch_no_wait(batch)
        else:
            nmsgs = await self._sub.fetch(batch, timeout=timeout)
        out = []
        for m in nmsgs:
            out.append(ReceivedMessage(
                subject=m.subject,
                data=m.data,
                headers=dict(m.headers or {}),
                _ack=m.ack,
                _nak=m.nak,
                _term=m.term,
            ))
        return out


class EphemeralPushHandle:
    def __init__(self, sub):
        self._sub = sub
    async def close(self):
        await self._sub.unsubscribe()


class NatsBus:
    def __init__(self, cfg: NatsConfig):
        self.cfg = cfg
        self._nc: Optional[NATS] = None
        self._js = None
        self._subs: list = []
        self._push_keys: dict[tuple[str, Optional[str], Handler], object] = {}
        self._dedupe_recent: dict[str, float] = {}
        self._dedupe_lock: Optional[asyncio.Lock] = None

    @property
    def nc(self) -> NATS:
        if not self._nc:
            raise RuntimeError("not connected")
        return self._nc

    # --- small helper to wrap JS admin calls with a timeout nicely ----------
    async def _with_timeout(self, coro, label: str):
        try:
            return await asyncio.wait_for(coro, timeout=self.cfg.js_api_timeout_s)
        except asyncio.TimeoutError as e:
            log.error("js_api_timeout", extra={"op": label, "timeout_s": self.cfg.js_api_timeout_s})
            raise RuntimeError(f"JS API timeout: {label}") from e

    async def _ensure_push_consumer(
        self,
        stream: str,
        subject: str,
        durable: str,
        queue: Optional[str],
        *,
        consumer_cfg: Optional[dict] = None,
    ) -> str:
        queue = _norm_queue(queue)
        cfg = consumer_cfg or {}

        dp = _resolve_deliver_policy(cfg.get("deliver_policy", self.cfg.deliver_policy))
        ack_wait = int(cfg.get("ack_wait", cfg.get("ack_wait_s", self.cfg.ack_wait_s)))
        max_ack_pending = int(cfg.get("max_ack_pending", self.cfg.max_ack_pending))

        log.info("js_consumer_bind_try", extra={
            "stream": stream, "durable": durable, "subject": subject, "queue": queue,
            "deliver_policy": str(dp), "ack_wait_s": ack_wait, "max_ack_pending": max_ack_pending,
        })

        try:
            info = await self._with_timeout(self._js.consumer_info(stream, durable),
                                            f"consumer_info stream={stream} durable={durable}")
            c = info.config

            deliver_subject = getattr(c, "deliver_subject", None)
            if not deliver_subject:
                raise RuntimeError(f"Existing consumer '{durable}' is PULL; cannot bind as PUSH.")

            actual_q = getattr(c, "deliver_group", None) or None
            if actual_q != queue:
                await self._with_timeout(self._js.delete_consumer(stream, durable),
                                         f"delete_consumer stream={stream} durable={durable}")
                raise js_err.NotFoundError()

            existing_filter = getattr(c, "filter_subject", None)
            if existing_filter and existing_filter != subject:
                await self._with_timeout(self._js.delete_consumer(stream, durable),
                                         f"delete_consumer stream={stream} durable={durable}")
                raise js_err.NotFoundError()

            existing_dp = getattr(c, "deliver_policy", None)
            if (existing_dp is not None) and (existing_dp != dp):
                await self._with_timeout(self._js.delete_consumer(stream, durable),
                                         f"delete_consumer stream={stream} durable={durable}")
                raise js_err.NotFoundError()

            existing_ack_wait = getattr(c, "ack_wait", None)
            if (existing_ack_wait is not None) and (int(existing_ack_wait) != ack_wait):
                await self._with_timeout(self._js.delete_consumer(stream, durable),
                                         f"delete_consumer stream={stream} durable={durable}")
                raise js_err.NotFoundError()

            existing_max_ack = getattr(c, "max_ack_pending", None)
            if (existing_max_ack is not None) and (int(existing_max_ack) != max_ack_pending):
                await self._with_timeout(self._js.delete_consumer(stream, durable),
                                         f"delete_consumer stream={stream} durable={durable}")
                raise js_err.NotFoundError()

            log.info("js_consumer_bound", extra={"stream": stream, "durable": durable, "inbox": deliver_subject})
            return deliver_subject

        except js_err.NotFoundError:
            deliver_subject = self._nc.new_inbox()
            await self._with_timeout(
                self._js.add_consumer(
                    stream,
                    ConsumerConfig(
                        durable_name=durable,
                        filter_subject=subject,
                        ack_policy=AckPolicy.EXPLICIT,
                        deliver_subject=deliver_subject,
                        deliver_group=queue,
                        deliver_policy=dp,
                        ack_wait=ack_wait,
                        max_ack_pending=max_ack_pending,
                    ),
                ),
                f"add_consumer stream={stream} durable={durable}",
            )
            log.info("js_consumer_created", extra={
                "stream": stream, "durable": durable, "inbox": deliver_subject, "queue": queue
            })
            return deliver_subject

    async def _ensure_pull_consumer(self, stream: str, subject: str, durable: str) -> None:
        """
        Ensure a PULL consumer exists and matches our desired config.
        If an existing consumer is incompatible (push mode, wrong filter/deliver policy/ack settings),
        delete it and recreate with the desired pull configuration.
        """
        desired_dp = DeliverPolicy.NEW  # we only want NEW for per-user drains
        desired_ack_wait = int(self.cfg.ack_wait_s)
        desired_max_ack = int(self.cfg.max_ack_pending)

        try:
            info = await self._with_timeout(
                self._js.consumer_info(stream, durable),
                f"consumer_info stream={stream} durable={durable}",
            )
            c = info.config

            # Determine current properties regardless of type (pydantic vs dict-like)
            deliver_subject = getattr(c, "deliver_subject", None)
            filter_subject = getattr(c, "filter_subject", None)
            ack_policy = getattr(c, "ack_policy", None)
            deliver_policy = getattr(c, "deliver_policy", None)
            ack_wait = getattr(c, "ack_wait", None)
            max_ack_pending = getattr(c, "max_ack_pending", None)

            # Normalize values
            def _to_seconds(raw) -> int:
                # nats-py may return ns as int; accept ints (ns) or strings with ns/us/ms/s/m suffix
                if raw is None:
                    return desired_ack_wait
                if isinstance(raw, int):
                    # Assume ns
                    return int(raw / 1_000_000_000)
                txt = str(raw).lower()
                if txt.endswith("ns"):
                    return int(float(txt[:-2]) / 1_000_000_000)
                if txt.endswith("us"):
                    return int(float(txt[:-2]) / 1_000_000)
                if txt.endswith("ms"):
                    return int(float(txt[:-2]) / 1_000)
                if txt.endswith("s"):
                    return int(float(txt[:-1]))
                if txt.endswith("m"):
                    return int(float(txt[:-1]) * 60)
                return int(desired_ack_wait)

            ack_wait_s = _to_seconds(ack_wait)
            max_ack_pending = int(max_ack_pending or 0)

            # Incompatible if:
            recreate = False
            reason = None
            if deliver_subject:
                recreate, reason = True, "PUSH (has deliver_subject)"
            elif filter_subject and filter_subject != subject:
                recreate, reason = True, f"filter_subject mismatch ({filter_subject} != {subject})"
            elif ack_policy not in (AckPolicy.EXPLICIT, "explicit", None):
                recreate, reason = True, "non-explicit ack policy"
            elif deliver_policy not in (DeliverPolicy.NEW, "new", None):
                recreate, reason = True, "non-NEW deliver policy"
            elif ack_wait_s != desired_ack_wait:
                recreate, reason = True, f"ack_wait mismatch ({ack_wait_s}s != {desired_ack_wait}s)"
            elif max_ack_pending != desired_max_ack:
                recreate, reason = True, f"max_ack_pending mismatch ({max_ack_pending} != {desired_max_ack})"

            if not recreate:
                return

            log.info(
                "pull_consumer_recreate",
                extra={"stream": stream, "durable": durable, "reason": reason},
            )
            await self._with_timeout(
                self._js.delete_consumer(stream, durable),
                f"delete_consumer stream={stream} durable={durable}",
            )
            # fall through to creation
        except js_err.NotFoundError:
            pass

        # Create desired PULL durable
        await self._with_timeout(
            self._js.add_consumer(
                stream,
                ConsumerConfig(
                    durable_name=durable,
                    filter_subject=subject,
                    # Explicit pull durable with sane defaults:
                    deliver_policy=desired_dp,
                    ack_policy=AckPolicy.EXPLICIT,
                    ack_wait=self.cfg.ack_wait_s,
                    max_ack_pending=self.cfg.max_ack_pending,
                ),
            ),
            f"add_consumer (pull) stream={stream} durable={durable}",
        )
        log.info(
            "pull_consumer_created",
            extra={"stream": stream, "durable": durable, "subject": subject},
        )

    async def connect(self) -> None:
        raw = _split_servers(self.cfg.server)
        urls = _normalize_servers(raw)
        servers_arg = urls[0] if len(urls) == 1 else urls

        self._nc = NATS()
        await self._nc.connect(
            servers=servers_arg,
            user=self.cfg.username,
            password=self.cfg.password,
            name=self.cfg.name,
            reconnect_time_wait=self.cfg.reconnect_time_wait,
            max_reconnect_attempts=self.cfg.max_reconnect_attempts,
        )
        self._js = self._nc.jetstream()

        # Log current stream state
        if self.cfg.stream_name:
            try:
                info = await self._with_timeout(
                    self._js.stream_info(self.cfg.stream_name),
                    f"stream_info name={self.cfg.stream_name}",
                )
                subs = ",".join(list(getattr(info.config, "subjects", []) or []))
                log.info("nats_js_stream_info", extra={"stream": self.cfg.stream_name, "exists": True, "subjects": subs})
            except js_err.NotFoundError:
                log.info("nats_js_stream_info", extra={"stream": self.cfg.stream_name, "exists": False, "subjects": ""})

        # Create stream if asked
        if self.cfg.stream_create and self.cfg.stream_name and self.cfg.stream_subjects:
            try:
                await self._with_timeout(
                    self._js.add_stream(StreamConfig(name=self.cfg.stream_name,
                                                     subjects=list(self.cfg.stream_subjects))),
                    f"add_stream name={self.cfg.stream_name}",
                )
                log.info("nats_stream_created", extra={
                    "stream": self.cfg.stream_name,
                    "subjects": ",".join(sorted(set(self.cfg.stream_subjects))),
                })
            except js_err.APIError:
                pass

        # Optionally update subjects (union) to include any missing ones
        if self.cfg.stream_name and self.cfg.stream_subjects and getattr(self.cfg, "stream_update_subjects", False):
            try:
                info = await self._with_timeout(
                    self._js.stream_info(self.cfg.stream_name),
                    f"stream_info name={self.cfg.stream_name}",
                )
                current = set(getattr(info.config, "subjects", []) or [])
                desired = set(self.cfg.stream_subjects)
                if not desired.issubset(current):
                    merged = sorted(current | desired)
                    await self._with_timeout(
                        self._js.update_stream(StreamConfig(name=self.cfg.stream_name, subjects=merged)),
                        f"update_stream name={self.cfg.stream_name}",
                    )
                    log.info("nats_stream_subjects_updated", extra={
                        "stream": self.cfg.stream_name,
                        "subjects": ",".join(merged),
                    })
                else:
                    log.info("nats_stream_ok", extra={
                        "stream": self.cfg.stream_name,
                        "subjects": ",".join(sorted(current)),
                    })
            except js_err.NotFoundError:
                await self._with_timeout(
                    self._js.add_stream(StreamConfig(name=self.cfg.stream_name,
                                                     subjects=list(self.cfg.stream_subjects))),
                    f"add_stream name={self.cfg.stream_name}",
                )
                log.info("nats_stream_created", extra={
                    "stream": self.cfg.stream_name,
                    "subjects": ",".join(sorted(set(self.cfg.stream_subjects))),
                })

    async def close(self) -> None:
        if self._nc:
            try:
                await self._nc.drain()
            finally:
                await self._nc.close()
        self._nc = None
        self._js = None
        self._subs.clear()
        self._push_keys.clear()
        self._dedupe_recent.clear()
        self._dedupe_lock = None

    async def publish(self, msg: BusMessage) -> None:
        if not self._js:
            raise RuntimeError("JetStream not initialized; call connect() first")
        if await self._should_drop_duplicate(msg):
            return
        await self._js.publish(msg.subject, msg.data, headers=msg.headers)

    async def _should_drop_duplicate(self, msg: BusMessage) -> bool:
        """Return True when publish should be suppressed due to recent duplicate."""
        window_ms = getattr(self.cfg, "dedupe_window_ms", None)
        if not window_ms or window_ms <= 0:
            return False

        correlation_id = msg.correlation_id
        if not correlation_id:
            return False

        window_s = window_ms / 1000.0
        now = time.monotonic()
        cutoff = now - window_s

        if self._dedupe_lock is None:
            self._dedupe_lock = asyncio.Lock()

        async with self._dedupe_lock:
            if self._dedupe_recent:
                stale = [cid for cid, ts in self._dedupe_recent.items() if ts < cutoff]
                for cid in stale:
                    self._dedupe_recent.pop(cid, None)

            last_seen = self._dedupe_recent.get(correlation_id)
            if last_seen and last_seen >= cutoff:
                log.warning(
                    "dedupe_drop",
                    extra={
                        "correlation_id": correlation_id,
                        "subject": msg.subject,
                        "window_ms": window_ms,
                        "message_type": msg.message_type,
                        "sender": msg.sender,
                    },
                )
                return True

            self._dedupe_recent[correlation_id] = now
            return False

    async def publish_json(
        self,
        subject: str,
        obj,
        *,
        sender: Optional[str] = None,
        correlation_id: Optional[str] = None,
        headers: Optional[dict[str, str]] = None,
        reply_on: Optional[str] = None,
        final_to: Optional[str] = None,
        compress: bool = False,
        message_type: Optional[str] = None,
    ) -> None:
        msg = BusMessage.from_json(
            subject,
            obj,
            sender=sender,
            correlation_id=correlation_id,
            headers=headers,
            compress=compress,
            reply_on=reply_on,
            final_to=final_to,
            message_type=message_type,
        )
        await self.publish(msg)

    async def publish_bytes(
        self,
        subject: str,
        data: bytes,
        *,
        sender: Optional[str] = None,
        correlation_id: Optional[str] = None,
        headers: Optional[dict[str, str]] = None,
        content_type: str = "application/octet-stream",
        reply_on: Optional[str] = None,
        final_to: Optional[str] = None,
        compress: bool = False,
        message_type: Optional[str] = None,
    ) -> None:
        msg = BusMessage.from_bytes(
            subject,
            data,
            sender=sender,
            correlation_id=correlation_id,
            headers=headers,
            content_type=content_type,
            compress=compress,
            reply_on=reply_on,
            final_to=final_to,
            message_type=message_type,
        )
        await self.publish(msg)

    async def push_subscribe(
        self,
        subject: str,
        handler: Handler,
        *,
        durable: Optional[str] = None,
        queue: Optional[str] = None,
        manual_ack: Optional[bool] = None,
        consumer_cfg: Optional[dict] = None,
    ) -> None:
        if not self._js:
            raise RuntimeError("JetStream not initialized; call connect() first")

        if manual_ack is None:
            manual_ack = self.cfg.manual_ack
        if queue is None:
            queue = self.cfg.queue_group
        queue = _norm_queue(queue)

        if not self.cfg.stream_name or not durable:
            raise ValueError("stream_name and durable are required for PUSH consumers")

        deliver_subject = await self._ensure_push_consumer(
            self.cfg.stream_name, subject, durable, queue, consumer_cfg=consumer_cfg
        )

        key = (deliver_subject, queue, handler)
        if key in self._push_keys:
            return

        async def _cb(nats_msg):
            async def _ack():
                reply = getattr(nats_msg, "reply", None)
                if reply:
                    await self._nc.publish(reply, b"+ACK")
                elif hasattr(nats_msg, "ack"):
                    await nats_msg.ack()

            async def _nak():
                reply = getattr(nats_msg, "reply", None)
                if reply:
                    await self._nc.publish(reply, b"-NAK")
                elif hasattr(nats_msg, "nak"):
                    await nats_msg.nak()

            async def _term():
                reply = getattr(nats_msg, "reply", None)
                if reply:
                    await self._nc.publish(reply, b"+TERM")
                elif hasattr(nats_msg, "term"):
                    await nats_msg.term()

            rm = ReceivedMessage(
                subject=subject,
                data=nats_msg.data,
                headers=dict(nats_msg.headers or {}),
                _ack=_ack,
                _nak=_nak,
                _term=_term,
            )

            try:
                await handler(rm)
            except Exception:
                import logging
                logging.getLogger("natbus.client").exception(
                    "sub_handler_error",
                    extra={"subject": subject, "durable": durable, "queue": queue},
                )
                try:
                    await _nak()
                except Exception:
                    logging.getLogger("natbus.client").exception("nak_failed")

        if queue:
            sub = await self._nc.subscribe(deliver_subject, queue=queue, cb=_cb)
        else:
            sub = await self._nc.subscribe(deliver_subject, cb=_cb)

        log.info("nats_inbox_subscribed", extra={"inbox": deliver_subject, "queue": queue or ""})
        self._subs.append(sub)
        self._push_keys[key] = sub

    async def subscribe(
        self,
        subject: str,
        handler: Handler,
        *,
        durable: Optional[str] = None,
        queue: Optional[str] = None,
        manual_ack: Optional[bool] = None,
        bind: Optional[bool] = None,
    ) -> None:
        await self.push_subscribe(
            subject, handler, durable=durable, queue=queue, manual_ack=manual_ack
        )

    async def pull_subscribe(
        self,
        subject: str,
        *,
        durable: str,
        stream: Optional[str] = None,
    ) -> PullSubscription:
        if not self._js:
            raise RuntimeError("JetStream not initialized; call connect() first")

        stream_name = stream or self.cfg.stream_name or ""
        if not stream_name:
            raise ValueError("stream name required for pull_subscribe (set cfg.stream_name or pass stream=)")

        await self._ensure_pull_consumer(stream_name, subject, durable)

        try:
            sub = await self._js.pull_subscribe(
                subject,
                durable=durable,
                stream=stream_name,
            )
        except js_err.Error as e:
            raise RuntimeError(
                f"JetStream pull_subscribe failed: stream={stream_name} subject={subject} durable={durable} err={e}"
            )
        return PullSubscription(sub)

    async def ephemeral_push_subscribe(
        self,
        subject: str,
        handler: Handler,
        *,
        inactive_seconds: int = 120,
        queue: Optional[str] = None,
    ) -> EphemeralPushHandle:
        if not self._js:
            raise RuntimeError("JetStream not initialized; call connect() first")
        if not self.cfg.stream_name:
            raise ValueError("cfg.stream_name required for ephemeral_push_subscribe")

        deliver_subject = self._nc.new_inbox()

        await self._with_timeout(
            self._js.add_consumer(
                self.cfg.stream_name,
                ConsumerConfig(
                    filter_subject=subject,
                    ack_policy=AckPolicy.EXPLICIT,
                    deliver_subject=deliver_subject,
                    deliver_group=queue,
                    inactive_threshold=inactive_seconds,
                    deliver_policy=_resolve_deliver_policy(self.cfg.deliver_policy),
                    ack_wait=self.cfg.ack_wait_s,
                    max_ack_pending=self.cfg.max_ack_pending,
                ),
            ),
            f"add_consumer (ephemeral) stream={self.cfg.stream_name}",
        )

        async def _cb(nats_msg):
            async def _ack():
                reply = getattr(nats_msg, "reply", None)
                if reply:
                    await self._nc.publish(reply, b"+ACK")
                elif hasattr(nats_msg, "ack"):
                    await nats_msg.ack()

            async def _nak():
                reply = getattr(nats_msg, "reply", None)
                if reply:
                    await self._nc.publish(reply, b"-NAK")
                elif hasattr(nats_msg, "nak"):
                    await nats_msg.nak()

            async def _term():
                reply = getattr(nats_msg, "reply", None)
                if reply:
                    await self._nc.publish(reply, b"+TERM")
                elif hasattr(nats_msg, "term"):
                    await nats_msg.term()

            rm = ReceivedMessage(
                subject=subject,
                data=nats_msg.data,
                headers=dict(nats_msg.headers or {}),
                _ack=_ack,
                _nak=_nak,
                _term=_term,
            )
            await handler(rm)

        sub = await self._nc.subscribe(deliver_subject, queue=queue, cb=_cb) if queue \
              else await self._nc.subscribe(deliver_subject, cb=_cb)
        log.info("nats_inbox_subscribed", extra={"inbox": deliver_subject, "queue": queue or ""})
        return EphemeralPushHandle(sub)

    # ---------- Reply helpers (use reply_on/final_to headers) ----------------
    async def reply_json(
        self,
        to_msg: ReceivedMessage,
        obj,
        *,
        subject: Optional[str] = None,
        final: bool = False,
        sender: Optional[str] = None,
        headers: Optional[dict[str, str]] = None,
        compress: bool = False,
        message_type: Optional[str] = None,
    ) -> None:
        target = subject or (to_msg.final_to if final else to_msg.reply_on)
        if not target:
            raise ValueError("No reply subject resolved (pass subject= or set x-reply-on/x-final-to).")
        h = dict(headers or {})
        if H_MESSAGE_TYPE not in h or not h[H_MESSAGE_TYPE]:
            h[H_MESSAGE_TYPE] = message_type or to_msg.message_type
        if not h.get(H_MESSAGE_TYPE):
            raise ValueError("x-message-type required for replies.")
        msg = BusMessage.from_json(
            target,
            obj,
            sender=sender,
            correlation_id=to_msg.correlation_id,
            headers=h,
            compress=compress,
            message_type=h[H_MESSAGE_TYPE],
        )
        await self.publish(msg)

    async def reply_text(
        self,
        to_msg: ReceivedMessage,
        text: str,
        *,
        subject: Optional[str] = None,
        final: bool = False,
        sender: Optional[str] = None,
        headers: Optional[dict[str, str]] = None,
        encoding: str = "utf-8",
        compress: bool = False,
        message_type: Optional[str] = None,
    ) -> None:
        target = subject or (to_msg.final_to if final else to_msg.reply_on)
        if not target:
            raise ValueError("No reply subject resolved (pass subject= or set x-reply-on/x-final-to).")
        h = dict(headers or {})
        if H_MESSAGE_TYPE not in h or not h[H_MESSAGE_TYPE]:
            h[H_MESSAGE_TYPE] = message_type or to_msg.message_type
        if not h.get(H_MESSAGE_TYPE):
            raise ValueError("x-message-type required for replies.")
        msg = BusMessage.from_text(
            target,
            text,
            sender=sender,
            correlation_id=to_msg.correlation_id,
            headers=h,
            encoding=encoding,
            compress=compress,
            message_type=h[H_MESSAGE_TYPE],
        )
        await self.publish(msg)

    async def reply_bytes(
        self,
        to_msg: ReceivedMessage,
        data: bytes,
        *,
        subject: Optional[str] = None,
        final: bool = False,
        sender: Optional[str] = None,
        headers: Optional[dict[str, str]] = None,
        content_type: str = "application/octet-stream",
        compress: bool = False,
        message_type: Optional[str] = None,
    ) -> None:
        target = subject or (to_msg.final_to if final else to_msg.reply_on)
        if not target:
            raise ValueError("No reply subject resolved (pass subject= or set x-reply-on/x-final-to).")
        h = dict(headers or {})
        if H_MESSAGE_TYPE not in h or not h[H_MESSAGE_TYPE]:
            h[H_MESSAGE_TYPE] = message_type or to_msg.message_type
        if not h.get(H_MESSAGE_TYPE):
            raise ValueError("x-message-type required for replies.")
        msg = BusMessage.from_bytes(
            target,
            data,
            sender=sender,
            correlation_id=to_msg.correlation_id,
            headers=h,
            content_type=content_type,
            compress=compress,
            message_type=h[H_MESSAGE_TYPE],
        )
        await self.publish(msg)
