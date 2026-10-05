"""Real SQLite acceptance cases for the private query-engine boundary."""

import sqlite3
from hashlib import sha256
from unittest.mock import Mock

import pytest

import data_intel.query_engine as query_engine
from data_intel._sales_context import _sales_context
from data_intel._sqlite_policy import PolicyFailure
from data_intel.contracts import SourceId, SourceIdentity, SqlIntent
from data_intel.query_engine import QueryExecutionResult, QueryFailure, SQLiteQueryEngine
from data_intel.sales_fixture import SALES_SOURCE

_BUSY_SQL = f"SELECT count(sale_id) FROM main.sales CROSS JOIN (VALUES{'(0),' * 1_499}(0))"


def _intent(sql: str, max_rows: int = 20, source: SourceIdentity = SALES_SOURCE) -> SqlIntent:
    return SqlIntent(
        version="1", source=source, question="Verify fixture math", sql=sql, max_rows=max_rows
    )


def _values(result: QueryExecutionResult) -> tuple[tuple[object, ...], ...]:
    return tuple(tuple(cell.value for cell in row) for row in result.content.rows)


def _assert_failure(intent: SqlIntent | str, code: str, max_rows: int = 20) -> None:
    proposal = _intent(intent, max_rows) if isinstance(intent, str) else intent
    with pytest.raises(QueryFailure) as error:
        SQLiteQueryEngine().execute(proposal)
    assert (error.value.code, str(error.value)) == (code, code)


@pytest.mark.parametrize(
    ("sql", "max_rows", "failure_code"),
    [
        ("SELECT sum(units) FROM sales", 20, None),
        ("SELECT FROM sales", 20, "invalid_query"),
        ("SELECT sale_id FROM sales ORDER BY sale_id", 5, "result_limit"),
        (
            "SELECT CASE WHEN units >= 0 THEN X'00' ELSE X'01' END FROM sales LIMIT 1",
            20,
            "invalid_result",
        ),
    ],
)
def test_owned_connection_closes_after_every_execution_outcome(
    sql: str, max_rows: int, failure_code: str | None, monkeypatch: pytest.MonkeyPatch
) -> None:
    original_connect = sqlite3.connect
    opened: list[sqlite3.Connection] = []

    def track(database: str) -> sqlite3.Connection:
        assert database == ":memory:"
        connection = original_connect(database)
        opened.append(connection)
        return connection

    monkeypatch.setattr("data_intel._sales_context.sqlite3.connect", track)
    if failure_code is None:
        result = SQLiteQueryEngine().execute(_intent(sql, max_rows))
        assert _values(result) == (("10",),)
    else:
        _assert_failure(_intent(sql, max_rows), failure_code)
    assert len(opened) == 1
    with pytest.raises(sqlite3.ProgrammingError, match="closed database"):
        opened[0].execute("SELECT 1")


@pytest.mark.parametrize(
    ("sql", "expected"),
    [
        (
            "SELECT sum(revenue_cents), sum(units), count(sale_id) FROM sales",
            (("130000", "10", "6"),),
        ),
        ("SELECT count(*) FROM main.sales", (("6",),)),
        (
            "SELECT strftime('%Y-%m', sale_date), sum(revenue_cents), sum(units) "
            "FROM sales GROUP BY 1 ORDER BY 1",
            (("2026-01", "60000", "4"), ("2026-02", "70000", "6")),
        ),
        (
            "WITH monthly AS (SELECT strftime('%Y-%m', sale_date) AS period, "
            "sum(revenue_cents) AS cents FROM sales GROUP BY 1) "
            "SELECT max(CASE WHEN period='2026-02' THEN cents END)-"
            "max(CASE WHEN period='2026-01' THEN cents END) AS cents_difference FROM monthly",
            (("10000",),),
        ),
        (
            "SELECT customer, sum(revenue_cents) AS cents FROM sales GROUP BY customer "
            "ORDER BY cents DESC, customer ASC",
            (("Bright", "75000"), ("Acme", "55000"), ("Cedar", "0")),
        ),
        (
            "SELECT sum(revenue_cents), sum(units), count(sale_id) FROM sales WHERE product='Core'",
            (("105000", "9", "4"),),
        ),
        (
            "SELECT region, product, sum(revenue_cents) FROM sales GROUP BY region, product "
            "ORDER BY region, product",
            (
                ("East", "Core", "0"),
                ("North", "Core", "60000"),
                ("North", "Plus", "-5000"),
                ("South", "Core", "45000"),
                ("South", "Plus", "30000"),
            ),
        ),
    ],
)
def test_generic_sql_matches_independent_fixture_oracles(
    sql: str, expected: tuple[tuple[object, ...], ...]
) -> None:
    engine = SQLiteQueryEngine()
    result = engine.execute(_intent(sql, len(expected)))
    assert _values(result) == expected
    assert (result.source, result.schema_revision) == (SALES_SOURCE, "sales-proof.v1")
    assert (result.actual_sql, result.sql_sha256) == (sql, sha256(sql.encode("utf-8")).hexdigest())
    assert result.analytical_validated is False
    with pytest.raises(QueryFailure, match="unsafe_query"):
        engine.execute(_intent("SELECT 1"))


