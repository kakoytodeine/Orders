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
    
    BASE_DIR = Path(__file__).resolve().parent.parent  # ты сейчас в app/, поднимаемся к корню проекта
    db_path = BASE_DIR / "data" / "product.db"
    
    return Config(
        db=DataBaseConfig(database_url=f"sqlite:///{db_path}"),
        tg_token=env('TG_TOKEN', default='your_bot_token_here'),
        debug=env('DEBUG', default=False)
    )

_config = load_config()