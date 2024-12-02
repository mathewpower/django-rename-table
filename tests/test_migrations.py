import pytest
from django.db import connection, models
from django_rename_table.operations import RenameTableWithAlias, RemoveAlias


class DynamicTable(models.Model):
    name = models.TextField()

    class Meta:
        app_label = "testapp"
        managed = False


@pytest.mark.django_db
def test_rename_table_with_alias_migration():
    DynamicTable._meta.db_table = "old_table"
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(DynamicTable)

    operation = RenameTableWithAlias("old_table", "new_table")
    operation.database_forwards("testapp", connection.schema_editor(), None, None)

    assert "new_table" in connection.introspection.table_names()

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT table_name
            FROM information_schema.views
            WHERE table_name = 'old_table';
            """
        )
        alias_view = cursor.fetchone()
        assert alias_view is not None

    operation.database_backwards("testapp", connection.schema_editor(), None, None)

    assert "old_table" in connection.introspection.table_names()

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT table_name
            FROM information_schema.views
            WHERE table_name = 'old_table';
            """
        )
        alias_view = cursor.fetchone()
        assert alias_view is None


@pytest.mark.django_db
def test_remove_alias():
    DynamicTable._meta.db_table = "new_table"
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(DynamicTable)

    with connection.cursor() as cursor:
        cursor.execute("CREATE VIEW old_table AS SELECT * FROM new_table;")

    operation = RemoveAlias("old_table")
    operation.database_forwards("testapp", connection.schema_editor(), None, None)

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT table_name
            FROM information_schema.views
            WHERE table_name = 'old_table';
            """
        )
        alias_view = cursor.fetchone()
        assert alias_view is None

    assert "new_table" in connection.introspection.table_names()


@pytest.mark.django_db
def test_crud_on_renamed_model_with_alias_table():
    DynamicTable._meta.db_table = "old_table"
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(DynamicTable)

    rename_operation = RenameTableWithAlias("old_table", "new_table")
    rename_operation.database_forwards(
        "testapp", connection.schema_editor(), None, None
    )

    DynamicTable._meta.db_table = "old_table"

    DynamicTable.objects.create(name="Test Entry")
    assert DynamicTable.objects.filter(name="Test Entry").exists()

    instance = DynamicTable.objects.get(name="Test Entry")
    assert instance.name == "Test Entry"

    instance.name = "Updated Entry"
    instance.save()
    assert DynamicTable.objects.filter(name="Updated Entry").exists()

    instance.delete()
    assert not DynamicTable.objects.filter(name="Updated Entry").exists()

    rename_operation.database_backwards(
        "testapp", connection.schema_editor(), None, None
    )
    DynamicTable._meta.db_table = "old_table"

    assert "old_table" in connection.introspection.table_names()
    assert "new_table" not in connection.introspection.table_names()
