from typing import Any

__all__ = ("make_selected_filters",)


def make_selected_filters(
    filters: list = None,
    current_query: dict[str, Any] = None,
):
    selected_filters = []
    for filter_item in filters:
        selected_data: dict | list | None = current_query.get(filter_item["name"])
        if not selected_data or len(selected_data) == 0:
            continue

        if (
            isinstance(selected_data, dict)
            and len([k for k, v in selected_data.items() if v is not None]) == 0
        ):
            continue

        if filter_item["type"] in {"select", "select_array"}:
            for data in selected_data:
                enum = filter_item.get("enum")
                labels = filter_item.get("labels", {})
                if enum:
                    data = getattr(enum, str(data), data)

                selected_filters.append(
                    {
                        "label": labels.get(enum(data) if enum else data, data),
                        "name": filter_item["name"],
                        "value": enum(data).name if enum else data,
                        "type": filter_item["type"],
                    }
                )
        elif filter_item["type"] == "number":
            minimum = selected_data.get("min")
            maximum = selected_data.get("max")
            if minimum is not None and maximum is not None:
                result_label = (
                    f"{filter_item['label']} (between {minimum} and {maximum})"
                )
            elif minimum is None and maximum is not None:
                result_label = f"{filter_item['label']} (To {maximum})"
            elif minimum is not None and maximum is None:
                result_label = f"{filter_item['label']} (From {minimum})"
            else:
                result_label = filter_item["label"]

            selected_filters.append(
                {
                    "label": result_label,
                    "name": filter_item["name"],
                    "value": selected_data,
                    "type": filter_item["type"],
                }
            )
        elif filter_item["type"] == "date":
            minimum = selected_data.get("min")
            maximum = selected_data.get("max")
            if minimum is not None and maximum is not None:
                result_label = f"{filter_item['label']} (From {minimum} To {maximum})"
            elif minimum is None and maximum is not None:
                result_label = f"{filter_item['label']} (To {maximum})"
            elif minimum is not None and maximum is None:
                result_label = f"{filter_item['label']} (From {minimum})"
            else:
                result_label = filter_item["label"]

            selected_filters.append(
                {
                    "label": result_label,
                    "name": filter_item["name"],
                    "value": selected_data,
                    "type": filter_item["type"],
                }
            )
        elif filter_item["type"] == "search":
            selected_filters.append(
                {
                    "label": f"Search ({selected_data})",
                    "name": filter_item["name"],
                    "value": selected_data,
                    "type": filter_item["type"],
                }
            )

    return selected_filters
