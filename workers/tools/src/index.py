"""Private Python service binding; no public Worker route is configured."""

import sqlite3
import sys
from urllib.parse import urlsplit

from data_intel.query_engine import SQLiteQueryEngine
from data_intel.service_contracts import RuntimeProvenanceError, runtime_info_from_bindings
from data_intel.service_routes import error_response, handle_service
from data_intel.service_v2_routes import (
    error_response_v2,
    handle_service_v2,
    runtime_provenance_v2_from_bindings,
)
from data_intel.worker_transport import BodyTooLarge, JsException, read_bounded_body
from workers import Response, WorkerEntrypoint  # type: ignore[attr-defined]


# The Worker SDK is isolated to the Worker project; the root gate lacks its types.
class Default(WorkerEntrypoint):  # type: ignore[misc]
    """Expose only three bounded service-binding operations."""

    async def fetch(self, request: object) -> object:
        method = getattr(request, "method", None)
        path = urlsplit(getattr(request, "url", "")).path
        if isinstance(method, str) and path.startswith("/v2/"):
            return await self._fetch_v2(request, method, path)
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

    async def _fetch_v2(self, request: object, method: str, path: str) -> object:
        metadata = getattr(self.env, "CF_VERSION_METADATA", None)
        try:
            runtime = runtime_provenance_v2_from_bindings(
                runtime_mode=getattr(self.env, "RUNTIME_MODE", None),
                build_revision=getattr(self.env, "BUILD_REVISION", None),
                worker_version_id=getattr(metadata, "id", None),
                python_version=sys.version.split()[0],
                sqlite_version=sqlite3.sqlite_version,
            )
        except (TypeError, ValueError):
            status, body = error_response_v2("runtime_incompatible", "transport")
        else:
            limits = {
                "/v2/profile": 1_024,
                "/v2/query": 16_384,
                "/v2/search": 2_048,
            }
            try:
                payload = await read_bounded_body(request, limits.get(path, 0))
                status, body = handle_service_v2(method, path, payload, runtime)
            except BodyTooLarge:
                status, body = error_response_v2("result_limit", "input")
            except (AttributeError, JsException, OSError, TypeError, ValueError):
                status, body = error_response_v2("runtime_incompatible", "transport")
        return Response(body, status=status, headers={"content-type": "application/json"})
