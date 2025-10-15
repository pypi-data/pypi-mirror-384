from contextlib import contextmanager
from dataclasses import dataclass
from typing import Generator, Optional

import sqlalchemy
from sqlalchemy.engine import Engine, URL
from sqlalchemy.orm import Session, sessionmaker

"""
This module defines the global database manager object used across the project.

Usage patterns:

1. FastAPI:
   - In the app lifespan, call `db.connect()` on startup and `db.dispose()` on shutdown.
   - This ensures the DB connection is ready for all API requests.

   Example:
   @asynccontextmanager
   async def lifespan(app: FastAPI):
       db.connect()
       yield
       db.dispose()

2. Celery workers:
   - Worker processes do NOT run FastAPI lifespan.
   - Use Celery signals to connect/dispose in each worker process.

   Example:
   from celery.signals import worker_process_init, worker_shutdown

   @worker_process_init.connect
   def init_db(**kwargs):
       db.connect()

   @worker_shutdown.connect
   def close_db(**kwargs):
       db.dispose()

3. All file uses:
   - Use `with db.session() as session:` to get a session with automatic commit/rollback.
"""
@dataclass
class DatabaseConfig:
    host: str
    database: str
    user: str
    password: str
    port: int

    def __post_init__(self) -> None:
        if not all([self.host, self.database, self.user, self.password, self.port]):
            raise ValueError("All database configuration fields must be provided")

    def to_url(self) -> URL:
        return URL.create(
            "postgresql+psycopg2",
            username=self.user,
            password=self.password,
            host=self.host,
            port=self.port,
            database=self.database,
        )


class DatabaseManager:
    """Reusable database manager that wraps SQLAlchemy engine + sessions."""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._engine: Optional[Engine] = None
        self._SessionLocal: Optional[sessionmaker] = None

    def connect(self) -> None:
        """Create SQLAlchemy engine + session factory."""
        self._engine = sqlalchemy.create_engine(
            self.config.to_url(),
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800,
            pool_pre_ping=True,
        )
        self._SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self._engine
        )

    def dispose(self) -> None:
        """Dispose engine (close all connections)."""
        if self._engine is not None:
            self._engine.dispose()

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """Context-managed session with commit/rollback handling."""
        if self._SessionLocal is None:
            raise RuntimeError("DatabaseManager.connect() must be called first")

        session = self._SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
