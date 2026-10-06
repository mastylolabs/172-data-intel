"""Novel demo SQL and safe refusal cases against independently known fixture facts."""

import json
import sqlite3
from hashlib import sha256
from pathlib import Path
from typing import cast
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest

from data_intel._sales_context import _sales_context
from data_intel.contracts import SqlIntent
from data_intel.query_engine import QueryFailure, SQLiteQueryEngine
from data_intel.sales_demo import DEMO_FIELDS, DEMO_SOURCE
from data_intel.sales_fixture import SALES_SOURCE, FixtureError
from data_intel.sales_profile import profile_sales_demo
from data_intel.service_contracts import QueryServiceRequest, RuntimeInfo
from data_intel.service_routes import handle_service


def _intent(sql: str, max_rows: int = 20) -> SqlIntent:
    return SqlIntent(
        version="1", source=DEMO_SOURCE, question="Verify demo", sql=sql, max_rows=max_rows
    )


@pytest.mark.parametrize(
    "sql,expected",
    [
        (
            "SELECT count(sale_id), sum(units), sum(revenue_cents) FROM main.sales",
            (("24", "29", "395000"),),
        ),
        (
            "SELECT strftime('%Y-%m', sale_date), count(sale_id), sum(units), sum(revenue_cents) "
            "FROM sales GROUP BY 1 ORDER BY 1",
            (
                ("2026-01", "8", "7", "105000"),
                ("2026-02", "8", "12", "140000"),
                ("2026-03", "8", "10", "150000"),
            ),
        ),
        (
            "SELECT customer, sum(revenue_cents) AS cents FROM sales GROUP BY customer "
            "ORDER BY cents DESC, customer ASC",
            (
                ("Acme", "100000"),
                ("Cedar", "80000"),
                ("Bright", "75000"),
                ("Delta", "60000"),
                ("Elm", "40000"),
                ("Fjord", "40000"),
            ),
        ),
        (
            "WITH monthly AS (SELECT strftime('%Y-%m', sale_date) AS month, "
            "sum(revenue_cents) AS cents FROM sales GROUP BY 1) SELECT month, "
            "cents-lag(cents) OVER (ORDER BY month) FROM monthly ORDER BY month",
            (("2026-01", None), ("2026-02", "35000"), ("2026-03", "10000")),
        ),
        (
            "SELECT count(sale_id), sum(units), sum(revenue_cents) "
            "FROM sales WHERE revenue_cents<0",
            (("4", "-4", "-45000"),),
        ),
        (
            "SELECT sale_id FROM sales WHERE units=0 ORDER BY sale_id",
            (("D004",), ("D014",), ("D023",)),
        ),
        (
            "SELECT customer, sum(revenue_cents) FROM sales "
            "WHERE region='North' AND product='Plus' "
            "AND sale_date>='2026-03-01' AND sale_date<'2026-04-01' GROUP BY customer",
            (("Acme", "45000"),),
        ),
        (
            "SELECT sum(units), sum(revenue_cents) FROM sales WHERE sale_date>='2026-01-31' "
            "AND sale_date<'2026-02-01'",
            (("1", "15000"),),
        ),
        ("SELECT sum(units) FROM sales WHERE customer='Unknown'", ((None,),)),
    ],
)
def test_generic_demo_queries_match_independent_oracles(
    sql: str, expected: tuple[tuple[object, ...], ...]
) -> None:
    result = SQLiteQueryEngine(allow_demo_source=True).execute(_intent(sql, len(expected)))
    assert tuple(tuple(cell.value for cell in row) for row in result.content.rows) == expected
    assert (result.source, result.schema_revision) == (DEMO_SOURCE, "sales-demo.v1")
    assert (result.actual_sql, result.sql_sha256) == (sql, sha256(sql.encode()).hexdigest())
    assert result.content.content_sha256 == sha256(result.content.content_bytes).hexdigest()
    assert result.analytical_validated is False


@pytest.mark.parametrize(
    "sql,code",
    [
        ("SELECT FROM sales", "invalid_query"),
        ("SELECT 1", "unsafe_query"),
        ("UPDATE sales SET units=0", "unsafe_query"),
        ("SELECT * FROM sqlite_master", "unsafe_query"),
        ("WITH sales AS (VALUES(1)) SELECT count(*) FROM sales", "unsafe_query"),
        ("SELECT sale_id FROM sales ORDER BY sale_id", "result_limit"),
        ("SELECT sale_id AS x, customer AS x FROM sales LIMIT 1", "invalid_result"),
        ("SELECT 1e999 + units FROM sales LIMIT 1", "invalid_result"),
        (
            "SELECT sum(CASE WHEN sale_id='D001' THEN 9223372036854775807 ELSE 1 END) FROM sales",
            "invalid_result",
        ),
        (
            "SELECT count(sale_id) FROM main.sales CROSS JOIN (VALUES" + "(0)," * 1499 + "(0))",
            "execution_limit",
        ),
    ],
)
def test_demo_queries_refuse_without_partial_result_or_raw_diagnostics(sql: str, code: str) -> None:
    with pytest.raises(QueryFailure) as error:
        SQLiteQueryEngine(allow_demo_source=True).execute(_intent(sql))
    assert (error.value.code, str(error.value)) == (code, code)