@pytest.mark.parametrize(
    ("source", "code"),
    [
        (SALES_SOURCE.model_copy(update={"snapshot_sha256": "0" * 64}), "source_mismatch"),
        (
            SourceIdentity(
                version="1",
                source_id=SourceId.SUPPORT,
                snapshot_sha256="1" * 64,
                meaning_revision="support-proof.v1",
            ),
            "unsupported_source",
        ),
    ],
)
def test_loader_authorizes_exact_source_before_database_open(
    source: SourceIdentity, code: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("data_intel._sales_context.sqlite3.connect", pytest.fail)
    _assert_failure(_intent("SELECT sum(units) FROM sales", source=source), code)


def test_policy_failure_maps_safely_before_sql_dispatch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("data_intel.query_engine._sales_context", Mock(side_effect=PolicyFailure()))
    monkeypatch.setattr("data_intel.query_engine._execute_in_context", pytest.fail)
    _assert_failure(_intent("SELECT sum(units) FROM sales"), "runtime_incompatible")


def test_sqlite_nomem_maps_safely_and_missing_codes_remain_safe() -> None:
    with _sales_context(SALES_SOURCE) as context:
        error = sqlite3.OperationalError("private memory diagnostic")
        error.sqlite_errorcode = sqlite3.SQLITE_NOMEM | 1 << 8
        failure = query_engine._sqlite_failure(error, context)
        assert (failure.code, str(failure)) == ("execution_limit", "execution_limit")
        missing = sqlite3.ProgrammingError("private sqlite diagnostic")
        failure = query_engine._sqlite_failure(missing, context)
        assert (failure.code, str(failure)) == ("invalid_query", "invalid_query")


@pytest.mark.parametrize(
    ("sql", "max_rows"),
    [
        ("-- leading comment\nSELECT sum(units) FROM sales", 20),
        ("", 20),
        ("SELECT 1", 21),
        ("SELECT '" + "é" * 4_000 + "'", 20),
    ],
)
def test_invalid_intents_fail_before_database_open(
    sql: str, max_rows: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    intent = (
        SqlIntent.model_construct(
            version="1", source=SALES_SOURCE, question="x", sql="", max_rows=max_rows
        )
        if not sql
        else _intent(sql, max_rows)
    )
    monkeypatch.setattr("data_intel.query_engine._sales_context", pytest.fail)
    expected = "invalid_input" if not sql or max_rows > 20 or "é" in sql else "unsafe_query"
    _assert_failure(intent, expected)


@pytest.mark.parametrize(
    ("sql", "code"),
    [
        ("UPDATE sales SET units=0", "unsafe_query"),
        ("CREATE TABLE x (id INTEGER)", "unsafe_query"),
        ("PRAGMA query_only=0", "unsafe_query"),
        ("ATTACH DATABASE ':memory:' AS other", "unsafe_query"),
        ("SELECT * FROM temp.sales", "invalid_query"),
        ("SELECT * FROM sqlite_master", "unsafe_query"),
        ("SELECT load_extension('x') FROM sales", "unsafe_query"),
        ("SELECT missing_function(customer) FROM sales", "invalid_query"),
        (
            "WITH RECURSIVE n(x) AS (VALUES(1) UNION ALL SELECT x+1 FROM n) SELECT sum(x) FROM n",
            "unsafe_query",
        ),
    ],
)
def test_unsafe_sql_is_refused_without_leaking_input(sql: str, code: str) -> None:
    _assert_failure(sql, code)


@pytest.mark.parametrize(
    ("sql", "code"),
    [
        ("WITH sales AS (VALUES(1),(2),(3)) SELECT 42, count(*) FROM sales", "unsafe_query"),
        ("SELECT customer FROM sales; SELECT units FROM sales", "invalid_query"),
        ("SELECT FROM sales", "invalid_query"),
        ("SELECT sale_id FROM sales WHERE", "invalid_query"),
        ("SELECT 1", "unsafe_query"),
    ],
)
def test_invalid_or_readless_sql_is_refused(sql: str, code: str) -> None:
    _assert_failure(sql, code)


@pytest.mark.parametrize(
    ("sql", "max_rows", "code"),
    [
        ("SELECT sale_id FROM sales ORDER BY sale_id", 5, "result_limit"),
        ("SELECT sale_id AS x, customer AS x FROM sales LIMIT 1", 20, "invalid_result"),
        (f'SELECT sale_id AS "{"x" * 65}" FROM sales LIMIT 1', 20, "result_limit"),
        (
            f"SELECT customer || '{'x' * 253}' FROM sales LIMIT 1",
            20,
            "result_limit",
        ),
        (
            "SELECT CASE WHEN units >= 0 THEN X'00' ELSE X'01' END FROM sales LIMIT 1",
            20,
            "invalid_result",
        ),
        ("SELECT 1e999 + units FROM sales LIMIT 1", 20, "invalid_result"),
        (
            "SELECT sum(CASE WHEN sale_id='S001' THEN 9223372036854775807 ELSE 1 END) FROM sales",
            20,
            "invalid_result",
        ),
        (_BUSY_SQL, 1, "execution_limit"),
    ],
)
def test_result_and_execution_boundaries_refuse_without_partial_result(
    sql: str, max_rows: int, code: str
) -> None:
    _assert_failure(sql, code, max_rows)


def test_result_byte_bound_is_enforced_for_complete_result() -> None:
    columns = ", ".join(f"customer || '{'x' * 244}' AS c{i}" for i in range(16))
    _assert_failure(f"SELECT {columns} FROM sales ORDER BY sale_id", "result_limit", 6)


def test_more_than_sixteen_result_columns_is_refused() -> None:
    columns = ", ".join(f"units AS c{i}" for i in range(17))
    _assert_failure(f"SELECT {columns} FROM sales LIMIT 1", "result_limit")
