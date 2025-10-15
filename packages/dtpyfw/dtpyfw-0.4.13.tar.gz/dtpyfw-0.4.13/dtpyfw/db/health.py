from typing import Tuple

from sqlalchemy import text

from .database import DatabaseInstance

__all__ = ("is_database_connected",)


def is_database_connected(db: DatabaseInstance) -> Tuple[bool, Exception | None]:
    try:
        with db.engine_write.connect() as connection:
            connection.execute(text("SELECT 1"))

        with db.engine_read.connect() as connection:
            connection.execute(text("SELECT 1"))

        return True, None

    except Exception as e:
        return False, e
