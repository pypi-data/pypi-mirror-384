from typing import Any, Dict, List, Type

from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, Session

__all__ = (
    "upsert_data",
    "upsert_data_async",
)


def _prepare_upsert(
    list_of_data: List[Dict[str, Any]],
    model: Type[DeclarativeBase],
):
    """Middle function that prepares the INSERT ... ON CONFLICT DO UPDATE
    statement for PostgreSQL if possible.

    :param list_of_data: A list of dictionaries with data to be inserted/updated.
    :param model: The SQLAlchemy model class (mapped).
    :return: Tuple (do_upsert, statement_or_None)
       - do_upsert (bool) indicates if there's a valid statement to execute.
       - statement_or_None is the compiled statement or None if no valid upsert is needed.
    """

    # If there's no data, we can't do anything.
    if not list_of_data:
        return False, None

    # Build the base INSERT statement from the data
    stmt = insert(model.__table__).values(list_of_data)

    # We only want to update columns that exist in the data and are not primary keys
    data_keys = list_of_data[0].keys()
    update_dict = {
        col.name: col
        for col in stmt.excluded
        if not col.primary_key and col.name in data_keys
    }

    # If there's nothing to update, we can't do an upsert
    if not update_dict:
        return False, None

    # Get the primary keys to use in the ON CONFLICT clause
    primary_keys = [key.name for key in inspect(model.__table__).primary_key]

    # Build the ON CONFLICT DO UPDATE statement
    stmt = stmt.on_conflict_do_update(index_elements=primary_keys, set_=update_dict)

    return True, stmt


def upsert_data(
    list_of_data: List[Dict[str, Any]],
    model: Type[DeclarativeBase],
    db: Session,
    only_update=False,
    only_insert=False,
) -> bool:
    if not list_of_data:
        return False

    try:
        if only_update:
            db.bulk_update_mappings(model, list_of_data)
            db.commit()
            return True

        elif only_insert:
            db.bulk_insert_mappings(model, list_of_data)
            db.commit()
            return True

        do_upsert, stmt = _prepare_upsert(list_of_data, model)
        if not do_upsert:
            return False

        db.execute(stmt)
        db.commit()
        return True

    except (SQLAlchemyError, IntegrityError):
        db.rollback()
        raise


async def upsert_data_async(
    list_of_data: List[Dict[str, Any]],
    model: Type[DeclarativeBase],
    db: AsyncSession,
    only_update: bool = False,
    only_insert: bool = False,
) -> bool:
    if not list_of_data:
        return False

    if only_update:
        await db.run_sync(lambda s: s.bulk_update_mappings(model, list_of_data))
        await db.commit()
        return True

    elif only_insert:
        await db.run_sync(lambda s: s.bulk_insert_mappings(model, list_of_data))
        await db.commit()
        return True

    do_upsert, stmt = _prepare_upsert(list_of_data, model)
    if not do_upsert:
        return False

    await db.execute(stmt)
    await db.commit()
    return True
