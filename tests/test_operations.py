import pytest
from django_rename_table.operations import (
    RenameTableWithAlias,
    RemoveAlias,
    UnsupportedDatabaseError,
)
from django.db.migrations.state import ModelState, ProjectState


def test_rename_table_with_alias_forward(mocker):
    schema_editor = mocker.Mock()
    operation = RenameTableWithAlias("test_table", "test_table_renamed")

    mocker.patch("django_rename_table.operations.connection.vendor", "postgresql")

    operation.database_forwards("myapp", schema_editor, None, None)

    schema_editor.execute.assert_has_calls(
        [
            mocker.call("ALTER TABLE test_table RENAME TO test_table_renamed;"),
            mocker.call("CREATE VIEW test_table AS SELECT * FROM test_table_renamed;"),
        ]
    )


def test_rename_with_alias_describe():
    operation = RenameTableWithAlias("test_table", "test_table_renamed")
    assert (
        operation.describe()
        == "Rename table test_table to test_table_renamed with alias"
    )


def test_rename_table_with_alias_backward(mocker):
    schema_editor = mocker.Mock()
    operation = RenameTableWithAlias("test_table", "test_table_renamed")

    mocker.patch("django_rename_table.operations.connection.vendor", "postgresql")

    operation.database_backwards("myapp", schema_editor, None, None)

    schema_editor.execute.assert_has_calls(
        [
            mocker.call("DROP VIEW test_table;"),
            mocker.call("ALTER TABLE test_table_renamed RENAME TO test_table;"),
        ]
    )


def test_rename_table_with_alias_state_forwards():
    project_state = ProjectState()
    model_state = ModelState(
        app_label="myapp",
        name="TestModel",
        fields=[],
        options={"db_table": "test_table"},
        bases=(object,),
        managers=[],
    )
    project_state.models["myapp.TestModel"] = model_state

    operation = RenameTableWithAlias("test_table", "test_table_renamed")
    operation.state_forwards("myapp", project_state)

    updated_model_state = project_state.models["myapp.TestModel"]
    assert updated_model_state.options["db_table"] == "test_table_renamed"


def test_rename_table_with_alias_unsupported_database(mocker):
    schema_editor = mocker.Mock()
    operation = RenameTableWithAlias("test_table", "test_table_renamed")

    mocker.patch("django_rename_table.operations.connection.vendor", "sqlite")

    with pytest.raises(
        UnsupportedDatabaseError,
        match="This operation is only supported on postgresql",
    ):
        operation.database_forwards("myapp", schema_editor, None, None)


def test_remove_alias_forward(mocker):
    schema_editor = mocker.Mock()
    operation = RemoveAlias("test_table_view")

    mocker.patch("django_rename_table.operations.connection.vendor", "postgresql")

    operation.database_forwards("myapp", schema_editor, None, None)

    schema_editor.execute.assert_called_once_with("DROP VIEW test_table_view;")


def test_remove_alias_describe():
    operation = RemoveAlias("test_table_view")
    assert operation.describe() == "Remove alias test_table_view"


def test_remove_alias_unsupported_database(mocker):
    schema_editor = mocker.Mock()
    operation = RemoveAlias("test_table_view")

    mocker.patch("django_rename_table.operations.connection.vendor", "sqlite")

    with pytest.raises(
        UnsupportedDatabaseError,
        match="This operation is only supported on postgresql",
    ):
        operation.database_forwards("myapp", schema_editor, None, None)


def test_remove_alias_backward_not_implemented(mocker):
    schema_editor = mocker.Mock()
    operation = RemoveAlias("test_table_view")

    with pytest.raises(NotImplementedError, match="Alias removal cannot be reversed."):
        operation.database_backwards("myapp", schema_editor, None, None)


def test_remove_alias_state_forwards():
    project_state = ProjectState()

    operation = RemoveAlias("test_table_view")
    operation.state_forwards("myapp", project_state)

    assert project_state.models == {}
