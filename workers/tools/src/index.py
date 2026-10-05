"""Private Python service binding; no public Worker route is configured."""

import sqlite3
import sys
from urllib.parse import urlsplit

from data_intel.query_engine import SQLiteQueryEngine
from data_intel.service_contracts import RuntimeProvenanceError, runtime_info_from_bindings
from data_intel.service_routes import error_response, handle_service
from data_intel.worker_transport import BodyTooLarge, JsException, read_bounded_body
from workers import Response, WorkerEntrypoint  # type: ignore[attr-defined]


# The Worker SDK is isolated to the Worker project; the root gate lacks its types.
class Default(WorkerEntrypoint):  # type: ignore[misc]
    """Expose only three bounded service-binding operations."""

    async def fetch(self, request: object) -> object:
        try:
            metadata = getattr(self.env, "CF_VERSION_METADATA", None)
            runtime = runtime_info_from_bindings(
                runtime_mode=getattr(self.env, "RUNTIME_MODE", None),
                build_revision=getattr(self.env, "BUILD_REVISION", None),
                worker_version_id=getattr(metadata, "id", None),
                python_version=sys.version.split()[0],
                sqlite_version=sqlite3.sqlite_version,
            )
        except RuntimeProvenanceError:
            status, body = error_response("runtime_incompatible", "transport")
        else:
            try:
                method = getattr(request, "method", None)
                if not isinstance(method, str):
                    raise TypeError("invalid request method")
                path = urlsplit(getattr(request, "url", "")).path
                payload = (
                    await read_bounded_body(request)
                    if method == "POST" and path == "/query"
                    else b""
                )
                status, body = handle_service(method, path, payload, runtime, SQLiteQueryEngine())
            except BodyTooLarge:
                status, body = error_response("result_limit", "input")
            except (AttributeError, JsException, OSError, TypeError, ValueError):
                status, body = error_response("unsupported_transport", "transport")
        return Response(body, status=status, headers={"content-type": "application/json"})
