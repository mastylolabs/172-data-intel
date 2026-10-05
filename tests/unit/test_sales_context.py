"""Source-bound SQLite context ownership, provenance and failure behavior."""

import sqlite3
from collections.abc import Iterator
from datetime import date
from functools import partial

import pytest

from data_intel._sales_context import _populate_sales, _SalesContext
from data_intel._sales_context import _sales_context as _loader
from data_intel._sqlite_policy import (
    PolicyFailure,
    _PolicyEvidence,
    install_sqlite_policy,
)
from data_intel.sales_fixture import (
    SALES_FIELDS,
    SALES_REVISION,
    SALES_SOURCE,
    FixtureError,
    SaleRow,
)

_sales_context = partial(_loader, SALES_SOURCE)


@pytest.fixture
def context() -> Iterator[_SalesContext]:
    with _sales_context() as result:
        yield result


def test_context_loads_exact_verified_rows_and_metadata(context: _SalesContext) -> None:
    rows = context._connection.execute(
        "SELECT sale_id, sale_date, customer, region, product, units, revenue_cents "
        "FROM sales ORDER BY sale_id"
    ).fetchall()
    assert rows == [
        ("S001", "2026-01-02", "Acme", "North", "Core", 2, 20000),
        ("S002", "2026-01-14", "Bright", "South", "Core", 3, 45000),
        ("S003", "2026-01-31", "Acme", "North", "Plus", -1, -5000),
        ("S004", "2026-02-01", "Acme", "North", "Core", 4, 40000),
        ("S005", "2026-02-15", "Bright", "South", "Plus", 2, 30000),
        ("S006", "2026-02-28", "Cedar", "East", "Core", 0, 0),
    ]
    assert context.source == SALES_SOURCE
    assert context.schema_revision == SALES_REVISION
    assert context.fields == SALES_FIELDS
    assert (context.profile.record_count, context.profile.date_min, context.profile.date_max) == (
        6,
        date(2026, 1, 2),
        date(2026, 2, 28),
    )


def test_real_sql_totals_match_independent_fixture_oracles(context: _SalesContext) -> None:
    connection = context._connection
    assert connection.execute("SELECT sum(revenue_cents) FROM sales").fetchone() == (130000,)
    actual = connection.execute(
        "SELECT strftime('%Y-%m', sale_date), sum(revenue_cents) FROM sales "
        "GROUP BY strftime('%Y-%m', sale_date) ORDER BY 1"
    ).fetchall()
    assert actual == [
        ("2026-01", 60000),
        ("2026-02", 70000),
    ]


def test_each_context_owns_a_fresh_isolated_database() -> None:
    with _sales_context() as first, _sales_context() as second:
        assert first._connection is not second._connection
        for context in (first, second):
            assert context._connection.execute("SELECT count(*) FROM sales").fetchone() == (6,)


def test_policy_is_installed_after_fixture_setup(monkeypatch: pytest.MonkeyPatch) -> None:
    original_populate = _populate_sales
    original_install = install_sqlite_policy
    events: list[str] = []

    def populate(connection: sqlite3.Connection, rows: tuple[SaleRow, ...]) -> None:
        original_populate(connection, rows)
        events.append("loaded")

    def install(connection: sqlite3.Connection) -> _PolicyEvidence:
        assert events == ["loaded"]
        events.append("policy")
        return original_install(connection)

    monkeypatch.setattr("data_intel._sales_context._populate_sales", populate)
    monkeypatch.setattr("data_intel._sales_context.install_sqlite_policy", install)
    with _sales_context():
        pass
    assert events == ["loaded", "policy"]


def test_installed_policy_denies_writes_and_preserves_fixture_rows(context: _SalesContext) -> None:
    with pytest.raises(sqlite3.DatabaseError):
        context._connection.execute("UPDATE sales SET units=99 WHERE sale_id='S001'")
    assert context._connection.execute(
        "SELECT units FROM sales WHERE sale_id='S001'"
    ).fetchone() == (2,)


def test_successful_exit_closes_owned_connection() -> None:
    with _sales_context() as context:
        connection = context._connection
    with pytest.raises(sqlite3.ProgrammingError, match="closed database"):
        connection.execute("SELECT count(*) FROM sales")


def test_loader_failure_opens_no_database_or_yields_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_loader(_requested: object = None) -> None:
        raise FixtureError("fixture_invalid")

    monkeypatch.setattr("data_intel._sales_context.load_sales_fixture", fail_loader)
    monkeypatch.setattr("data_intel._sales_context.sqlite3.connect", pytest.fail)
    yielded: list[bool] = []
    with pytest.raises(FixtureError), _sales_context():
        yielded.append(True)
    assert not yielded


@pytest.mark.parametrize(
    "failure",
    [sqlite3.OperationalError("setup failed"), MemoryError("setup exhausted")],
)
def test_setup_failure_is_safe_and_never_yields(
    failure: Exception,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_connect = sqlite3.connect
    opened: list[sqlite3.Connection] = []

    def track_connect(database: str) -> sqlite3.Connection:
        assert database == ":memory:"
        connection = original_connect(database)
        opened.append(connection)
        return connection

    def fail_setup(connection: sqlite3.Connection, rows: tuple[SaleRow, ...]) -> None:
        del connection, rows
        raise failure

    monkeypatch.setattr("data_intel._sales_context.sqlite3.connect", track_connect)
    monkeypatch.setattr("data_intel._sales_context._populate_sales", fail_setup)
    monkeypatch.setattr("data_intel._sales_context.install_sqlite_policy", pytest.fail)
    with pytest.raises(PolicyFailure, match=r"^runtime_incompatible$") as error, _sales_context():
        pytest.fail("context yielded after setup failure")
    assert error.value.code == "runtime_incompatible"
    assert str(failure) not in str(error.value)
    assert len(opened) == 1
    with pytest.raises(sqlite3.ProgrammingError, match="closed database"):
        opened[0].execute("SELECT 1")


def test_connection_creation_failure_is_safe_and_never_yields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_connect(database: str) -> sqlite3.Connection:
        assert database == ":memory:"
        raise sqlite3.OperationalError("private connection detail")

    monkeypatch.setattr("data_intel._sales_context.sqlite3.connect", fail_connect)
    with pytest.raises(PolicyFailure, match=r"^runtime_incompatible$") as error, _sales_context():
        pytest.fail("context yielded after connection failure")
    assert "private connection detail" not in str(error.value)


def test_policy_failure_closes_connection_and_does_not_yield(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_connect = sqlite3.connect
    opened: list[sqlite3.Connection] = []

    def track_connect(database: str) -> sqlite3.Connection:
        assert database == ":memory:"
        connection = original_connect(database)
        opened.append(connection)
        return connection

    def fail_policy(connection: sqlite3.Connection) -> None:
        del connection
        raise PolicyFailure()

    monkeypatch.setattr("data_intel._sales_context.sqlite3.connect", track_connect)
    monkeypatch.setattr("data_intel._sales_context.install_sqlite_policy", fail_policy)
    with pytest.raises(PolicyFailure), _sales_context():
        pytest.fail("context yielded after policy failure")
    assert len(opened) == 1
    with pytest.raises(sqlite3.ProgrammingError, match="closed database"):
        opened[0].execute("SELECT 1")


def test_use_failure_closes_connection() -> None:
    with (
        pytest.raises(sqlite3.OperationalError, match="incomplete input"),
        _sales_context() as context,
    ):
        connection = context._connection
        connection.execute("SELECT * FROM sales WHERE")
    with pytest.raises(sqlite3.ProgrammingError, match="closed database"):
        connection.execute("SELECT count(*) FROM sales")
