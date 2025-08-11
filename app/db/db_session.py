from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import _config

# Создание движка SQLAlchemy с использованием URL из конфига
engine = create_engine(_config.db.database_url)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# Базовый класс для моделей
Base = declarative_base()
