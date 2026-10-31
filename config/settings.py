from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    app_name: str = "frame² – red sox intelligence"
    cache_dir: str = "cache"
    data_dir: str = "data"
    timezone: str = "America/New_York"
    lowercase_posts: bool = True
    request_timeout_s: float = 10.0

SETTINGS = Settings()
