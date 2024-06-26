# database\_schema\_ensurer

Ensures that the database schema is at a certain version.

## Installation

`pip install database_schema_ensurer`

## Usage

Put your migrations in a directory. Each migration SQL file name must obey these rules:
* Start with `{version}_` (e.g. `1_init.sql.up`)
* Have two versions: `.up.sql` for upgrading (adding the necessary things) and `.down.sql` for downgrading (undoing the upgrade) (must have the specified extensions)

```
from database_schema_ensurer import migrate, Database

class MyDatabase(Database):
    ...
    # Implement all the methods or use a library:
    # * Postgres: postgres_schema_ensurer

migrate(
    MyDatabase(...),
    target_version=OPTIONAL_SPECIFIC_VERSION, # Default: greatest version from the directory
    migrations_directory=OPTIONAL_SPECIFIC_DIRECTORY, # Default: "migrations"
)
```
