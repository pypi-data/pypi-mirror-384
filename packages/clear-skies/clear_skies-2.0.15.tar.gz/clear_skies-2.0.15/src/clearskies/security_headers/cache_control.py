from __future__ import annotations

from clearskies import configs, decorators
from clearskies.security_header import SecurityHeader


class CacheControl(SecurityHeader):
    max_age = configs.Integer()
    s_maxage = configs.Integer()
    stale_while_revalidate = configs.Integer()
    stale_if_error = configs.Integer()
    immutable = configs.Boolean(default=False)
    must_understand = configs.Boolean(default=False)
    no_cache = configs.Boolean(default=False)
    no_store = configs.Boolean(default=False)
    no_transform = configs.Boolean(default=False)
    private = configs.Boolean(default=False)
    public = configs.Boolean(default=False)

    numbers: list[str] = [
        "max_age",
        "stale_if_error",
        "stale_while_revalidate",
        "s_maxage",
    ]
    bools: list[str] = [
        "immutable",
        "must_understand",
        "no_cache",
        "no_store",
        "no_transform",
        "private",
        "public",
    ]

    @decorators.parameters_to_properties
    def __init__(
        self,
        max_age: int | None = None,
        s_maxage: int | None = None,
        stale_while_revalidate: int | None = None,
        stale_if_error: int | None = None,
        immutable: bool = False,
        must_understand: bool = False,
        no_cache: bool = False,
        no_store: bool = False,
        no_transform: bool = False,
        private: bool = False,
        public: bool = False,
    ):
        self.finalize_and_validate_configuration()

    def set_headers_for_input_output(self, input_output):
        parts = []
        for variable_name in self.bools:
            value = getattr(self, variable_name)
            if not value:
                continue
            parts.append(variable_name.replace("_", "-"))
        for variable_name in self.numbers:
            value = getattr(self, variable_name)
            if value is None:
                continue
            key_name = variable_name.replace("_", "-")
            parts.append(f"{key_name}={value}")
        if not parts:
            return
        input_output.response_headers.add("cache-control", ", ".join(parts))
