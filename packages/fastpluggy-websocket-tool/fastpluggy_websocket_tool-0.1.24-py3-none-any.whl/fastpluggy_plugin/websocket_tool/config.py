
from fastpluggy.core.config import BaseDatabaseSettings


class WebSocketSettings(BaseDatabaseSettings):
    max_queue_size: int = 10000

    enable_heartbeat: bool = True
    heartbeat_interval: int = 30
    heartbeat_timeout: int = 60


    # todo add prefix for var like FP_WST_