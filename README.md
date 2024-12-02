# Django Rename Table

This package provides the ability to create (and remove) an alias of a database table.

You may wish to do this when renaming database tables and want to avoid downtime.

Renaming tables on a live system can be problematic. If you run the migration to raname the table first then any
previous running versions of the code will start to error as they can no longer find the model's table.

Deploying the updated code first and then migrating would also fail for similar reasons.

A solution to this is to use this tool and a multistep process.

## Instructions

### 1) Rename the table
This renames the table and create an alias with the original name.

```python
from django.db import migrations
from django_rename_table.operations import RenameTableWithAlias

class Migration(migrations.Migration):
    dependencies = [
        ("myapp", "0001_initial"),
    ]

    operations = [
        RenameTableWithAlias("old_table_name", "new_table_name"),
    ]
```

### 2) Apply the migration
```python manage.py migrate```

### 3) Update model to point at renamed table
```python
from django.db import models

class MyModel(models.Model):
    name = models.CharField(max_length=1000)

    class Meta:
        db_table = "new_table_name"
```


### 4) Delete alias when you're happy no deployed code is using the old table
```python
from django.db import migrations
from django_rename_table.operations import RemoveAlias

class Migration(migrations.Migration):
    dependencies = [
        ("myapp", "0002_rename_and_create_alias"),
    ]

    operations = [
        RemoveAlias("old_table_name"),
    ]
```

## License
This project is licensed under the MIT License. See the LICENSE file for details.

## Contributing
Contributions are welcome! Please submit a pull request or open an issue to report bugs or suggest features.