def test_default_engine_refuses_demo_before_context_but_opt_in_preserves_proof() -> None:
    with (
        patch(
            "data_intel.query_engine._sales_context", side_effect=AssertionError("must not open")
        ),
        pytest.raises(QueryFailure, match=r"^unsupported_source$"),
    ):
        SQLiteQueryEngine().execute(_intent("SELECT sum(units) FROM sales"))
    proof = _intent("SELECT sum(units) FROM sales").model_copy(update={"source": SALES_SOURCE})
    result = SQLiteQueryEngine(allow_demo_source=True).execute(proof)
    assert (result.source, result.schema_revision, result.content.rows[0][0].value) == (
        SALES_SOURCE,
        "sales-proof.v1",
        "10",
    )
    assert profile_sales_demo().capabilities == ("query",)


@pytest.mark.parametrize(
    "change", [{"meaning_revision": "sales-demo.v2"}, {"snapshot_sha256": "f" * 64}]
)
def test_unknown_full_identity_fails_before_file_or_database_access(change: dict[str, str]) -> None:
    intent = _intent("SELECT count(sale_id) FROM sales").model_copy(
        update={"source": DEMO_SOURCE.model_copy(update=change)}
    )
    with (
        patch.object(Path, "open", side_effect=AssertionError("must not read")),
        patch(
            "data_intel._sales_context.sqlite3.connect",
            side_effect=AssertionError("must not connect"),
        ),
        pytest.raises(QueryFailure, match=r"^source_mismatch$"),
    ):
        SQLiteQueryEngine(allow_demo_source=True).execute(intent)


def test_demo_context_is_pinned_isolated_and_closed_after_exit() -> None:
    with _sales_context(DEMO_SOURCE) as demo, _sales_context(SALES_SOURCE) as proof:
        connection = demo._connection
        assert demo.fields == DEMO_FIELDS and demo.schema_revision == "sales-demo.v1"
        assert demo.profile.record_count == 24 and proof.profile.record_count == 6
        assert connection is not proof._connection
        assert connection.execute("SELECT count(*) FROM main.sales").fetchone() == (24,)
        with pytest.raises(sqlite3.DatabaseError):
            connection.execute("DELETE FROM sales")
    with pytest.raises(sqlite3.ProgrammingError, match="closed database"):
        connection.execute("SELECT 1")


def test_invalid_demo_bytes_map_safely_before_opening_database(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "data_intel._sales_context.load_sales_demo",
        Mock(side_effect=FixtureError("fixture_invalid")),
    )
    monkeypatch.setattr("data_intel._sales_context.sqlite3.connect", pytest.fail)
    with pytest.raises(QueryFailure, match=r"^runtime_incompatible$"):
        SQLiteQueryEngine(allow_demo_source=True).execute(_intent("SELECT sum(units) FROM sales"))


@pytest.mark.parametrize("option", ["false", 0, 1, None])
def test_opt_in_configuration_cannot_coerce_nonbooleans(option: object) -> None:
    with pytest.raises(QueryFailure, match=r"^invalid_input$"):
        SQLiteQueryEngine(allow_demo_source=cast("bool", option))


def test_explicit_twenty_row_scope_succeeds_but_column_and_byte_limits_refuse() -> None:
    engine = SQLiteQueryEngine(allow_demo_source=True)
    result = engine.execute(_intent("SELECT sale_id FROM main.sales ORDER BY sale_id LIMIT 20"))
    assert tuple(row[0].value for row in result.content.rows) == tuple(
        f"D{i:03}" for i in range(1, 21)
    )
    columns = ",".join(f"units AS c{i}" for i in range(17))
    large = ",".join(f"customer || '{'x' * 244}' AS c{i}" for i in range(16))
    for sql in (f"SELECT {columns} FROM sales LIMIT 1", f"SELECT {large} FROM sales LIMIT 8"):
        with pytest.raises(QueryFailure, match=r"^result_limit$"):
            engine.execute(_intent(sql))


def test_existing_v1_service_default_still_refuses_demo_and_reports_proof_metadata() -> None:
    runtime = RuntimeInfo(
        python_version="3.12",
        sqlite_version="3",
        runtime_mode="local",
        build_revision=None,
        worker_version_id=None,
    )
    request = QueryServiceRequest(
        version="1", job_id=uuid4(), intent=_intent("SELECT sum(units) FROM sales")
    )
    engine = SQLiteQueryEngine()
    status, body = handle_service(
        "POST", "/query", request.model_dump_json().encode(), runtime, engine
    )
    assert status == 422 and json.loads(body)["code"] == "unsupported_source"
    status, body = handle_service("GET", "/metadata", b"", runtime, engine)
    metadata = json.loads(body)
    assert status == 200 and metadata["source"] == SALES_SOURCE.model_dump(mode="json")
    assert (
        metadata["profile"]["record_count"] == 6 and metadata["schema_revision"] == "sales-proof.v1"
    )
