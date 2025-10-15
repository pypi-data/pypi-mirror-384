from sqlalchemy import func, union
from sqlalchemy.orm import Session

__all__ = ("get_filters_value",)


def filters_mapper(
    db: Session, pre_conditions: list, joins: list[dict], filter_item, conditions
):
    columns = filter_item.get("columns")
    columns_type = filter_item.get("type", "select")

    if columns_type in {"select", "select_array"}:
        distinct_names_query = []
        for column in columns:
            query = db.query(
                func.jsonb_array_elements_text(column)
                if filter_item.get("is_json", False)
                else column
            )

            for join_item in joins:
                query = query.join(**join_item)

            distinct_names_query.append(
                query.filter(*pre_conditions, *conditions).distinct()
            )

        values = []
        db_values = list(map(lambda x: x[0], db.execute(union(*distinct_names_query)).fetchall()))
        if columns_type == "select_array":
            for db_value in db_values:
                if isinstance(db_value, list):
                    values.extend(db_value)
        else:
            if isinstance(db_values, list):
                values.extend(db_values)

        enum = filter_item.get("enum")
        labels = filter_item.get("labels", {})
        items = [
            {
                "label": labels.get(enum(value) if enum else value, value),
                "value": enum(value).name if enum else value,
            }
            for value in values
            if value is not None
        ]
        items = sorted(items, key=lambda x: x.get("label"))
    elif columns_type in ["number", "date"]:
        main_query = db.query(
            func.least(*list(map(func.min, columns))),
            func.greatest(*list(map(func.max, columns))),
        )
        for join_item in joins:
            main_query = main_query.join(**join_item)

        min_value, max_value = main_query.filter(*pre_conditions, *conditions).first()
        items = {"min": min_value, "max": max_value}
    else:
        items = None

    return items


def get_filters_value(
    db: Session,
    pre_conditions: list,
    joins: list[dict],
    filters: list,
    names_conditions: dict,
):
    available_filters = []
    for filter_item in filters:
        filter_name_conditions = names_conditions.get(filter_item["name"])
        if filter_name_conditions is None:
            continue
        filter_mapping_result = filters_mapper(
            db=db,
            pre_conditions=pre_conditions,
            joins=joins,
            filter_item=filter_item,
            conditions=filter_name_conditions,
        )
        filter_label = filter_item.get("label")
        filter_type = filter_item.get("type")
        filter_name = filter_item.get("name")
        if filter_mapping_result is not None:
            if filter_type in {"select", "select_array"}:
                available_filters.append(
                    {
                        "label": filter_label,
                        "name": filter_name,
                        "type": filter_type,
                        "value": filter_mapping_result,
                    }
                )
            elif filter_type in ["number", "date"]:
                available_filters.append(
                    {
                        "label": filter_label,
                        "name": filter_name,
                        "type": filter_type,
                        "value": filter_mapping_result,
                    }
                )
            else:
                available_filters.append(
                    {
                        "label": filter_label,
                        "name": filter_name,
                        "type": filter_type,
                    }
                )

    return available_filters
