"""Strict registry contract for the two approved synthetic MVP sources."""

from typing import Literal

from pydantic import Field, field_validator, model_validator

from data_intel.contracts import SourceId, SourceIdentity
from data_intel.sales_demo import DEMO_SOURCE
from data_intel.service_v2_contracts import V2StrictModel, canonical_json
from data_intel.support_demo import SUPPORT_SOURCE

CatalogRevision = Literal["m4-catalog.v1"]
CatalogCapability = Literal["profile", "query", "search"]
CatalogKind = Literal["structured", "messages"]
CatalogScope = Literal["complete_immutable_fixture"]


class CatalogEntryV2(V2StrictModel):
    source: SourceIdentity
    schema_revision: str = Field(min_length=1, max_length=64)
    profile_revision: str | None = Field(max_length=64)
    kind: CatalogKind
    display_name: str = Field(min_length=1, max_length=64)
    description: str = Field(min_length=1, max_length=160)
    capability_help: dict[CatalogCapability, str]
    capabilities: list[CatalogCapability] = Field(min_length=1, max_length=3)
    record_count: int = Field(strict=True, ge=0, le=256)
    manifest_bytes: int = Field(strict=True, ge=1, le=65_536)
    scope: CatalogScope

    @field_validator("display_name", "description")
    @classmethod
    def bounded_text(cls, value: str, info: object) -> str:
        maximum = 64 if getattr(info, "field_name", "") == "display_name" else 160
        try:
            if len(value.encode("utf-8")) > maximum:
                raise ValueError("invalid_input")
        except UnicodeEncodeError:
            raise ValueError("invalid_input") from None
        return value

    @field_validator("capability_help")
    @classmethod
    def bounded_help(cls, value: dict[CatalogCapability, str]) -> dict[CatalogCapability, str]:
        if not value:
            raise ValueError("invalid_input")
        for text in value.values():
            try:
                if len(text.encode("utf-8")) > 180:
                    raise ValueError("invalid_input")
            except UnicodeEncodeError:
                raise ValueError("invalid_input") from None
        return value

    @model_validator(mode="after")
    def capabilities_match_kind(self) -> "CatalogEntryV2":
        expected = {"structured": {"profile", "query"}, "messages": {"search"}}[self.kind]
        if len(self.capabilities) != len(set(self.capabilities)):
            raise ValueError("invalid_input")
        if set(self.capabilities) != expected or set(self.capability_help) != expected:
            raise ValueError("capability_mismatch")
        return self


class CatalogV2(V2StrictModel):
    version: Literal["2"]
    catalog_revision: CatalogRevision
    entries: list[CatalogEntryV2] = Field(min_length=1, max_length=8)

    @model_validator(mode="after")
    def registered_sources_and_size(self) -> "CatalogV2":
        source_ids = {entry.source.source_id for entry in self.entries}
        if len(source_ids) != len(self.entries) or source_ids != {SourceId.SALES, SourceId.SUPPORT}:
            raise ValueError("unsupported_source")
        for entry in self.entries:
            expected = _REGISTERED[entry.source.source_id]
            if entry.model_dump(mode="json") != expected:
                raise ValueError("source_mismatch")
        if len(canonical_json(self)) > 4_096:
            raise ValueError("result_limit")
        return self


def _entry(
    source: SourceIdentity,
    schema_revision: str,
    profile_revision: str | None,
    kind: CatalogKind,
    display_name: str,
    description: str,
    capability_help: dict[CatalogCapability, str],
    capabilities: list[CatalogCapability],
    record_count: int,
    manifest_bytes: int,
) -> dict[str, object]:
    return {
        "source": source.model_dump(mode="json"),
        "schema_revision": schema_revision,
        "profile_revision": profile_revision,
        "kind": kind,
        "display_name": display_name,
        "description": description,
        "capability_help": capability_help,
        "capabilities": capabilities,
        "record_count": record_count,
        "manifest_bytes": manifest_bytes,
        "scope": "complete_immutable_fixture",
    }


_REGISTERED: dict[SourceId, dict[str, object]] = {
    SourceId.SALES: _entry(
        DEMO_SOURCE,
        "sales-demo.v1",
        "m3-profile.v1",
        "structured",
        "Sales demo",
        "Synthetic net sales lines for bounded structured analysis.",
        {
            "profile": "Summarize fields and bounded statistics.",
            "query": "Ask for read-only totals, groups, rankings or period comparisons.",
        },
        ["profile", "query"],
        24,
        1025,
    ),
    SourceId.SUPPORT: _entry(
        SUPPORT_SOURCE,
        "support-demo.v1",
        None,
        "messages",
        "Support messages",
        "Synthetic support messages for targeted lexical examples.",
        {
            "search": (
                "Find matching messages with exact IDs and source quotes; "
                "hits do not establish prevalence."
            )
        },
        ["search"],
        16,
        3091,
    ),
}


def registered_catalog() -> CatalogV2:
    """Return the server-owned registry; callers cannot supply fixture paths."""
    return CatalogV2(
        version="2",
        catalog_revision="m4-catalog.v1",
        entries=[CatalogEntryV2.model_validate(value) for value in _REGISTERED.values()],
    )
