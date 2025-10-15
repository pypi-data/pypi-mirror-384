from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional, Dict
from uuid import uuid4
from datetime import datetime, timezone
import json
import gzip

"""
# JSON payload with compression
await bus.publish_json("ai.json.requests", {"a": "b", "n": 123}, sender="json-svc", compress=True, message_type="chat")

# Raw bytes with compression
await bus.publish_bytes("blob.store", b"\x00" * 200_000, sender="blob-svc", compress=True, message_type="blob")

# Text convenience (via from_text)
msg = BusMessage.from_text("logs.info", "hello", sender="log-svc", compress=True, message_type="log")
await bus.publish(msg)
"""

Headers = Dict[str, str]

# Canonical header keys (lowercase for consistency)
H_TRACE_ID         = "x-trace-id"          # unique per message
H_CORRELATION_ID   = "x-correlation-id"    # for request/reply or workflow tie-ups
H_SENDER           = "x-sender"            # service identifier
H_SENT_AT          = "x-sent-at"           # ISO-8601 UTC timestamp
H_CONTENT_TYPE     = "content-type"        # MIME: application/json, text/plain; charset=utf-8, application/octet-stream
H_CONTENT_ENCODING = "content-encoding"    # compression indicator: e.g. "gzip"
H_MESSAGE_TYPE     = "x-message-type"      # mandatory: identifies message domain (e.g., chat, control, snipe)

# Reply routing
H_REPLY_ON         = "x-reply-on"          # ephemeral subject for progress/partial replies
H_FINAL_TO         = "x-final-to"          # terminal subject for the final reply


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _maybe_compress(b: bytes, *, compress: bool, headers: Headers) -> bytes:
    if not compress:
        return b
    headers[H_CONTENT_ENCODING] = "gzip"
    return gzip.compress(b)


def _ensure_msg_type(h: Headers, message_type: Optional[str]) -> None:
    if message_type:
        h[H_MESSAGE_TYPE] = message_type
    # mandatory – must be present and non-empty (preserve if caller already set it)
    mt = h.get(H_MESSAGE_TYPE, "")
    if not isinstance(mt, str) or not mt.strip():
        raise ValueError("Missing required header: x-message-type")


