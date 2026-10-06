"""Registry identity, capability and byte-bound tests for CatalogV2."""

import json

import pytest
from pydantic import ValidationError

from data_intel.catalog_v2 import CatalogEntryV2, CatalogV2, registered_catalog
from data_intel.sales_demo import DEMO_SOURCE
from data_intel.support_demo import SUPPORT_SOURCE


def _entry(source: object = DEMO_SOURCE) -> CatalogEntryV2:
    if source == DEMO_SOURCE:
        return CatalogEntryV2(
            source=DEMO_SOURCE,
            schema_revision="sales-demo.v1",
            profile_revision="m3-profile.v1",
            kind="structured",
            display_name="Sales demo",
            description="Synthetic net sales lines for bounded structured analysis.",
            capability_help=(
                ("profile", "Summarize fields and bounded statistics."),
                ("query", "Ask for read-only totals, groups, rankings or period comparisons."),
            ),
            capabilities=("profile", "query"),
            record_count=24,
            manifest_bytes=1025,
            scope="complete_immutable_fixture",
        )
    return CatalogEntryV2(
        source=SUPPORT_SOURCE,
        schema_revision="support-demo.v1",
        profile_revision=None,
        kind="messages",
        display_name="Support messages",
        description="Synthetic support messages for targeted lexical examples.",
        capability_help=(
            (
                "search",
                "Find matching messages with exact IDs and source quotes; "
                "hits do not establish prevalence.",
            ),
        ),
        capabilities=("search",),
        record_count=16,
        manifest_bytes=3091,
        scope="complete_immutable_fixture",
    )


def test_registered_catalog_round_trips_and_is_bounded() -> None:
    catalog = registered_catalog()
    restored = CatalogV2.model_validate_json(catalog.model_dump_json())
    assert restored == catalog
    assert {entry.source.source_id for entry in catalog.entries} == {"sales", "support"}
    assert len(catalog.model_dump_json().encode()) <= 4096


@pytest.mark.parametrize(
    "field,value",
    [("version", "1"), ("catalog_revision", "other"), ("entries", [])],
)
def test_catalog_rejects_wrong_version_revision_and_empty_registry(
    field: str, value: object
) -> None:
    data = registered_catalog().model_dump(mode="json")
    data[field] = value
    with pytest.raises(ValidationError):
        CatalogV2.model_validate(data)


def test_catalog_rejects_duplicate_or_unregistered_sources() -> None:
    entry = _entry()
    with pytest.raises(ValidationError, match="unsupported_source"):
        CatalogV2(version="2", catalog_revision="m4-catalog.v1", entries=(entry, entry))
    fake_source = DEMO_SOURCE.model_copy(update={"snapshot_sha256": "0" * 64})
    wrong = entry.model_copy(update={"source": fake_source})
    with pytest.raises(ValidationError, match=r"source_mismatch"):
        CatalogV2(
            version="2",
            catalog_revision="m4-catalog.v1",
            entries=(wrong, _entry(SUPPORT_SOURCE)),
        )


def test_entry_rejects_capability_and_utf8_mismatches() -> None:
    with pytest.raises(ValidationError, match="capability_mismatch"):
        CatalogEntryV2(
            **(
                _entry().model_dump(mode="json")
                | {"capabilities": ["search"], "capability_help": {"search": "wrong"}}
            )
        )
    with pytest.raises(ValidationError, match="invalid_input"):
        CatalogEntryV2.model_validate(_entry().model_dump(mode="json") | {"description": "é" * 81})
    with pytest.raises(ValidationError, match="invalid_input"):
        CatalogEntryV2.model_validate(
            _entry().model_dump(mode="json") | {"description": "bad\ud800"}
        )
    with pytest.raises(ValidationError, match="invalid_input"):
        CatalogEntryV2.model_validate(
            _entry().model_dump(mode="json")
            | {"capability_help": {"profile": "x" * 181, "query": "q"}}
        )


def test_catalog_rejects_fabricated_manifest_and_unknown_fields() -> None:
    data = registered_catalog().model_dump(mode="json")
    data["entries"][0]["manifest_bytes"] = 1026
    with pytest.raises(ValidationError, match="source_mismatch"):
        CatalogV2.model_validate(data)
    with pytest.raises(ValidationError, match="extra_forbidden"):
        CatalogV2.model_validate(
            registered_catalog().model_dump(mode="json") | {"path": "/tmp/sales.csv"}
        )
    assert json.loads(registered_catalog().model_dump_json())["catalog_revision"] == "m4-catalog.v1"


def test_registered_catalog_nested_values_are_immutable() -> None:
    catalog = registered_catalog()
    append_name = "append"
    with pytest.raises(AttributeError, match="append"):
        getattr(catalog.entries[0].capabilities, append_name)("search")
    with pytest.raises(ValidationError):
        catalog.entries[0].capability_help = (("query", "fabricated"),)
    clear_name = "clear"
    with pytest.raises(AttributeError, match="clear"):
        getattr(catalog.entries, clear_name)()
