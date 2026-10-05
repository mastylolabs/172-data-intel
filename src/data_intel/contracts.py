"""Transport validation only: SQL intents remain untrusted, unexecuted proposals."""

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

Digest = Annotated[str, StringConstraints(strict=True, pattern=r"^[a-f0-9]{64}$")]
Revision = Annotated[str, StringConstraints(strict=True, pattern=r"^[a-z][a-z0-9._-]{0,63}$")]


class SourceId(StrEnum):
    SALES = "sales"
    SUPPORT = "support"


class SourceIdentity(BaseModel):
    """Declared identity; no fixture existence or source integrity verification yet."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    version: Literal["1"]
    source_id: SourceId
    snapshot_sha256: Digest
    meaning_revision: Revision


class SqlIntent(BaseModel):
    """Generic SQL proposal; acceptance grants no execution or source authorization."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    version: Literal["1"]
    source: SourceIdentity
    question: str = Field(strict=True, min_length=1, max_length=2000, pattern=r"\S")
    sql: str = Field(strict=True, min_length=1, max_length=8000, pattern=r"\S")
    max_rows: int = Field(strict=True, ge=1, le=1000)
