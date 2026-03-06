from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    app_name: str = "frame² — red sox history v1"
    timezone: str = "America/New_York"
    lowercase_posts: bool = True
    cache_dir: str = "storage/cache"
    request_timeout_s: int = 12

SETTINGS = Settings()
