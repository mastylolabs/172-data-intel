"""Exercise policy hooks with a test-owned SQLite connection and synthetic sales rows."""

import sqlite3
from pathlib import Path
from typing import cast

import pytest

from data_intel._sqlite_policy import PolicyFailure, install_sqlite_policy

_BUSY_SQL = f"SELECT count(sale_id) FROM main.sales CROSS JOIN (VALUES{'(0),' * 1_499}(0))"


def _sales_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.execute(
        "CREATE TABLE sales (sale_id TEXT NOT NULL UNIQUE, sale_date TEXT NOT NULL, "
        "customer TEXT NOT NULL, region TEXT NOT NULL, product TEXT NOT NULL, "
        "units INTEGER NOT NULL, revenue_cents INTEGER NOT NULL)"
    )
    connection.execute("CREATE TABLE forbidden (payload TEXT)")
    connection.executemany(
        "INSERT INTO sales VALUES (?, ?, ?, ?, ?, ?, ?)",
        tuple(
            (f"T{i}", f"2026-01-{i:02d}", "Acme", "North", "Core", i, i * 100) for i in range(1, 7)
        ),
    )
    return connection


@pytest.fixture
def connection(request: pytest.FixtureRequest) -> sqlite3.Connection:
    database = _sales_connection()
    request.addfinalizer(database.close)
    return database


def test_installer_verifies_exact_effective_controls(connection: sqlite3.Connection) -> None:
    evidence = install_sqlite_policy(connection)
    assert 0 < evidence.heap_bytes <= 8_388_608
    assert dict(evidence.pragmas) == {"trusted_schema": 0, "temp_store": 2, "query_only": 1}
    assert dict(evidence.limits) == {
        "sql_length": 8_000,
        "length": 65_536,
        "column": 16,
        "expr_depth": 30,
        "compound_select": 8,
        "vdbe_op": 10_000,
        "function_arg": 8,
        "attached": 0,
        "like_pattern_length": 128,
        "variable_number": 0,
        "trigger_depth": 0,
    }
    assert connection.execute("SELECT count(*) FROM main.sales").fetchone() == (6,)
    assert evidence.audit.sales_reads > 0 and not evidence.audit.denied


def test_installer_rejects_file_backed_connections_without_disclosing_path(tmp_path: Path) -> None:
    path = tmp_path / "not-memory.sqlite"
    connection = sqlite3.connect(path)
    try:
        with pytest.raises(PolicyFailure, match=r"^runtime_incompatible$") as error:
            install_sqlite_policy(connection)
        assert str(path) not in str(error.value)
    finally:
        connection.close()


def test_sales_read_and_every_declared_function_family_are_allowed(
    connection: sqlite3.Connection,
) -> None:
    evidence = install_sqlite_policy(connection)
    connection.execute(
        "SELECT sum(units), count(*), min(units), max(units), avg(units), abs(min(units)), "
        "round(avg(units)), coalesce(nullif(min(units), 99), 0), lower(min(customer)), "
        "upper(max(customer)), length(max(customer)), substr(min(customer), 1, 1), "
        "min(customer) LIKE 'A%', strftime('%Y', min(sale_date)) FROM sales"
    ).fetchone()
    connection.execute(
        "SELECT row_number() OVER (ORDER BY sale_id), rank() OVER (ORDER BY sale_id), "
        "dense_rank() OVER (ORDER BY sale_id), lag(units) OVER (ORDER BY sale_id), "
        "lead(units) OVER (ORDER BY sale_id) FROM sales"
    ).fetchall()
    assert evidence.audit.sales_reads > 0 and not evidence.audit.denied


@pytest.mark.parametrize(
    "sql",
    [
        "INSERT INTO sales VALUES ('X', '2026-01-01', 'A', 'N', 'Core', 1, 1)",
        "UPDATE sales SET units=0",
        "DELETE FROM sales",
        "CREATE TABLE other (id INTEGER)",
        "DROP TABLE sales",
        "CREATE TEMP TABLE other (id INTEGER)",
        "PRAGMA query_only",
        "ATTACH DATABASE ':memory:' AS other",
        "DETACH DATABASE main",
        "SELECT name FROM sqlite_master",
        "SELECT name FROM sqlite_schema",
        "SELECT name FROM temp.sqlite_master",
        "SELECT name FROM temp.sqlite_temp_master",
        "SELECT random() FROM sales",
        "SELECT load_extension('unsafe') FROM sales",
        "WITH RECURSIVE n(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM n WHERE x<2) SELECT x FROM n",
        "SELECT payload FROM forbidden",
    ],
)
def test_authorizer_denies_write_schema_temp_recursive_and_unknown_actions(
    sql: str,
    connection: sqlite3.Connection,
) -> None:
    evidence = install_sqlite_policy(connection)
    with pytest.raises(sqlite3.DatabaseError):
        connection.execute(sql)
    assert evidence.audit.denied


