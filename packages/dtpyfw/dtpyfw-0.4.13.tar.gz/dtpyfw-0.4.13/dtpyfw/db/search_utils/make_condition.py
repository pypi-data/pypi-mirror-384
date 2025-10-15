from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import Text, and_, cast, func, literal, or_

__all__ = ("make_condition",)


def select_condition_maker(filter_item: dict, values: list, array_mode: bool):
    columns = filter_item.get("columns", [])
    columns_logic = filter_item.get("columns_logic", "or")
    case_insensitive = filter_item.get("case_insensitive", False)
    use_similarity = filter_item.get("use_similarity", False)
    similarity_threshold = filter_item.get("similarity_threshold", 0.3)
    logic_fn = {"or": or_, "and_": and_}[columns_logic]

    # 1) Unwrap enums / custom types into primitives
    def unwrap(v_):
        if isinstance(v_, Enum):
            return v_.value
        return v_

    # 2) Pre-process values: unwrap + optional lower()
    processed_values = []
    for v in values:
        uv = unwrap(v)
        if case_insensitive and isinstance(uv, str):
            uv = uv.lower()
        processed_values.append(uv)

    conditions = []

    if use_similarity:
        for col in columns:
            for v in processed_values:
                if isinstance(v, str):
                    lit_q = literal(v).cast(Text)
                    col_txt = cast(col, Text)
                    conditions.append(
                        func.similarity(col_txt, lit_q) >= similarity_threshold
                    )
                else:
                    # now v is a primitive (int, float, etc.)
                    conditions.append(col == v)
    else:
        for col in columns:
            # detect string columns via their python_type
            is_str_col = getattr(getattr(col, "type", None), "python_type", None) is str
            if case_insensitive and is_str_col:
                if array_mode:
                    lower_col_array = func.array(select(func.lower(func.unnest(col))).scalar_subquery())
                    lower_vals_array = array([v.lower() for v in processed_values], type_=ARRAY(Text()))
                    conditions.append(lower_col_array.op('&&')(lower_vals_array))
                else:
                    conditions.append(func.lower(col).in_(processed_values))
            else:
                if array_mode:
                    conditions.append(col.op("&&")(literal(processed_values)))
                else:
                    conditions.append(col.in_(processed_values))

    # if no conditions, return a no-op true clause
    if not conditions:
        return True  # or `text('TRUE')` in SQLAlchemy

    return logic_fn(*conditions)


def number_condition_maker(filter_item: dict, values: dict):
    columns = filter_item.get("columns")
    columns_logic = filter_item.get("columns_logic", "or")
    logic_function = {
        "or": or_,
        "and": and_,
    }.get(columns_logic)

    value_min = values.get("min")
    value_max = values.get("max")
    if value_min is not None and value_max is not None:
        return logic_function(
            *[getattr(column, "between")(value_min, value_max) for column in columns]
        )
    elif value_min is None and value_max is not None:
        return logic_function(*[column <= value_max for column in columns])
    elif value_min is not None and value_max is None:
        return logic_function(*[column >= value_min for column in columns])


def date_condition_maker(filter_item: dict, values: dict):
    value_min: datetime = values.get("min")
    value_max: datetime = values.get("max")

    columns = filter_item.get("columns")
    columns_logic = filter_item.get("columns_logic", "or")
    logic_function = {
        "or": or_,
        "and": and_,
    }.get(columns_logic)

    if value_min is not None and value_max is not None:
        return logic_function(
            *[getattr(column, "between")(value_min, value_max) for column in columns]
        )
    elif value_min is None and value_max is not None:
        return logic_function(
            *[or_(column <= value_max, column == None) for column in columns]
        )
    elif value_min is not None and value_max is None:
        return logic_function(*[column >= value_min for column in columns])


def make_condition(filter_item: dict, values: Any):
    columns_type = filter_item.get("type", "select")

    if columns_type in {"select", "select_array"}:
        return select_condition_maker(
            filter_item=filter_item,
            values=values,
            array_mode=columns_type == "select_array",
        )
    elif columns_type == "number":
        return number_condition_maker(
            filter_item=filter_item,
            values=values,
        )
    elif columns_type == "date":
        return date_condition_maker(
            filter_item=filter_item,
            values=values,
        )
    else:
        return None
