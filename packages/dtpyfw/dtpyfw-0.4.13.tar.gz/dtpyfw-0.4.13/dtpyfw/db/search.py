from enum import Enum
from math import ceil
from typing import Any

from sqlalchemy import distinct as distinct_func
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .search_utils.filter_values import get_filters_value
from .search_utils.free_search import free_search
from .search_utils.make_condition import make_condition
from .search_utils.selected_filters import make_selected_filters

__all__ = ("get_list",)


def get_list(
    current_query: dict,
    db: Session,
    model: Any,
    joins: list[dict] = None,
    pre_conditions: list = None,
    filters: list = None,
    searchable_columns: list = None,
    exact_search: bool = False,
    search_tokenizer: bool = False,
    search_similarity_threshold: float = 0.1,
    options: list = None,
    primary_column: str = "id",
    sorting_null_at_the_end: bool = True,
    get_function_parameters: dict = None,
    return_available_filters: bool = True,
    return_selected_filters: bool = True,
    return_rows_data: bool = True,
    export_mode: bool = False,
    return_as_dict: bool = True,
    unique: bool = True,
):
    if joins is None:
        joins = []

    if filters is None:
        filters = []

    if searchable_columns is None:
        searchable_columns = []

    if pre_conditions is None:
        pre_conditions = []

    if options is None:
        options = []

    if get_function_parameters is None:
        get_function_parameters = {}

    page = current_query.get("page") or 1
    items_per_page = current_query.get("items_per_page") or 30

    orm_primary_column = getattr(model, primary_column)

    # Create Initial Model Query
    main_query = select(model)

    if unique:
        count_query = select(func.count(distinct_func(orm_primary_column))).select_from(
            model
        )
    else:
        count_query = select(func.count()).select_from(model)

    for join_item in joins:
        main_query = main_query.join(**join_item)
        count_query = count_query.join(**join_item)

    main_query = main_query.where(*pre_conditions)
    count_query = count_query.where(*pre_conditions)

    # Initialize rows and conditions
    conditions = []
    names_conditions = {filter_item.get("name"): [] for filter_item in filters}

    for filter_item in filters:
        name = filter_item.get("name")
        columns = filter_item.get("columns")
        values = current_query.get(name)
        if not columns or not name or not values:
            continue

        target_condition = make_condition(filter_item=filter_item, values=values)
        if target_condition is not None:
            conditions.append(target_condition)
            for inner_name, inner_name_values in names_conditions.items():
                if inner_name != name:
                    inner_name_values.append(target_condition)

    if conditions:
        main_query = main_query.where(*conditions)
        count_query = count_query.where(*conditions)

    if search_query := current_query.get("search"):
        search_conditions, search_sort = free_search(
            columns=searchable_columns,
            query=search_query,
            threshold=search_similarity_threshold,
            exact=exact_search,
            tokenize=search_tokenizer,
        )
        main_query = main_query.where(*search_conditions)
        count_query = count_query.where(*search_conditions)
    else:
        search_sort = None

    if unique:
        main_query = main_query.distinct(orm_primary_column)
        main_query.order_by(orm_primary_column)

    dedup_cte = main_query.cte("dedup_cte")

    sorting = (current_query.get("sorting") or [])

    order_by_list = []
    if search_sort is not None:
        order_by_list.extend(search_sort)
    elif sorting := (current_query.get("sorting") or []):
        for item in sorting:
            order_by = item.get("order_by")
            sort_by = item.get("sort_by")

            if sort_by is None or order_by is None:
                continue

            sort_by = sort_by.value if isinstance(sort_by, Enum) else sort_by
            order_by = order_by.value if isinstance(order_by, Enum) else order_by

            sort_by_model = (
                getattr(model, sort_by) if isinstance(sort_by, str) else sort_by
            )
            order_by_model = (
                getattr(sort_by_model, order_by)
                if isinstance(order_by, str)
                else order_by
            )

            if sorting_null_at_the_end:
                order_by_list.append(order_by_model().nulls_last())
            else:
                order_by_list.append(order_by_model())

    final_query = select(model).join(dedup_cte, orm_primary_column == dedup_cte.c.id)

    if options:
        final_query = final_query.options(*options)

    if order_by_list:
        final_query = final_query.order_by(*order_by_list)

    if items_per_page and page:
        final_query = final_query.limit(items_per_page).offset(
            (page - 1) * items_per_page
        )

    count_query = count_query.order_by(None)

    if return_rows_data:
        db_rows = db.execute(final_query).unique().scalars().all()
        if return_as_dict:
            rows = [
                row.get(**get_function_parameters)
                for row in db_rows
            ]
        else:
            rows = db_rows
    else:
        rows = None

    if export_mode and return_rows_data:
        return rows
    else:
        count = db.execute(count_query).scalar_one()
        current_query["total_row"] = count

        # Calculate pagination-related information
        if items_per_page and page:
            last_page = ceil(count / items_per_page)
            current_query["last_page"] = last_page
            current_query["has_next"] = last_page > page
            current_query["page"] = page
            current_query["items_per_page"] = items_per_page

        result = {
            "payload": current_query,
        }

        if return_rows_data:
            result["rows_data"] = rows

        if return_available_filters:
            result["available_filters"] = (
                get_filters_value(
                    db=db,
                    pre_conditions=pre_conditions,
                    joins=joins,
                    filters=filters,
                    names_conditions=names_conditions,
                )
                if filters is not None
                else []
            )

        if return_selected_filters:
            result["selected_filters"] = make_selected_filters(
                current_query=current_query,
                filters=filters,
            )

        # Return a dictionary containing the filter/sort options, current query data, and rows of data
        return result
