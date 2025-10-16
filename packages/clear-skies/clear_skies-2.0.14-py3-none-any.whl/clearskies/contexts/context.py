from __future__ import annotations

import datetime
from types import ModuleType
from typing import TYPE_CHECKING, Any, Callable

from clearskies import exceptions
from clearskies.di import Di
from clearskies.di.additional_config import AdditionalConfig
from clearskies.input_outputs import InputOutput
from clearskies.input_outputs import Programmatic

if TYPE_CHECKING:
    from clearskies.endpoint import Endpoint
    from clearskies.endpoint_group import EndpointGroup


class Context:
    """Context: a flexible way to connect applications to hosting strategies."""

    di: Di = None  # type: ignore

    """
    The application to execute.

    This can be a callable, an endpoint, or an endpoint group.  If passed a callable, the callable can request any
    standard or defined dependencies and should return the desired response.  It can also raise any exception from
    exceptions.
    """
    application: Callable | Endpoint | EndpointGroup = None  # type: ignore

    def __init__(
        self,
        application: Callable | Endpoint | EndpointGroup,
        classes: type | list[type] = [],
        modules: ModuleType | list[ModuleType] = [],
        bindings: dict[str, Any] = {},
        additional_configs: AdditionalConfig | list[AdditionalConfig] = [],
        class_overrides: dict[type, Any] = {},
        overrides: dict[str, type] = {},
        now: datetime.datetime | None = None,
        utcnow: datetime.datetime | None = None,
    ):
        self.di = Di(
            classes=classes,
            modules=modules,
            bindings=bindings,
            additional_configs=additional_configs,
            class_overrides=class_overrides,
            overrides=overrides,
            now=now,
            utcnow=utcnow,
        )
        self.application = application

    def execute_application(self, input_output: InputOutput):
        self.di.add_binding("input_output", input_output)
        self.di.add_class_override(InputOutput, input_output)

        if hasattr(self.application, "injectable_properties"):
            self.application.injectable_properties(self.di)
            return self.application(input_output)
        elif callable(self.application):
            try:
                return input_output.respond(
                    self.di.call_function(self.application, **input_output.get_context_for_callables())
                )
            except exceptions.ClientError as e:
                return input_output.respond(str(e), 400)
            except exceptions.Authentication as e:
                return input_output.respond(str(e), 401)
            except exceptions.Authorization as e:
                return input_output.respond(str(e), 403)
            except exceptions.NotFound as e:
                return input_output.respond(str(e), 404)
            except exceptions.MovedPermanently as e:
                return input_output.respond(str(e), 302)
            except exceptions.MovedTemporarily as e:
                return input_output.respond(str(e), 307)

    def __call__(
        self,
        url: str = "",
        request_method: str = "GET",
        body: str | dict[str, Any] | list[Any] = "",
        query_parameters: dict[str, str] = {},
        request_headers: dict[str, str] = {},
    ):
        return self.execute_application(
            Programmatic(
                url=url,
                request_method=request_method,
                body=body,
                query_parameters=query_parameters,
                request_headers=request_headers,
            )
        )

    def build(self, thing: Any, cache: bool = False) -> Any:
        return self.di.build(thing, cache=cache)
