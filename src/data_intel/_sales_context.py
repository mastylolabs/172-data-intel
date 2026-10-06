"""Private, verified sales fixture context for later trusted query code."""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass

from data_intel._sqlite_policy import PolicyFailure, _PolicyEvidence, install_sqlite_policy
from data_intel.contracts import SourceIdentity
from data_intel.sales_demo import DEMO_SOURCE, load_sales_demo
from data_intel.sales_fixture import (
    FieldMeaning,
    SaleRow,
    SalesFixture,
    SalesProfile,
    load_sales_fixture,
)


@dataclass(frozen=True, slots=True)
class _SalesContext:
    """Verified metadata and a private connection owned by the context manager."""

    source: SourceIdentity
    schema_revision: str
    fields: tuple[FieldMeaning, ...]
    profile: SalesProfile
    _connection: sqlite3.Connection
    _policy: _PolicyEvidence


def _populate_sales(connection: sqlite3.Connection, rows: tuple[SaleRow, ...]) -> None:
    connection.execute(
        "CREATE TABLE sales (sale_id TEXT NOT NULL UNIQUE, sale_date TEXT NOT NULL, "
        "customer TEXT NOT NULL, region TEXT NOT NULL, product TEXT NOT NULL, "
        "units INTEGER NOT NULL, revenue_cents INTEGER NOT NULL)"
    )
    connection.executemany(
        "INSERT INTO sales (sale_id, sale_date, customer, region, product, units, "
        "revenue_cents) VALUES (?, ?, ?, ?, ?, ?, ?)",
        tuple(
            (
                row.sale_id,
                row.sale_date.isoformat(),
                row.customer,
                row.region,
                row.product,
                row.units,
                row.revenue_cents,
            )
            for row in rows
        ),
    )
    connection.commit()


def _verified_sales_fixture(expected_source: SourceIdentity) -> SalesFixture:
    """Select a complete server-owned identity before either loader reads its path."""
    if expected_source != DEMO_SOURCE:
        return load_sales_fixture(expected_source)
    demo = load_sales_demo(expected_source)
    dates = tuple(row.sale_date for row in demo.rows)
    return SalesFixture(
        source=demo.source,
        rows=demo.rows,
        fields=demo.fields,
        schema_revision=demo.schema_revision,
        profile=SalesProfile(record_count=len(demo.rows), date_min=min(dates), date_max=max(dates)),
    )


@contextmanager
def _sales_context(expected_source: SourceIdentity) -> Iterator[_SalesContext]:
    """Load only the verified sales fixture, install policy, then always close."""
    fixture = _verified_sales_fixture(expected_source)
    try:
        connection = sqlite3.connect(":memory:")
    except (MemoryError, sqlite3.Error):
        raise PolicyFailure() from None
    try:
        try:
            _populate_sales(connection, fixture.rows)
        except (MemoryError, sqlite3.Error):
            raise PolicyFailure() from None
        policy = install_sqlite_policy(connection)
        yield _SalesContext(
            source=fixture.source,
            schema_revision=fixture.schema_revision,
            fields=fixture.fields,
            profile=fixture.profile,
            _connection=connection,
            _policy=policy,
        )
    finally:
        connection.close()
