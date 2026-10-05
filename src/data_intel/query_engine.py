"""Private, source-bound SQLite execution for bounded sales queries."""

import re
import sqlite3
from dataclasses import dataclass
from hashlib import sha256
from typing import Literal, Protocol

from data_intel._bounded_result import (
    BoundedResultContent,
    ResultContentError,
    build_bounded_result,
)
from data_intel._sales_context import _sales_context, _SalesContext
from data_intel._sqlite_policy import PolicyFailure
from data_intel.contracts import SourceIdentity, SqlIntent
from data_intel.sales_fixture import SALES_SOURCE, FixtureError

QueryErrorCode = Literal[
    "invalid_input",
    "unsupported_source",
    "source_mismatch",
    "unsafe_query",
    "invalid_query",
    "execution_limit",
    "invalid_result",
    "result_limit",
    "runtime_incompatible",
]
_SELECT_PREFIX = re.compile(r"^\s*(?:SELECT|WITH)\b", re.IGNORECASE)


class QueryFailure(RuntimeError):
    """Stable execution classification without SQL, source, or SQLite details."""

    def __init__(self, code: QueryErrorCode) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class QueryExecutionResult:
    source: SourceIdentity
    schema_revision: str
    actual_sql: str
    sql_sha256: str
    content: BoundedResultContent
    analytical_validated: Literal[False] = False


class QueryEngine(Protocol):
    """Reusable synchronous boundary for untrusted SQL intents."""

    def execute(self, intent: SqlIntent) -> QueryExecutionResult: ...


def _sql_bytes(intent: SqlIntent) -> bytes:
    if type(intent.max_rows) is not int or not 1 <= intent.max_rows <= 20:
        raise QueryFailure("invalid_input")
    if type(intent.sql) is not str or not intent.sql.strip():
        raise QueryFailure("invalid_input")
    try:
        encoded = intent.sql.encode("utf-8")
    except UnicodeEncodeError:
        raise QueryFailure("invalid_input") from None
    if len(encoded) > 8_000:
        raise QueryFailure("invalid_input")
    if _SELECT_PREFIX.match(intent.sql) is None:
        raise QueryFailure("unsafe_query")
    return encoded


def _fixture_failure(error: FixtureError, source: SourceIdentity) -> QueryFailure:
    if error.code == "source_mismatch":
        code: QueryErrorCode = (
            "source_mismatch"
            if source.source_id == SALES_SOURCE.source_id
            else "unsupported_source"
        )
    else:
        code = "runtime_incompatible"
    return QueryFailure(code)


def _sqlite_failure(error: sqlite3.Error, context: _SalesContext) -> QueryFailure:
    if context._policy.progress.reason is not None:
        code: QueryErrorCode = "execution_limit"
    elif context._policy.audit.denied:
        code = "unsafe_query"
    elif "too many columns" in str(error).lower():
        code = "result_limit"
    elif "integer overflow" in str(error).lower():
        code = "invalid_result"
    else:
        code = "invalid_query"
    return QueryFailure(code)


def _execute_in_context(
    intent: SqlIntent, context: _SalesContext, sql_bytes: bytes
) -> QueryExecutionResult:
    before_reads = context._policy.audit.sales_reads
    try:
        cursor = context._connection.execute(intent.sql)
        if context._policy.audit.denied or context._policy.audit.sales_reads <= before_reads:
            raise QueryFailure("unsafe_query")
        if cursor.description is None:
            raise QueryFailure("invalid_query")
        columns = tuple(column[0] for column in cursor.description)
        content = build_bounded_result(columns, cursor, intent.max_rows)
    except QueryFailure:
        raise
    except ResultContentError as error:
        raise QueryFailure(error.code) from None
    except sqlite3.Error as error:
        raise _sqlite_failure(error, context) from None
    except MemoryError:
        raise QueryFailure("execution_limit") from None
    except OverflowError:
        raise QueryFailure("invalid_result") from None
    return QueryExecutionResult(
        source=context.source,
        schema_revision=context.schema_revision,
        actual_sql=intent.sql,
        sql_sha256=sha256(sql_bytes).hexdigest(),
        content=content,
    )


class SQLiteQueryEngine:
    """Run one intent per fresh, verified, policy-controlled SQLite context."""

    def execute(self, intent: SqlIntent) -> QueryExecutionResult:
        encoded_sql = _sql_bytes(intent)
        try:
            with _sales_context(intent.source) as context:
                result = _execute_in_context(intent, context, encoded_sql)
        except FixtureError as error:
            raise _fixture_failure(error, intent.source) from None
        except PolicyFailure:
            raise QueryFailure("runtime_incompatible") from None
        return result
