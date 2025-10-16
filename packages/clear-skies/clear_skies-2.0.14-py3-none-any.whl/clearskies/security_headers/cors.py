from __future__ import annotations

from clearskies import configs, decorators
from clearskies.security_header import SecurityHeader


class Cors(SecurityHeader):
    origin = configs.String()
    methods = configs.StringList(default=[])
    headers = configs.StringList(default=[])
    max_age = configs.Integer(default=5)
    credentials = configs.Boolean(default=False)
    expose_headers = configs.StringList(default=[])
    is_cors = True

    @decorators.parameters_to_properties
    def __init__(
        self,
        credentials: bool = False,
        expose_headers: list[str] = [],
        headers: list[str] = [],
        max_age: int = 5,
        methods: list[str] = [],
        origin: str = "",
    ):
        self.finalize_and_validate_configuration()

    def set_headers(self, headers: list[str]):
        self.headers = headers

    def add_header(self, header: str):
        self.headers = [*self.headers, header]

    def set_methods(self, methods: list[str]):
        self.methods = methods

    def add_method(self, method: str):
        self.methods = [*self.methods, method]

    def set_headers_for_input_output(self, input_output):
        for key in ["expose_headers", "methods", "headers"]:
            value = getattr(self, key)
            if not value:
                continue
            input_output.response_headers.add(f"access-control-allow-{key}".replace("_", "-"), ", ".join(value))
        if self.credentials:
            input_output.response_headers.add("access-control-allow-credentials", "true")
        if self.max_age:
            input_output.response_headers.add("access-control-max-age", str(self.max_age))
        if self.origin:
            input_output.response_headers.add("access-control-allow-origin", str(self.origin))
