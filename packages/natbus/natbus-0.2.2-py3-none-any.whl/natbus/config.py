# natbus/config.py
from dataclasses import dataclass
from typing import Optional, Tuple

@dataclass(frozen=True)
class NatsConfig:
    server: str = "nats-nats-jetstream:4222"
    username: Optional[str] = None
    password: Optional[str] = None
    name: str = "natsbus-client"
    reconnect_time_wait: float = 1.0
    max_reconnect_attempts: int = 60

    # JetStream stream bootstrapping
    stream_create: bool = False
    stream_name: str = ""
    stream_subjects: Tuple[str, ...] = ()

    # auto-update subjects when stream exists
    stream_update_subjects: bool = False

    # PUSH consumer defaults
    queue_group: Optional[str] = None
    bind: bool = True
    manual_ack: bool = True

    # Consumer defaults
    deliver_policy: str = "new"
    ack_wait_s: int = 30
    max_ack_pending: int = 1024

    # Optional publish de-duplication window (milliseconds); disable when None/<=0
    dedupe_window_ms: Optional[int] = None

    # JS management request timeout (seconds)
    js_api_timeout_s: float = 5.0
