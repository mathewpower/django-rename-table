from django.db.migrations.operations.base import Operation
from django.db import connection
from django.db.migrations.state import ModelState


_SUPPORTED_BACKEND = "postgresql"


class UnsupportedDatabaseError(Exception):
    pass


def ensure_supported_database():
    backend = connection.vendor
    if backend != _SUPPORTED_BACKEND:
        raise UnsupportedDatabaseError(
            f"This operation is only supported on {_SUPPORTED_BACKEND}. "
            f"Current backend: {backend}"
        )


class RenameTableWithAlias(Operation):
    reversible = True

    def __init__(self, old_table_name, new_table_name):
        self.old_table_name = old_table_name
        self.new_table_name = new_table_name

    def state_forwards(self, app_label, state):
        for model_name, model_state in state.models.items():
            if model_state.options.get("db_table") == self.old_table_name:
                state.models[model_name] = ModelState(
                    app_label=app_label,
                    name=model_state.name,
                    fields=model_state.fields,
                    options={**model_state.options, "db_table": self.new_table_name},
                    bases=model_state.bases,
                    managers=model_state.managers,
                )
                break

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        ensure_supported_database()
        schema_editor.execute(
            f"ALTER TABLE {self.old_table_name} RENAME TO {self.new_table_name};"
        )
        schema_editor.execute(
            f"CREATE VIEW {self.old_table_name} AS SELECT * FROM {self.new_table_name};"
        )

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        ensure_supported_database()
        schema_editor.execute(f"DROP VIEW {self.old_table_name};")
        schema_editor.execute(
            f"ALTER TABLE {self.new_table_name} RENAME TO {self.old_table_name};"
        )

    def describe(self):
        return f"Rename table {self.old_table_name} to {self.new_table_name} with alias"


class RemoveAlias(Operation):
    reversible = True

    def __init__(self, alias_name):
        self.alias_name = alias_name

    def state_forwards(self, app_label, state):
        pass

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        ensure_supported_database()
        schema_editor.execute(f"DROP VIEW {self.alias_name};")

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        raise NotImplementedError("Alias removal cannot be reversed.")

    def describe(self):
        return f"Remove alias {self.alias_name}"
