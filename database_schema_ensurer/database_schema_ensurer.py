from abc import ABC, abstractmethod
from typing import Dict, Optional
from dataclasses import dataclass
import os


class NotFound(Exception):
    pass


class AlreadyExists(Exception):
    pass


class FileNameCollision(Exception):
    pass


@dataclass
class InvalidMigrationFileName(Exception):
    file_name: str


@dataclass
class MigrationFileNotFound(Exception):
    pair_file_name: str


@dataclass
class VersionSkipped(Exception):
    version: int


_Version = int


@dataclass
class _Migration:
    up_sql: str
    down_sql: str


@dataclass
class SchemaUpdateRecord:
    """
    A record of when the schema was updated, including the version number (`version`) and the code needed to downgrade to the previous version of the schema (`downgrade_sql`)
    """
    version: int
    downgrade_sql: str


_UP_SQL = ".up.sql"
def _read_migrations(directory: str) -> Dict[_Version, _Migration]:
    versions: Dict[_Version, _Migration] = {}
    for file_name in os.listdir(directory):
        if file_name.endswith(_UP_SQL):
            try:
                version_number, _ = file_name.split("_", 1)
                version_number = int(version_number)
                if version_number < 1:
                    raise ValueError
            except ValueError:
                raise InvalidMigrationFileName(file_name)
            up_file_name = file_name
            down_file_name = up_file_name[:-len(_UP_SQL)] + ".down.sql"
            with open(up_file_name, encoding="utf-8") as f:
                up_file_sql = f.read()
            try:
                with open(down_file_name, encoding="utf-8") as f:
                    down_file_sql = f.read()
            except FileNotFoundError:
                raise MigrationFileNotFound(pair_file_name=down_file_name)
            if version_number in versions:
                raise InvalidMigrationFileName()
            versions[version_number] = _Migration(
                up_sql=up_file_sql,
                down_sql=down_file_sql,
            )
    current_version = 1
    for version in sorted(versions.keys()):
        if version == current_version:
            current_version += 1
        else:
            raise VersionSkipped(current_version)
    return versions


class Ensurer(ABC):
    """
    A note for implementors: please, allow the user to specify where the migration records will be stored. I don't want the users to have stupid collisions because of this library
    """

    def migrate(self, target_version: Optional[int] = None, migrations_directory: str = "migrations") -> None:
        """
        `target_version` is the desired schema version (the version you want to have after running this function).

        If `target_version` is `None`, the last accessible version (from the migrations directory) is chosen
        """
        migrations = _read_migrations(migrations_directory)
        try:
            latest_schema_update_record = self.get_schema_update_record_with_greatest_version()
        except NotFound:
            if migrations:
                pass # TODO try to load from cache
            else:
                raise NotFound("No migration files are present, cannot migrate")
        else:
            schema_version = schema_row.version
        if schema_version == target_version:
            return
        elif schema_row.version > target_version:
            # We need to downgrade

        elif schema_row.version < target_version:
            # We need to upgrade

    @abstractmethod
    def execute_sql(self, sql: str) -> None:
        """
        Might raise any database-specific errors
        """
        pass

    @abstractmethod
    def get_schema_update_record_with_greatest_version(self) -> SchemaUpdateRecord:
        """
        Must raise `NotFound` (from this module) when the entry is not found (that is, there are no entries at all yet); might raise any database-specific errors
        """
        pass

    @abstractmethod
    def get_schema_update_record(self, version: int) -> SchemaUpdateRecord:
        """
        Must raise `NotFound` (from this module) when the entry is not found; might raise any database-specific errors
        """
        pass

    @abstractmethod
    def remove_schema_update_record(self, version: int):
        """
        Must raise `NotFound` (from this module) when the entry is not found; might raise any database-specific errors
        """
        pass

    @abstractmethod
    def add_schema_update_record(self, schema_update_record: SchemaUpdateRecord) -> int:
        """
        Might raise any database-specific errors. If a record with the specified version number already exists, this function must raise `AlreadyExists` (from this module)
        """
        pass


class PostgresEnsurer(Ensurer):
