from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Callable, Self, overload

from clearskies import configs, decorators
from clearskies.column import Column

if TYPE_CHECKING:
    from clearskies import Model, typing


class Json(Column):
    """
    A column to store generic data.

    ```python
    import clearskies


    class MyModel(clearskies.Model):
        backend = clearskies.backends.MemoryBackend()
        id_column_name = "id"

        id = clearskies.columns.Uuid()
        my_data = clearskies.columns.Json()


    wsgi = clearskies.contexts.WsgiRef(
        clearskies.endpoints.Create(
            MyModel,
            writeable_column_names=["my_data"],
            readable_column_names=["id", "my_data"],
        ),
        classes=[MyModel],
    )
    wsgi()
    ```

    And when invoked:

    ```bash
    $ curl 'http://localhost:8080' -d '{"my_data":{"count":[1,2,3,4,{"thing":true}]}}' | jq
    {
        "status": "success",
        "error": "",
        "data": {
            "id": "63cbd5e7-a198-4424-bd35-3890075a2a5e",
            "my_data": {
                "count": [
                    1,
                    2,
                    3,
                    4,
                    {
                        "thing": true
                    }
                ]
            }
        },
        "pagination": {},
        "input_errors": {}
    }
    ```

    Note that there is no attempt to check the shape of the input passed into a JSON column.

    """

    setable = configs.Any(default=None)  # type: ignore
    default = configs.Any(default=None)  # type: ignore
    is_searchable = configs.Boolean(default=False)
    _descriptor_config_map = None

    @decorators.parameters_to_properties
    def __init__(
        self,
        default: dict[str, Any] | list[Any] | None = None,
        setable: dict[str, Any] | list[Any] | Callable[..., dict[str, Any]] | None = None,
        is_readable: bool = True,
        is_writeable: bool = True,
        is_temporary: bool = False,
        validators: typing.validator | list[typing.validator] = [],
        on_change_pre_save: typing.action | list[typing.action] = [],
        on_change_post_save: typing.action | list[typing.action] = [],
        on_change_save_finished: typing.action | list[typing.action] = [],
        created_by_source_type: str = "",
        created_by_source_key: str = "",
        created_by_source_strict: bool = True,
    ):
        pass

    @overload
    def __get__(self, instance: None, cls: type[Model]) -> Self:
        pass

    @overload
    def __get__(self, instance: Model, cls: type[Model]) -> dict[str, Any]:
        pass

    def __get__(self, instance, cls):
        return super().__get__(instance, cls)

    def __set__(self, instance, value: dict[str, Any]) -> None:
        # this makes sure we're initialized
        if "name" not in self._config:  # type: ignore
            instance.get_columns()

        instance._next_data[self.name] = value

    def from_backend(self, value) -> dict[str, Any] | list[Any] | None:
        if isinstance(value, (list, dict)):
            return value
        if not value:
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return None

    def to_backend(self, data):
        if self.name not in data or data[self.name] is None:
            return data

        value = data[self.name]
        return {**data, self.name: value if isinstance(value, str) else json.dumps(value)}