def test_vm_counter_interrupts_at_the_500th_100_step_callback(
    monkeypatch: pytest.MonkeyPatch,
    connection: sqlite3.Connection,
) -> None:
    monkeypatch.setattr("data_intel._sqlite_policy.time.monotonic", lambda: 1.0)
    evidence = install_sqlite_policy(connection)
    with pytest.raises(sqlite3.OperationalError):
        connection.execute(_BUSY_SQL)
    assert evidence.progress.callbacks == 500 and evidence.progress.reason == "vm"


@pytest.mark.parametrize(
    ("readings", "callbacks"),
    [((10.0, 10.250), 1), ((None, 10.0, 10.250), 2)],
)
def test_measurable_deadline_interrupts_after_250ms(
    monkeypatch: pytest.MonkeyPatch,
    connection: sqlite3.Connection,
    readings: tuple[float | None, ...],
    callbacks: int,
) -> None:
    clock_readings = iter(readings)

    def clock() -> float:
        value = next(clock_readings)
        if value is None:
            raise OSError("clock unavailable")
        return value

    monkeypatch.setattr("data_intel._sqlite_policy.time.monotonic", clock)
    evidence = install_sqlite_policy(connection)
    with pytest.raises(sqlite3.OperationalError):
        connection.execute(_BUSY_SQL)
    assert evidence.progress.callbacks == callbacks and evidence.progress.reason == "time"


class _ConnectionProxy:
    def __init__(self, connection: sqlite3.Connection, missing: str | None = None) -> None:
        self.inner = connection
        self.missing = missing

    def __getattr__(self, name: str) -> object:
        if name == self.missing:
            raise AttributeError(name)
        if name == "setlimit" and self.missing == "ineffective_limit":
            return self._ignore_sql_length
        return getattr(self.inner, name)

    def execute(self, sql: str) -> sqlite3.Cursor:
        if sql == self.missing:
            raise sqlite3.OperationalError("sensitive sqlite diagnostic")
        return self.inner.execute(sql)

    def _ignore_sql_length(self, category: int, limit: int) -> int:
        if category == sqlite3.SQLITE_LIMIT_SQL_LENGTH:
            return self.inner.getlimit(category)
        return self.inner.setlimit(category, limit)


@pytest.mark.parametrize(
    "missing",
    [
        "setlimit",
        "getlimit",
        "set_authorizer",
        "set_progress_handler",
        "ineffective_limit",
    ],
)
def test_connection_control_failure_fails_closed_without_raw_detail(
    missing: str,
    connection: sqlite3.Connection,
) -> None:
    proxy = cast(sqlite3.Connection, _ConnectionProxy(connection, missing))
    with pytest.raises(PolicyFailure, match=r"^runtime_incompatible$") as error:
        install_sqlite_policy(proxy)
    assert "sensitive" not in str(error.value)


@pytest.mark.parametrize(
    "setter",
    [
        "PRAGMA hard_heap_limit=8388608",
        "PRAGMA trusted_schema=0",
        "PRAGMA temp_store=2",
        "PRAGMA query_only=1",
    ],
)
def test_hard_heap_memory_and_ineffective_pragmas_fail_closed(
    setter: str,
    connection: sqlite3.Connection,
) -> None:
    class IgnoredPragma(_ConnectionProxy):
        def execute(self, sql: str) -> sqlite3.Cursor:
            if sql == setter and "hard_heap_limit" in sql:
                raise MemoryError
            if sql == setter:
                return self.inner.execute("SELECT 0")
            return self.inner.execute(sql)

    with pytest.raises(PolicyFailure, match=r"^runtime_incompatible$"):
        install_sqlite_policy(cast(sqlite3.Connection, IgnoredPragma(connection)))
