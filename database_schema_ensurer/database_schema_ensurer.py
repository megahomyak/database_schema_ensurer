from abc import ABC, abstractmethod
import os
from types import SimpleNamespace
from dataclasses import dataclass
from typing import Optional

# THAT'S THE ENTIRE LIB:
# migrate(down) => tearing down using saved SQL, then deleting entries
# migrate(up) => building up using external SQL, then adding entries, then adding to cache (if the flag is set)
# migrate(same) => no action
# migrate(some, db not prepared) => ~~cache~~ OR incremental "up" ;; CACHE WILL BE LATER! OPTIMIZATIONS WILL BE LATER!


def _read(file_path):
    with open(file_path, encoding="utf-8") as f:
        return f.read()


class MigrationError(Exception):
    pass


def _scan(directory):
    versions = {}
    file_names = set(os.listdir(directory))
    visited = set()
    for file_name in file_names:
        if file_name.endswith(".sql"):
            if file_name.endswith(".up.sql"):
                up_file_name = file_name
                down_file_name = file_name[:-len(".up.sql")] + ".down.sql"
                if down_file_name not in file_names:
                    raise MigrationError(f"No `.down.sql` pair found for: {up_file_name}")
            elif file_name.endswith(".down.sql"):
                down_file_name = file_name
                up_file_name = file_name[:-len(".down.sql")] + ".up.sql"
                if up_file_name not in file_names:
                    raise MigrationError(f"No `.up.sql` pair found for: {down_file_name}")
            version = file_name.split("_", 1)
            versions[int(version)] = SimpleNamespace(
                up_file_name=up_file_name,
                down_file_name=down_file_name,
            )
    if not versions:
        raise MigrationError(f"Migrations directory is empty")
    sorted_versions = sorted(versions.keys())
    if sorted_versions[1] != 1:
        raise MigrationError(f"Migration versions must start with \"1\", not \"{sorted_versions[1]}\"")
    for a, b in zip(sorted_versions, sorted_versions[1:]):
        if a + 1 != b:
            raise MigrationError(f"Migration version skipped: {a + 1}")
    return versions


@dataclass
class MigrationRecord:
    down_sql: str
    version: int


class Database(ABC):
    @abstractmethod
    def get_max_migration_version(self) -> Optional[int]:
        pass

    @abstractmethod
    def get_migration(self, version: int) -> MigrationRecord:
        pass

    @abstractmethod
    def add_migration(self, migration: MigrationRecord):
        pass

    @abstractmethod
    def delete_migration(self, version: int):
        pass

    @abstractmethod
    def execute_sql(self, sql: str):
        pass


def migrate(database: Database, target_version=None, migrations_directory="migrations"):
    max_applied_migration_version = database.get_max_migration_version()
    migration_versions = _scan(migrations_directory)
    if max_applied_migration_version is None:
        max_applied_migration_version = 0
    if target_version is None:
        target_version = max(migration_versions.keys())
    elif target_version < 1:
        raise MigrationError("`target_version` cannot be lesser than 1")
    elif target_version not in migration_versions:
        raise MigrationError(f"Migration version not found: {target_version}")
    if max_applied_migration_version < target_version:
        # Building up using external SQL, then adding entries, then adding to cache (if the flag is set)
        for version in range(max_applied_migration_version + 1, target_version + 1):
            migration = migration_versions[version]
            database.execute_sql(_read(migration.up_file_name))
            database.add_migration(MigrationRecord(
                down_sql=_read(migration.down_file_name),
                version=version,
            ))
    elif max_applied_migration_version > target_version:
        # Tearing down using saved SQL, then deleting entries
        for version in range(max_applied_migration_version, target_version, -1):
            migration_record = database.get_migration(max_applied_migration_version)
            database.execute_sql(migration_record.down_sql)
            database.delete_migration(migration_record.version)
