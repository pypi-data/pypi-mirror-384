import json
import uuid

from sqlalchemy import UUID, Column, DateTime, func, inspect

from ..core.jsonable_encoder import jsonable_encoder

__all__ = ("ModelBase",)


def get_difference_between_dictionaries(old_value, new_value, path=""):
    changes = []

    if isinstance(old_value, dict) and isinstance(new_value, dict):
        # Recursive case for dictionaries
        keys = set(old_value.keys()) | set(new_value.keys())
        for key in keys:
            if key in old_value and key in new_value:
                changes.extend(
                    get_difference_between_dictionaries(
                        old_value[key], new_value[key], f"{path}.{key}" if path else key
                    )
                )
            elif key in old_value:
                changes.append(f"{path}.{key}")
            else:
                changes.append(f"{path}.{key}")
    elif isinstance(old_value, list) and isinstance(new_value, list):
        # Recursive case for lists
        old_items = {json.dumps(item, sort_keys=True): item for item in old_value}
        new_items = {json.dumps(item, sort_keys=True): item for item in new_value}
        old_set, new_set = set(old_items), set(new_items)

        if (old_set - new_set) or (new_set - old_set):
            changes.append(path)

        for item in old_set & new_set:
            old_item = old_items[item]
            new_item = new_items[item]
            if isinstance(old_item, (list, dict)) and old_item != new_item:
                changes.extend(
                    get_difference_between_dictionaries(
                        old_item, new_item, f"{path}[modified]"
                    )
                )
    else:
        # Base case for other types
        if old_value != new_value:
            changes.append(path)

    return changes


def get_modified_keys(instance):
    inst_state = inspect(instance)
    modified_attrs = [
        attr.key for attr in inst_state.attrs if attr.history.has_changes()
    ]
    return modified_attrs


class ModelBase(object):
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    settings = None
    regular_settings_field = False
    combined_settings = True
    need_jsonable_encoder = True
    valid_settings = []

    @classmethod
    def get_fields(cls) -> list:
        fields = list(cls.__table__.columns.keys())
        if "settings" in fields:
            fields.remove("settings")
        return fields

    def get(self, excludes: set = None, includes: set = None) -> dict | None:
        if self is None:
            return

        excludes = excludes or set()
        includes = includes or set()

        model = dict(self.__dict__.items())

        if not self.regular_settings_field:
            if settings := model.get("settings"):
                if self.combined_settings:
                    model = {**settings, **model}
                else:
                    model["settings"] = [
                        {"key": key, "value": value} for key, value in settings.items()
                    ]

            if self.combined_settings and "settings" in model:
                model.pop("settings", None)

        model = {
            k: v
            for k, v in model.items()
            if not k.startswith("_")
            and k not in excludes
            and (not includes or k in includes)
        }
        return model

    @classmethod
    def create(cls, db, data):
        data = jsonable_encoder(data) if cls.need_jsonable_encoder else data
        model_fields = {}

        if not cls.regular_settings_field:
            if cls.combined_settings:
                requested_settings = {}
            else:
                requested_settings = {
                    item["key"]: item["value"]
                    for item in (data.get("settings", []) or [])
                    if item["key"] in cls.valid_settings
                }
        else:
            requested_settings = {}

        for k, v in data.items():
            if k in cls.get_fields():
                model_fields[k] = v
            elif cls.valid_settings and k in cls.valid_settings:
                requested_settings[k] = v

        if cls.valid_settings and requested_settings:
            model_fields["settings"] = requested_settings

        new_model = cls(**model_fields)
        db.add(new_model)
        db.commit()
        db.refresh(new_model)
        return new_model

    def update(self, db, data):
        data = jsonable_encoder(data) if self.need_jsonable_encoder else data

        if not self.regular_settings_field:
            current_settings = self.settings
            if self.combined_settings:
                requested_settings = {}
            else:
                requested_settings = {
                    item["key"]: item["value"]
                    for item in (data.get("settings", []) or [])
                    if item["key"] in self.valid_settings
                }
        else:
            current_settings = {}
            requested_settings = {}

        for k, v in data.items():
            if k in self.get_fields():
                setattr(self, k, v)
            elif (
                self.combined_settings
                and self.valid_settings
                and k in self.valid_settings
            ):
                requested_settings[k] = v

        if (
            not self.regular_settings_field
            and self.valid_settings
            and requested_settings
        ):
            self.settings = (
                {**current_settings, **requested_settings}
                if self.settings
                else requested_settings
            )

        changes = get_modified_keys(self)

        if not self.regular_settings_field:
            if current_settings or requested_settings:
                if "settings" in changes:
                    changes.remove("settings")

                changes.extend(
                    get_difference_between_dictionaries(
                        old_value={
                            k: v
                            for k, v in (current_settings or {}).items()
                            if k in requested_settings
                        },
                        new_value=requested_settings,
                    )
                )

        db.commit()
        db.refresh(self)
        return self
