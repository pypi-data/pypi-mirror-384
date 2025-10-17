from __future__ import annotations

from clearskies import configs, decorators
from clearskies.security_header import SecurityHeader


class Hsts(SecurityHeader):
    max_age = configs.Integer(default=31536000)
    include_sub_domains = configs.Boolean()

    @decorators.parameters_to_properties
    def __init__(
        self,
        max_age: int = 31536000,
        include_sub_domains: bool = False,
    ):
        self.finalize_and_validate_configuration()

    def set_headers_for_input_output(self, input_output):
        value = f"max-age={self.max_age} ;"
        if self.include_sub_domains:
            value += " includeSubDomains"
        input_output.response_headers.add("strict-transport-security", value)
