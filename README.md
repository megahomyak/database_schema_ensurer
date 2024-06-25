# db\_schema\_ensurer

Ensures that the DB schema is at a certain version.

## Usage

Put your migrations in a directory. Each migration SQL file name must obey these rules:
* Start with `{version}_` (e.g. `1_init.sql.up`)
* Have two versions: `.up.sql` for upgrading (adding the necessary things) and `.down.sql` for downgrading (undoing the upgrade) (must have the specified extensions)

```
from db_schema_ensurer import migrate, Database

class MyDatabase(Database):
    ...
    # Implement all the methods or use a library:
    # * Postgres: pg_schema_ensurer

migrate(MyDatabase(...))
# You can also specify `target_version=` if you want a specific version,
# And you may also specify `migrations_directory` to change the directory the migrations are found at
```
