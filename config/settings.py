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

# Data marks every pennant season as "world series"; these are the ones the Red Sox won.
WS_TITLE_SEASONS = frozenset({2004, 2007, 2013, 2018})

# A season is over- or underperformed when its 162-game win pace is this many wins from expected.
LUCK_BAND = 4.0
