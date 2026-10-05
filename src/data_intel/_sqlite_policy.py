"""Private installers for the reviewed m2-sqlite.v1 connection controls."""

import sqlite3
import time
from contextlib import suppress
from dataclasses import dataclass
from typing import Literal

MAX_HEAP_BYTES = 8_388_608
MAX_PROGRESS_CALLBACKS = 500
_LIMITS = (
    ("SQL_LENGTH", 8_000),
    ("LENGTH", 65_536),
    ("COLUMN", 16),
    ("EXPR_DEPTH", 30),
    ("COMPOUND_SELECT", 8),
    ("VDBE_OP", 10_000),
    ("FUNCTION_ARG", 8),
    ("ATTACHED", 0),
    ("LIKE_PATTERN_LENGTH", 128),
    ("VARIABLE_NUMBER", 0),
    ("TRIGGER_DEPTH", 0),
)
_FUNCTION_NAMES = (
    "sum count min max avg abs round coalesce nullif lower upper length substr like "
    "strftime row_number rank dense_rank lag lead"
)
_FUNCTIONS = frozenset(_FUNCTION_NAMES.split())
_SALES_COLUMN_NAMES = "sale_id sale_date customer region product units revenue_cents"
_SALES_COLUMNS = frozenset(_SALES_COLUMN_NAMES.split())


class PolicyFailure(RuntimeError):
    """Safe policy failure without input, database or SQLite diagnostic details."""

    def __init__(self) -> None:
        self.code: Literal["runtime_incompatible"] = "runtime_incompatible"
        super().__init__(self.code)


@dataclass(slots=True)
class _Audit:
    sales_reads: int = 0
    denied: bool = False


@dataclass(slots=True)
class _ProgressBudget:
    started: float | None
    callbacks: int = 0
    reason: Literal["vm", "time"] | None = None

    def __call__(self) -> int:
        self.callbacks += 1
        if self.callbacks >= MAX_PROGRESS_CALLBACKS:
            self.reason = "vm"
            return 1
        try:
            now = time.monotonic()
        except (OSError, RuntimeError):
            now = None
        if now is None:
            return 0
        if self.started is None:
            self.started = now
        elif now - self.started >= 0.250:
            self.reason = "time"
            return 1
        return 0


@dataclass(frozen=True, slots=True)
class _PolicyEvidence:
    heap_bytes: int
    pragmas: tuple[tuple[str, int], ...]
    limits: tuple[tuple[str, int], ...]
    audit: _Audit
    progress: _ProgressBudget


def _memory_only(connection: sqlite3.Connection) -> None:
    databases = connection.execute("PRAGMA database_list").fetchall()
    if databases != [(0, "main", "")]:
        raise PolicyFailure()


def _set_heap_limit(connection: sqlite3.Connection) -> int:
    connection.execute(f"PRAGMA hard_heap_limit={MAX_HEAP_BYTES}")
    actual = connection.execute("PRAGMA hard_heap_limit").fetchone()
    if actual is None or type(actual[0]) is not int or not 0 < actual[0] <= MAX_HEAP_BYTES:
        raise PolicyFailure()
    return actual[0]


def _set_limits(connection: sqlite3.Connection) -> tuple[tuple[str, int], ...]:
    if not callable(getattr(connection, "setlimit", None)) or not callable(
        getattr(connection, "getlimit", None)
    ):
        raise PolicyFailure()
    effective: list[tuple[str, int]] = []
    for name, maximum in _LIMITS:
        category = getattr(sqlite3, f"SQLITE_LIMIT_{name}")
        connection.setlimit(category, maximum)
        value = connection.getlimit(category)
        if value != maximum:
            raise PolicyFailure()
        effective.append((name.lower(), value))
    return tuple(effective)


def _set_pragma(connection: sqlite3.Connection, name: str, value: int) -> int:
    connection.execute(f"PRAGMA {name}={value}")
    actual = connection.execute(f"PRAGMA {name}").fetchone()
    if actual is None or actual[0] != value:
        raise PolicyFailure()
    return int(actual[0])


def _is_sales_read(table: str | None, column: str | None, database: str | None) -> bool:
    if (table or "").lower() != "sales":
        return False
    if not column:
        return (database or "").lower() == "main"
    return (database or "").lower() == "main" and column in _SALES_COLUMNS


def _is_allowed_function(first: str | None, second: str | None) -> bool:
    return (second or first or "").lower() in _FUNCTIONS


def _install_authorizer(connection: sqlite3.Connection, audit: _Audit) -> None:
    def authorize(
        action: int,
        first: str | None,
        second: str | None,
        database: str | None,
        trigger: str | None,
    ) -> int:
        del trigger
        if action == sqlite3.SQLITE_SELECT:
            return sqlite3.SQLITE_OK
        if action == sqlite3.SQLITE_READ and _is_sales_read(first, second, database):
            audit.sales_reads += 1
            return sqlite3.SQLITE_OK
        if action == sqlite3.SQLITE_FUNCTION and _is_allowed_function(first, second):
            return sqlite3.SQLITE_OK
        audit.denied = True
        return sqlite3.SQLITE_DENY

    connection.set_authorizer(authorize)


def install_sqlite_policy(connection: sqlite3.Connection) -> _PolicyEvidence:
    """Install controls on a trusted, prepared :memory: connection; expose no connection API."""
    try:
        _memory_only(connection)
        heap_bytes = _set_heap_limit(connection)
        extension_loader = getattr(connection, "enable_load_extension", None)
        if callable(extension_loader):
            with suppress(sqlite3.NotSupportedError):
                extension_loader(False)
        limits = _set_limits(connection)
        pragmas = tuple(
            (name, _set_pragma(connection, name, value))
            for name, value in (("trusted_schema", 0), ("temp_store", 2), ("query_only", 1))
        )
        audit = _Audit()
        _install_authorizer(connection, audit)
        try:
            started: float | None = time.monotonic()
        except (OSError, RuntimeError):
            started = None
        progress = _ProgressBudget(started)
        connection.set_progress_handler(progress, 100)
        return _PolicyEvidence(heap_bytes, pragmas, limits, audit, progress)
    except PolicyFailure:
        raise
    except (AttributeError, MemoryError, sqlite3.Error):
        raise PolicyFailure() from None
