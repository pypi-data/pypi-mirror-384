from __future__ import annotations

from clearskies.configs import model_column


class WriteableModelColumn(model_column.ModelColumn):
    def get_allowed_columns(self, model_class, column_configs):
        return [name for (name, column) in column_configs.items() if column.is_writeable]

    def my_description(self):
        return "writeable column"
