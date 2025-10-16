from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any

from clearskies.validator import Validator

if TYPE_CHECKING:
    from clearskies import Model


class Unique(Validator):
    is_unique = True

    def check(self, model: Model, column_name: str, data: dict[str, Any]) -> str:
        # Unique is mildly tricky.  We obviously want to search the backend for the new value,
        # but we need to first skip this if our column is not being set, or if we're editing
        # the model and nothing is changing.
        if column_name not in data:
            return ""
        new_value = data[column_name]
        if model and getattr(model, column_name) == new_value:
            return ""

        as_query = model.as_query()
        matching_model = as_query.find(f"{column_name}={new_value}")
        if matching_model:
            return f"Invalid value for '{column_name}': the given value already exists, and must be unique."
        return ""
