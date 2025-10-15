
from typing import Optional


class KnowrithmConfig:
    def __init__(
        self,
        base_url: str,
        api_version: str = "v1",
        timeout: int = 30,
        max_retries: int = 3,
        retry_backoff_factor: float = 1.5,
        verify_ssl: bool = True,
        stream_path_template: Optional[str] = "/conversation/{conversation_id}/messages/stream",
        stream_base_url: Optional[str] = None,
        stream_timeout: Optional[float] = None,
    ):
        self.base_url = base_url
        self.api_version = api_version
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff_factor = retry_backoff_factor
        self.verify_ssl = verify_ssl
        self.stream_path_template = stream_path_template
        self.stream_base_url = stream_base_url
        self.stream_timeout = stream_timeout
