# NATBus #

• Auth: library uses explicit user=/password= with a host:port server so credentials are always sent.

• Streams: set stream_create=True to auto-create one stream (optional).

• Payloads: BusMessage.from_json sets content-type=application/json; binary pass-through uses from_bytes.

• Handlers: receive ReceivedMessage with ack()/nak()/term() for JetStream flow control.

• Durable consumers: pass durable="name"; bind=True lets pods restart without “already bound” errors.


# Add to Project
Add to the service’s requirements.txt
```text
pip install --find-links=/mnt/nas_share/python_package_repository/natbus natbus==<version>
```
# Usage
```python
import asyncio
from natbus import NatsConfig, NatsBus, BusMessage, ReceivedMessage

CFG = NatsConfig(
    server="nats-nats-jetstream:4222",
    username="nats-user",
    password="changeme",
    name="orders-svc",
    stream_create=True,
    stream_name="TEST_STREAM",
    stream_subjects=("test.stream",),

    # Optional defaults for PUSH; can be overridden per call
    queue_group=None,   # e.g. "orders-workers" to load-balance PUSH subscribers
    manual_ack=True,
)

# ---------- handlers ----------
async def handle_push(msg: ReceivedMessage):
    print("PUSH RX:", msg.subject, {
        "trace_id": msg.trace_id,
        "correlation_id": msg.correlation_id,
        "sender": msg.sender,
        "content_type": msg.content_type,
    })
    try:
        print("PUSH as_text:", msg.as_text())
    except Exception:
        pass
    await msg.ack()

async def handle_pull(msg: ReceivedMessage):
    print("PULL RX:", msg.subject, {
        "trace_id": msg.trace_id,
        "correlation_id": msg.correlation_id,
        "sender": msg.sender,
        "content_type": msg.content_type,
    })
    try:
        print("PULL as_text:", msg.as_text())
    except Exception:
        pass
    await msg.ack()

# ---------- app ----------
async def main():
    bus = NatsBus(CFG)
    await bus.connect()

    # --- PUSH consumer (server pushes to our callback) ---
    # Use a queue group to load-balance across many pods:
    # queue="orders-workers"  # uncomment to enable worker-pool behavior
    await bus.push_subscribe(
        subject="test.stream",
        handler=handle_push,
        durable="orders_push",   # retains cursor/acks
        # queue="orders-workers",  # optional: load-balanced PUSH
        manual_ack=True,
    )
    print("PUSH consumer ready (durable=orders_push)")

    # --- PULL consumer (we fetch batches, good for explicit backpressure) ---
    # Creates/ensures a pull-based durable (no queue group concept for pull)
    await bus.pull_subscribe(
        stream="TEST_STREAM",
        subject="test.stream",
        durable="orders_pull",
        handler=handle_pull,
        batch=10,        # fetch up to 10 msgs per request
        expires=1.5,     # server waits up to 1.5s for batch to fill
        manual_ack=True,
    )
    print("PULL consumer ready (durable=orders_pull)")

    # --- publish some messages (both consumers will see them, since durables differ) ---
    msg_json = BusMessage.from_json(
        "test.stream",
        {"hello": "world"},
        sender="orders-svc",
    )
    await bus.publish(msg_json)

    msg_bin = BusMessage.from_bytes(
        "test.stream",
        b"\xff\xd8\xff...binary...",
        sender="orders-svc",
        headers={"content-type": "image/jpeg"},
    )
    await bus.publish(msg_bin)

    # Keep the service alive
    while True:
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())


```


## Build

Version is controlled in pyproject.toml (project.version). Bump it before each release.

```shell
python3.11 -m venv .venv && . .venv/bin/activate
python -m pip install --upgrade pip build
python -m build
# artifacts: dist/natsbus-0.1.0.tar.gz and dist/natsbus-0.1.0-py3-none-any.whl

```