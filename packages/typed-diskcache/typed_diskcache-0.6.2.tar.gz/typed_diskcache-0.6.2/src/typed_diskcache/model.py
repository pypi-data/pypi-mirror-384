from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Annotated, Any

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, Json, JsonValue

from typed_diskcache.core.const import DEFAULT_SIZE_LIMIT
from typed_diskcache.core.types import (
    EvictionPolicy,
    SQLiteAutoVacuum,
    SQLiteJournalMode,
    SQLiteSynchronous,
)
from typed_diskcache.interface.disk import DiskProtocol

if TYPE_CHECKING:
    from os import PathLike

    from sqlalchemy.engine.interfaces import DBAPIConnection


__all__ = ["Settings"]


def _parse_disk(disk: Any) -> tuple[str, dict[str, JsonValue]]:
    if isinstance(disk, DiskProtocol):
        values = disk.model_dump()
        values[1].pop("directory", None)
        return values
    return disk


class SQLiteSettings(BaseModel):
    model_config = ConfigDict(frozen=True, alias_generator=lambda x: f"sqlite_{x}")

    auto_vacuum: SQLiteAutoVacuum = "FULL"
    cache_size: int = 2**13
    journal_mode: SQLiteJournalMode = "WAL"
    mmap_size: int = 2**26
    synchronous: SQLiteSynchronous = "NORMAL"

    def listen_connect(
        self,
        dbapi_connection: DBAPIConnection,
        connection_record: Any,  # noqa: ARG002
    ) -> None:
        """Listen for connect events."""
        values = self.model_dump()
        cursor = dbapi_connection.cursor()
        for key, value in values.items():
            cursor.execute(f"PRAGMA {key} = {value!s};", ())


class Settings(BaseModel):
    """Settings for the cache."""

    model_config = ConfigDict(frozen=True, use_enum_values=True)

    statistics: bool = False
    eviction_policy: EvictionPolicy = Field(
        default=EvictionPolicy.LEAST_RECENTLY_STORED, validate_default=True
    )
    size_limit: int = DEFAULT_SIZE_LIMIT
    cull_limit: int = 10
    serialized_disk: Annotated[
        tuple[str, dict[str, JsonValue]] | Json[tuple[str, dict[str, JsonValue]]],
        BeforeValidator(_parse_disk),
    ] = Field(default_factory=lambda: ("typed_diskcache.Disk", {}))
    sqlite_settings: SQLiteSettings = Field(default_factory=SQLiteSettings)

    @staticmethod
    def load_disk(cls_path: str | None = None) -> type[DiskProtocol]:
        """Load disk class."""
        if cls_path is None:
            cls_path = "typed_diskcache.Disk"
        module_path, cls_name = cls_path.rsplit(".", 1)
        module = import_module(module_path)
        return getattr(module, cls_name)

    def create_disk(self, directory: str | PathLike[str]) -> DiskProtocol:
        """Create disk instance."""
        cls_path, kwargs = self.serialized_disk

        kwargs.pop("directory", None)
        disk_type = self.load_disk(cls_path)
        return disk_type(directory, **kwargs)