@dataclass(slots=True)
class BusMessage:
    """
    Outbound message: carries data + headers with trace metadata.
    All constructors set (or preserve) trace headers and require x-message-type.
    """
    subject: str
    data: bytes
    headers: Headers = field(default_factory=dict)

    # ----- constructors ------------------------------------------------------
    @classmethod
    def from_json(
        cls,
        subject: str,
        obj: Any,
        *,
        sender: Optional[str] = None,
        correlation_id: Optional[str] = None,
        headers: Optional[Headers] = None,
        ensure_trace: bool = True,
        compress: bool = False,
        reply_on: Optional[str] = None,
        final_to: Optional[str] = None,
        message_type: Optional[str] = None,
    ) -> "BusMessage":
        h: Headers = {H_CONTENT_TYPE: "application/json"}
        if headers:
            h.update(headers)
        if reply_on:
            h[H_REPLY_ON] = reply_on
        if final_to:
            h[H_FINAL_TO] = final_to
        _ensure_msg_type(h, message_type)
        raw = json.dumps(obj).encode("utf-8")
        data = _maybe_compress(raw, compress=compress, headers=h)
        msg = cls(subject=subject, data=data, headers=h)
        if ensure_trace:
            msg._ensure_trace(sender=sender, correlation_id=correlation_id)
        return msg

    @classmethod
    def from_text(
        cls,
        subject: str,
        text: str,
        *,
        sender: Optional[str] = None,
        correlation_id: Optional[str] = None,
        headers: Optional[Headers] = None,
        encoding: str = "utf-8",
        ensure_trace: bool = True,
        compress: bool = False,
        reply_on: Optional[str] = None,
        final_to: Optional[str] = None,
        message_type: Optional[str] = None,
    ) -> "BusMessage":
        h: Headers = {H_CONTENT_TYPE: f"text/plain; charset={encoding}"}
        if headers:
            h.update(headers)
        if reply_on:
            h[H_REPLY_ON] = reply_on
        if final_to:
            h[H_FINAL_TO] = final_to
        _ensure_msg_type(h, message_type)
        raw = text.encode(encoding)
        data = _maybe_compress(raw, compress=compress, headers=h)
        msg = cls(subject=subject, data=data, headers=h)
        if ensure_trace:
            msg._ensure_trace(sender=sender, correlation_id=correlation_id)
        return msg

    @classmethod
    def from_bytes(
        cls,
        subject: str,
        b: bytes,
        *,
        sender: Optional[str] = None,
        correlation_id: Optional[str] = None,
        headers: Optional[Headers] = None,
        content_type: str = "application/octet-stream",
        ensure_trace: bool = True,
        compress: bool = False,
        reply_on: Optional[str] = None,
        final_to: Optional[str] = None,
        message_type: Optional[str] = None,
    ) -> "BusMessage":
        h: Headers = {H_CONTENT_TYPE: content_type}
        if headers:
            h.update(headers)
        if reply_on:
            h[H_REPLY_ON] = reply_on
        if final_to:
            h[H_FINAL_TO] = final_to
        _ensure_msg_type(h, message_type)
        data = _maybe_compress(b, compress=compress, headers=h)
        msg = cls(subject=subject, data=data, headers=h)
        if ensure_trace:
            msg._ensure_trace(sender=sender, correlation_id=correlation_id)
        return msg

    # ----- helpers -----------------------------------------------------------
    @property
    def content_type(self) -> str:
        return self.headers.get(H_CONTENT_TYPE, "")

    @property
    def trace_id(self) -> str:
        return self.headers.get(H_TRACE_ID, "")

    @property
    def correlation_id(self) -> str:
        return self.headers.get(H_CORRELATION_ID, "")

    @property
    def sender(self) -> str:
        return self.headers.get(H_SENDER, "")

    @property
    def sent_at(self) -> str:
        return self.headers.get(H_SENT_AT, "")

    @property
    def reply_on(self) -> str:
        return self.headers.get(H_REPLY_ON, "")

    @property
    def final_to(self) -> str:
        return self.headers.get(H_FINAL_TO, "")

    @property
    def message_type(self) -> str:
        return self.headers.get(H_MESSAGE_TYPE, "")

    def _ensure_trace(self, *, sender: Optional[str], correlation_id: Optional[str]) -> None:
        self.headers.setdefault(H_TRACE_ID, str(uuid4()))
        self.headers.setdefault(H_CORRELATION_ID, correlation_id or str(uuid4()))
        if sender:
            self.headers.setdefault(H_SENDER, sender)
        self.headers.setdefault(H_SENT_AT, _utc_now_iso())

    # decode convenience
    def as_json(self) -> Any:
        return json.loads(self.data.decode("utf-8"))

    def as_text(self, encoding: str = "utf-8") -> str:
        return self.data.decode(encoding)


@dataclass(slots=True)
class ReceivedMessage:
    """
    Inbound message wrapper with parsed trace metadata and ack helpers.
    If headers['content-encoding'] == 'gzip', payload is transparently decompressed.
    """
    subject: str
    data: bytes
    headers: Headers
    _ack: callable
    _nak: callable
    _term: callable
    received_at: str = field(default_factory=_utc_now_iso)

    def __post_init__(self) -> None:
        enc = (self.headers.get(H_CONTENT_ENCODING, "") or "").lower()
        if enc == "gzip":
            self.data = gzip.decompress(self.data)

    # trace accessors
    @property
    def content_type(self) -> str:
        return self.headers.get(H_CONTENT_TYPE, "")

    @property
    def trace_id(self) -> str:
        return self.headers.get(H_TRACE_ID, "")

    @property
    def correlation_id(self) -> str:
        return self.headers.get(H_CORRELATION_ID, "")

    @property
    def sender(self) -> str:
        return self.headers.get(H_SENDER, "")

    @property
    def sent_at(self) -> str:
        return self.headers.get(H_SENT_AT, "")

    @property
    def reply_on(self) -> str:
        return self.headers.get(H_REPLY_ON, "")

    @property
    def final_to(self) -> str:
        return self.headers.get(H_FINAL_TO, "")

    @property
    def message_type(self) -> str:
        return self.headers.get(H_MESSAGE_TYPE, "")

    # ack API
    async def ack(self) -> None:
        await self._ack()

    async def nak(self) -> None:
        await self._nak()

    async def term(self) -> None:
        await self._term()

    # decode convenience
    def as_json(self) -> Any:
        return json.loads(self.data.decode("utf-8"))

    def as_text(self, encoding: str = "utf-8") -> str:
        return self.data.decode(encoding)
