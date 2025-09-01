from dataclasses import dataclass
from pathlib import Path

from environs import Env


@dataclass
class DataBaseConfig:
    database_url: str


@dataclass
class Config:
    db: DataBaseConfig
    tg_token: str
    debug: bool


def load_config(path: str = None) -> Config:
    env = Env()
    env.read_env(path)

    db_url = env("DATABASE_URL")

    # Если SQLite и путь относительный — превращаем в абсолютный внутри проекта
    if db_url.startswith("sqlite:///"):
        db_path = db_url.replace("sqlite:///", "")
        db_path = Path(__file__).resolve().parent.parent / db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)  # создаём папку если её нет
        db_url = f"sqlite:///{db_path}"

    return Config(
        db=DataBaseConfig(database_url=db_url),
        tg_token=env("TG_TOKEN", default="your_bot_token_here"),
        debug=env.bool("DEBUG", default=False),
    )

_config = load_config()