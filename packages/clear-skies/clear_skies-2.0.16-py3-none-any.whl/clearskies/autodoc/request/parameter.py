class Parameter:
    location = ""
    in_body = False

    def __init__(self, definition, description="", required=False):
        self.definition = definition
        self.description = description
        self.required = required
