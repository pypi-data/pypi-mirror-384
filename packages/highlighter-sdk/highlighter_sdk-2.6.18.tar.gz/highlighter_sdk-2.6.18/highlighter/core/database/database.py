from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

from highlighter.core.config import HighlighterRuntimeConfig

__all__ = [
    "Database",
]


class Database:
    def __init__(self):
        hl_cfg = HighlighterRuntimeConfig.load()
        self.highlighter_path_to_database_file = str(hl_cfg.agent.db_file())
        self._engine = create_engine(
            f"sqlite:///{self.highlighter_path_to_database_file}", connect_args={"check_same_thread": False}
        )
        SQLModel.metadata.create_all(self._engine)

    @property
    def engine(self) -> Engine:
        return self._engine

    def get_session(self):
        return Session(self.engine)

    def close(self):
        self._engine.dispose()  # Call this when shutting down your app
