"""Private Python Worker placeholder; P3 owns its service-binding routes."""

import sqlite3
import sys

from data_intel.service_contracts import RuntimeProvenanceError, runtime_info_from_bindings
from workers import Response, WorkerEntrypoint  # type: ignore[attr-defined]


# The Worker SDK is isolated to the Worker project; the root gate lacks its types.
class Default(WorkerEntrypoint):  # type: ignore[misc]
    """Keep direct access closed while exercising actual runtime bindings."""

    async def fetch(self, request: object) -> object:
        del request
        try:
            metadata = getattr(self.env, "CF_VERSION_METADATA", None)
            runtime_info_from_bindings(
                runtime_mode=getattr(self.env, "RUNTIME_MODE", None),
                build_revision=getattr(self.env, "BUILD_REVISION", None),
                worker_version_id=getattr(metadata, "id", None),
                python_version=sys.version.split()[0],
                sqlite_version=sqlite3.sqlite_version,
            )
        except RuntimeProvenanceError:
            return Response("runtime_incompatible", status=503)
        return Response("Not found", status=404)
