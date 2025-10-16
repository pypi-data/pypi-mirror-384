import datetime as _dt
import json
import logging as _logging
import mimetypes
import os
import pathlib
import time as _time
from functools import wraps as _wraps
from typing import (
    IO,
    Any,
    Callable,
    Iterable,
    Mapping,
    MutableMapping,
    Sequence,
    TypedDict,
    TypeVar,
)

import requests
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Environment variables inside the kernel VM
# ---------------------------------------------------------------------------

TOKEN_ENV = "LUMERA_TOKEN"
BASE_URL_ENV = "LUMERA_BASE_URL"
ENV_PATH = "/root/.env"

# Load variables from /root/.env if it exists (and also current dir .env)
load_dotenv(override=False)  # Local .env (no-op in prod)
load_dotenv(ENV_PATH, override=False)


# Determine API base URL ------------------------------------------------------

_default_api_base = "https://app.lumerahq.com/api"
API_BASE = os.getenv(BASE_URL_ENV, _default_api_base).rstrip("/")
MOUNT_ROOT_ENV = "LUMERA_MOUNT_ROOT"
DEFAULT_MOUNT_ROOT = "/lumera-files"  # backward compatible default
MOUNT_ROOT = os.getenv(MOUNT_ROOT_ENV, DEFAULT_MOUNT_ROOT)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _ensure_token() -> str:
    """Return the personal Lumera token, loading /root/.env if necessary."""

    token = os.getenv(TOKEN_ENV)
    if token:
        return token

    raise RuntimeError(
        f"{TOKEN_ENV} environment variable not set (checked environment and {ENV_PATH})"
    )


# ---------------------------------------------------------------------------
# Provider-agnostic access-token retrieval
# ---------------------------------------------------------------------------


# _token_cache maps provider
# without an explicit expiry (e.g. API keys) we store `float('+inf')` so that
# they are never considered stale.
# Map provider -> (token, expiry)
_token_cache: dict[str, tuple[str, float]] = {}

# ``expires_at`` originates from the Lumera API and may be one of several
# formats: epoch seconds (``int``/``float``), an RFC 3339 / ISO-8601 string, or
# even ``None``. We therefore accept ``Any`` and normalise it internally.


# Accept multiple formats returned by the API (epoch seconds or ISO-8601), or
# ``None`` when the token never expires.


def _parse_expiry(expires_at: int | float | str | None) -> float:
    """Convert `expires_at` from the API (may be ISO8601 or epoch) to epoch seconds.

    Returns +inf if `expires_at` is falsy/None.
    """

    if not expires_at:
        return float("inf")

    if isinstance(expires_at, (int, float)):
        return float(expires_at)

    # Assume RFC 3339 / ISO 8601 string.
    if isinstance(expires_at, str):
        if expires_at.endswith("Z"):
            expires_at = expires_at[:-1] + "+00:00"
        return _dt.datetime.fromisoformat(expires_at).timestamp()

    raise TypeError(f"Unsupported expires_at format: {type(expires_at)!r}")


def _fetch_access_token(provider: str) -> tuple[str, float]:
    """Call the Lumera API to obtain a valid access token for *provider*."""

    provider = provider.lower().strip()
    if not provider:
        raise ValueError("provider is required")

    token = _ensure_token()

    url = f"{API_BASE}/connections/{provider}/access-token"
    headers = {"Authorization": f"token {token}"}

    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()

    data = resp.json()
    access_token = data.get("access_token")
    expires_at = data.get("expires_at")

    if not access_token:
        raise RuntimeError(f"Malformed response from Lumera when fetching {provider} access token")

    expiry_ts = _parse_expiry(expires_at)
    return access_token, expiry_ts


def get_access_token(provider: str, min_valid_seconds: int = 900) -> str:
    """Return a cached access token for *provider* valid
    *min_valid_seconds*.

       Automatically refreshes tokens via the Lumera API when they are missing or
       close to expiry.  For tokens without an expiry (API keys) the first value
       is cached indefinitely.
    """

    global _token_cache

    provider = provider.lower().strip()
    if not provider:
        raise ValueError("provider is required")

    now = _time.time()

    cached = _token_cache.get(provider)
    if cached is not None:
        access_token, expiry_ts = cached
        if (expiry_ts - now) >= min_valid_seconds:
            return access_token

    # (Re)fetch from server
    access_token, expiry_ts = _fetch_access_token(provider)
    _token_cache[provider] = (access_token, expiry_ts)
    return access_token


# Backwards-compatibility wrapper ------------------------------------------------


def get_google_access_token(min_valid_seconds: int = 900) -> str:
    """Legacy helper kept for old notebooks
    delegates to get_access_token."""

    return get_access_token("google", min_valid_seconds=min_valid_seconds)


# ---------------------------------------------------------------------------
# Function timing decorator
# ---------------------------------------------------------------------------

_logger = _logging.getLogger(__name__)

R = TypeVar("R")


def log_timed(fn: Callable[..., R]) -> Callable[..., R]:
    """Decorator that logs entry/exit and wall time for function calls.

    Logs at INFO level using a module-level logger named after this module.
    """

    @_wraps(fn)
    def wrapper(*args: object, **kwargs: object) -> R:
        _logger.info(f"Entering {fn.__name__}()")
        t0 = _time.perf_counter()
        try:
            return fn(*args, **kwargs)
        finally:
            dt = _time.perf_counter() - t0
            _logger.info(f"Exiting {fn.__name__}() - took {dt:.3f}s")

    return wrapper


# ---------------------------------------------------------------------------
# Unified FileRef helpers
# ---------------------------------------------------------------------------


class FileRef(TypedDict, total=False):
    scope: str
    id: str
    name: str
    path: str
    run_path: str
    object_name: str
    mime: str
    size: int


class CollectionField(TypedDict, total=False):
    id: str
    name: str
    type: str
    system: bool
    required: bool
    presentable: bool
    hidden: bool
    options: dict[str, Any]


class LumeraAPIError(RuntimeError):
    """Raised when requests to the Lumera API fail."""

    def __init__(
        self, status_code: int, message: str, *, url: str, payload: object | None = None
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload
        self.url = url

    def __str__(self) -> str:  # pragma: no cover - trivial string formatting
        base = super().__str__()
        return (
            f"{self.status_code} {self.url}: {base}" if base else f"{self.status_code} {self.url}"
        )


def _api_url(path: str) -> str:
    path = path.lstrip("/")
    if path.startswith("pb/"):
        return f"{API_BASE}/{path}"
    if path == "collections" or path.startswith("collections/"):
        return f"{API_BASE}/pb/{path}"
    return f"{API_BASE}/{path}"


def _raise_api_error(resp: requests.Response) -> None:
    message = resp.text.strip()
    payload: object | None = None
    content_type = resp.headers.get("Content-Type", "").lower()
    if "application/json" in content_type:
        try:
            payload = resp.json()
        except ValueError:
            payload = None
        else:
            if isinstance(payload, MutableMapping):
                for key in ("error", "message", "detail"):
                    value = payload.get(key)
                    if isinstance(value, str) and value.strip():
                        message = value
                        break
                else:
                    message = json.dumps(payload)
            else:
                message = json.dumps(payload)
    if resp.status_code == 400 and payload and isinstance(payload, MutableMapping):
        if any(
            isinstance(value, str) and ("unique" in value.lower() or "already" in value.lower())
            for value in payload.values()
        ):
            raise RecordNotUniqueError(resp.url, payload) from None
    raise LumeraAPIError(resp.status_code, message, url=resp.url, payload=payload)


class RecordNotUniqueError(LumeraAPIError):
    """Raised when attempting to insert a record that violates a uniqueness constraint."""

    def __init__(self, url: str, payload: MutableMapping[str, object]) -> None:
        message = next(
            (value for value in payload.values() if isinstance(value, str) and value.strip()),
            "record violates uniqueness constraint",
        )
        super().__init__(400, message, url=url, payload=payload)


def _api_request(
    method: str,
    path: str,
    *,
    params: Mapping[str, Any] | None = None,
    json_body: Mapping[str, Any] | None = None,
    data: Mapping[str, Any] | None = None,
    files: Mapping[str, Any] | None = None,
    timeout: int = 30,
) -> object | None:
    token = _ensure_token()
    url = _api_url(path)

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/json",
    }

    resp = requests.request(
        method,
        url,
        params=params,
        json=json_body,
        data=data,
        files=files,
        headers=headers,
        timeout=timeout,
    )

    if not resp.ok:
        _raise_api_error(resp)

    if resp.status_code == 204 or method.upper() == "DELETE":
        return None

    content_type = resp.headers.get("Content-Type", "").lower()
    if "application/json" in content_type:
        if not resp.text.strip():
            return {}
        return resp.json()
    return resp.text if resp.text else None


def _ensure_mapping(payload: Mapping[str, Any] | None, *, name: str) -> dict[str, Any]:
    if payload is None:
        return {}
    if not isinstance(payload, Mapping):
        raise TypeError(f"{name} must be a mapping, got {type(payload)!r}")
    return dict(payload)


_UNSET = object()


def list_collections() -> dict[str, Any]:
    """Return all PocketBase collections visible to the current tenant."""

    return _api_request("GET", "collections")


def get_collection(collection_id_or_name: str) -> dict[str, Any]:
    """Retrieve a single PocketBase collection by name or id."""

    if not collection_id_or_name:
        raise ValueError("collection_id_or_name is required")
    return _api_request("GET", f"collections/{collection_id_or_name}")


def create_collection(
    name: str,
    *,
    collection_type: str = "base",
    schema: Iterable[CollectionField] | None = None,
    list_rule: str | None = None,
    view_rule: str | None = None,
    create_rule: str | None = None,
    update_rule: str | None = None,
    delete_rule: str | None = None,
    indexes: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Create a new PocketBase collection and return the server payload."""

    if not name or not name.strip():
        raise ValueError("name is required")

    payload: dict[str, Any] = {"name": name.strip()}
    if collection_type:
        payload["type"] = collection_type
    if schema is not None:
        payload["schema"] = [dict(field) for field in schema]
    if list_rule is not None:
        payload["listRule"] = list_rule
    if view_rule is not None:
        payload["viewRule"] = view_rule
    if create_rule is not None:
        payload["createRule"] = create_rule
    if update_rule is not None:
        payload["updateRule"] = update_rule
    if delete_rule is not None:
        payload["deleteRule"] = delete_rule
    if indexes is not None:
        payload["indexes"] = list(indexes)

    return _api_request("POST", "collections", json_body=payload)


def update_collection(
    collection_id_or_name: str,
    *,
    name: str | None | object = _UNSET,
    collection_type: str | None | object = _UNSET,
    schema: Iterable[CollectionField] | object = _UNSET,
    list_rule: str | None | object = _UNSET,
    view_rule: str | None | object = _UNSET,
    create_rule: str | None | object = _UNSET,
    update_rule: str | None | object = _UNSET,
    delete_rule: str | None | object = _UNSET,
    indexes: Iterable[str] | object = _UNSET,
) -> dict[str, Any]:
    """Update a PocketBase collection."""

    if not collection_id_or_name:
        raise ValueError("collection_id_or_name is required")

    payload: dict[str, Any] = {}

    if name is not _UNSET:
        if name is None or not str(name).strip():
            raise ValueError("name cannot be empty")
        payload["name"] = str(name).strip()

    if collection_type is not _UNSET:
        payload["type"] = collection_type

    if schema is not _UNSET:
        if schema is None:
            raise ValueError("schema cannot be None; provide an iterable of fields")
        payload["schema"] = [dict(field) for field in schema]

    if list_rule is not _UNSET:
        payload["listRule"] = list_rule
    if view_rule is not _UNSET:
        payload["viewRule"] = view_rule
    if create_rule is not _UNSET:
        payload["createRule"] = create_rule
    if update_rule is not _UNSET:
        payload["updateRule"] = update_rule
    if delete_rule is not _UNSET:
        payload["deleteRule"] = delete_rule
    if indexes is not _UNSET:
        payload["indexes"] = list(indexes) if indexes is not None else []

    if not payload:
        raise ValueError("no fields provided to update")

    return _api_request("PATCH", f"collections/{collection_id_or_name}", json_body=payload)


def delete_collection(collection_id_or_name: str) -> None:
    """Delete a PocketBase collection by name or id."""

    if not collection_id_or_name:
        raise ValueError("collection_id_or_name is required")
    _api_request("DELETE", f"collections/{collection_id_or_name}")


def list_records(
    collection_id_or_name: str,
    *,
    page: int | None = None,
    per_page: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
    sort: str | None = None,
    filter: Mapping[str, Any] | Sequence[Any] | None = None,
) -> dict[str, Any]:
    """List records for the given PocketBase collection."""

    if not collection_id_or_name:
        raise ValueError("collection_id_or_name is required")

    params: dict[str, Any] = {}
    if page is not None:
        params["page"] = page
    if per_page is not None:
        params["perPage"] = per_page
    if limit is not None:
        params["limit"] = limit
    if offset is not None:
        params["offset"] = offset
    if sort is not None:
        params["sort"] = sort
    if filter is not None:
        params["filter"] = json.dumps(filter)

    path = f"collections/{collection_id_or_name}/records"
    return _api_request("GET", path, params=params or None)


def get_record(collection_id_or_name: str, record_id: str) -> dict[str, Any]:
    """Retrieve a single record by id."""

    if not collection_id_or_name:
        raise ValueError("collection_id_or_name is required")
    if not record_id:
        raise ValueError("record_id is required")

    path = f"collections/{collection_id_or_name}/records/{record_id}"
    return _api_request("GET", path)


def get_record_by_external_id(collection_id_or_name: str, external_id: str) -> dict[str, Any]:
    """Retrieve a record by its unique external_id."""

    if not collection_id_or_name:
        raise ValueError("collection_id_or_name is required")
    if not external_id:
        raise ValueError("external_id is required")

    response = list_records(
        collection_id_or_name,
        per_page=1,
        filter={"external_id": external_id},
    )
    items = response.get("items") if isinstance(response, dict) else None
    if not items:
        url = _api_url(f"collections/{collection_id_or_name}/records")
        raise LumeraAPIError(404, "record not found", url=url, payload=None)
    first = items[0]
    if not isinstance(first, dict):
        raise RuntimeError("unexpected response payload")
    return first


def run_agent(
    agent_id: str,
    *,
    inputs: Mapping[str, Any] | str | None = None,
    files: Mapping[str, str | os.PathLike[str] | Sequence[str | os.PathLike[str]]] | None = None,
    status: str | None = None,
    outputs: Mapping[str, Any] | str | None = None,
    error: str | None = None,
) -> dict[str, Any]:
    """Create an agent run and optionally upload files for file inputs."""

    agent_id = agent_id.strip()
    if not agent_id:
        raise ValueError("agent_id is required")

    run_id: str | None = None

    prepared_inputs = _prepare_agent_inputs(inputs) or {}

    file_map = files or {}
    run_id, upload_descriptors = _upload_agent_files(run_id, file_map)

    final_inputs = json.loads(json.dumps(prepared_inputs)) if prepared_inputs else {}
    for key, descriptors in upload_descriptors.items():
        if len(descriptors) == 1 and not _is_sequence(file_map.get(key)):
            final_inputs[key] = descriptors[0]
        else:
            final_inputs[key] = descriptors

    cleaned_status = status.strip() if isinstance(status, str) else ""
    payload: dict[str, Any] = {
        "agent_id": agent_id,
        "inputs": json.dumps(final_inputs),
        "status": cleaned_status or "queued",
    }
    if run_id:
        payload["id"] = run_id
    if outputs is not None:
        payload["outputs"] = _ensure_json_string(outputs, name="outputs")
    if error is not None:
        payload["error"] = error

    run = _api_request("POST", "agent-runs", json_body=payload)
    if not isinstance(run, dict):
        raise RuntimeError("unexpected response payload")
    return run


def _prepare_agent_inputs(
    inputs: Mapping[str, Any] | str | None,
) -> dict[str, Any] | None:
    if inputs is None:
        return None
    if isinstance(inputs, str):
        inputs = inputs.strip()
        if not inputs:
            return {}
        try:
            parsed = json.loads(inputs)
        except json.JSONDecodeError as exc:
            raise ValueError("inputs must be JSON-serialisable") from exc
        if not isinstance(parsed, dict):
            raise TypeError("inputs JSON must deserialize to an object")
        return parsed

    # Mapping path – normalise via JSON roundtrip to guarantee compatibility
    try:
        serialised = json.dumps(inputs)
        parsed = json.loads(serialised)
    except (TypeError, ValueError) as exc:
        raise ValueError("inputs must be JSON-serialisable") from exc
    if not isinstance(parsed, dict):
        raise TypeError("inputs mapping must serialize to a JSON object")
    return parsed


def _ensure_json_string(value: Mapping[str, Any] | str, *, name: str) -> str:
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be JSON-serialisable") from exc


def _is_sequence(value: object) -> bool:
    if isinstance(value, (str, os.PathLike)):
        return False
    return isinstance(value, Sequence)


def _upload_agent_files(
    run_id: str | None,
    files: Mapping[str, str | os.PathLike[str] | Sequence[str | os.PathLike[str]]],
) -> tuple[str | None, dict[str, list[dict[str, Any]]]]:
    if not files:
        return run_id, {}

    results: dict[str, list[dict[str, Any]]] = {}
    for key, value in files.items():
        paths = _ensure_sequence(value)
        descriptors: list[dict[str, Any]] = []
        for path in paths:
            file_path = pathlib.Path(os.fspath(path)).expanduser().resolve()
            if not file_path.is_file():
                raise FileNotFoundError(file_path)

            filename = file_path.name
            content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
            size = file_path.stat().st_size

            body: dict[str, Any] = {
                "scope": "agent_run",
                "filename": filename,
                "content_type": content_type,
                "size": size,
            }
            if run_id:
                body["resource_id"] = run_id

            presign = _api_request(
                "POST",
                "uploads/presign",
                json_body=body,
            )
            if not isinstance(presign, dict):
                raise RuntimeError("unexpected presign response")

            upload_url = presign.get("upload_url")
            if not isinstance(upload_url, str) or not upload_url:
                raise RuntimeError("missing upload_url in presign response")

            resp_run_id = presign.get("run_id")
            if isinstance(resp_run_id, str) and resp_run_id:
                if run_id is None:
                    run_id = resp_run_id
                elif run_id != resp_run_id:
                    raise RuntimeError("presign returned inconsistent run_id")
            elif run_id is None:
                raise RuntimeError("presign response missing run_id")

            _upload_file_to_presigned(upload_url, file_path, content_type)

            descriptor: dict[str, Any] = {"name": filename}
            if presign.get("run_path"):
                descriptor["run_path"] = presign["run_path"]
            if presign.get("object_key"):
                descriptor["object_key"] = presign["object_key"]
            descriptors.append(descriptor)

        results[key] = descriptors
    return run_id, results


def _upload_file_to_presigned(upload_url: str, path: pathlib.Path, content_type: str) -> None:
    with open(path, "rb") as fh:
        resp = requests.put(
            upload_url, data=fh, headers={"Content-Type": content_type}, timeout=300
        )
        resp.raise_for_status()


def _ensure_sequence(
    value: str | os.PathLike[str] | Sequence[str | os.PathLike[str]],
) -> list[str | os.PathLike[str]]:
    if isinstance(value, (str, os.PathLike)):
        return [value]
    seq = list(value)
    if not seq:
        raise ValueError("file input sequence must not be empty")
    return seq


def _record_mutation(
    method: str,
    collection_id_or_name: str,
    payload: Mapping[str, Any] | None,
    *,
    record_id: str | None = None,
    files: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if not collection_id_or_name:
        raise ValueError("collection_id_or_name is required")

    data = _ensure_mapping(payload, name="payload")
    path = f"collections/{collection_id_or_name}/records"
    if record_id:
        if not record_id.strip():
            raise ValueError("record_id is required")
        path = f"{path}/{record_id}".rstrip("/")

    if files:
        form = {"@jsonPayload": json.dumps(data)}
        response = _api_request(method, path, data=form, files=files)
    else:
        response = _api_request(method, path, json_body=data)

    if not isinstance(response, dict):
        raise RuntimeError("unexpected response payload")
    return response


def create_record(
    collection_id_or_name: str,
    payload: Mapping[str, Any] | None = None,
    *,
    files: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a record in the specified collection."""

    return _record_mutation("POST", collection_id_or_name, payload, files=files)


def update_record(
    collection_id_or_name: str,
    record_id: str,
    payload: Mapping[str, Any] | None = None,
    *,
    files: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Update an existing record."""

    return _record_mutation(
        "PATCH",
        collection_id_or_name,
        payload,
        record_id=record_id,
        files=files,
    )


def delete_record(collection_id_or_name: str, record_id: str) -> None:
    """Delete a record from the specified collection."""

    if not collection_id_or_name:
        raise ValueError("collection_id_or_name is required")
    if not record_id:
        raise ValueError("record_id is required")

    path = f"collections/{collection_id_or_name}/records/{record_id}"
    _api_request("DELETE", path)


def upsert_record(
    collection_id_or_name: str,
    payload: Mapping[str, Any] | None = None,
    *,
    files: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Create or update a record identified by external_id."""

    if not collection_id_or_name:
        raise ValueError("collection_id_or_name is required")

    data = _ensure_mapping(payload, name="payload")
    external_id = str(data.get("external_id", "")).strip()
    if not external_id:
        raise ValueError("payload.external_id is required for upsert")
    data["external_id"] = external_id

    path = f"collections/{collection_id_or_name}/records/upsert"
    if files:
        form = {"@jsonPayload": json.dumps(data)}
        response = _api_request("POST", path, data=form, files=files)
    else:
        response = _api_request("POST", path, json_body=data)

    if not isinstance(response, dict):
        raise RuntimeError("unexpected response payload")
    return response


def resolve_path(file_or_path: str | FileRef) -> str:
    """Return an absolute path string for a FileRef or path-like input.

    Accepts:
      - str paths (returned as-is)
      - dicts with keys like {"path": "/..."} or {"run_path": "/..."}
    """

    if isinstance(file_or_path, str):
        return file_or_path
    if isinstance(file_or_path, dict):
        if "path" in file_or_path and isinstance(file_or_path["path"], str):
            return file_or_path["path"]
        if "run_path" in file_or_path and isinstance(file_or_path["run_path"], str):
            return file_or_path["run_path"]
    raise TypeError("Unsupported file_or_path; expected str or dict with 'path'/'run_path'")


def open_file(
    file_or_path: str | FileRef,
    mode: str = "r",
    **kwargs: object,
) -> IO[str] | IO[bytes]:
    """Open a file from a FileRef or absolute path inside the mount root.

    Usage:
        with open_file(file_ref, 'r') as f:
            data = f.read()
    """

    p = resolve_path(file_or_path)
    return open(p, mode, **kwargs)


def to_filerefs(
    values: Iterable[str | FileRef],
    scope: str,
    id: str,
) -> list[FileRef]:
    """Convert a list of strings or partial dicts into FileRef-like dicts.

    This is a helper for tests/fixtures; it does not perform storage lookups.
    If a value is a string, it is assumed to be an absolute path under the mount root.
    """

    out: list[FileRef] = []
    for v in values:
        if isinstance(v, str):
            name = os.path.basename(v)
            object_name = f"{scope}/{id}/{name}"
            out.append(
                {
                    "scope": scope,
                    "id": id,
                    "name": name,
                    "path": v,
                    "object_name": object_name,
                }
            )
        elif isinstance(v, dict):
            # Fill minimal fields if missing
            name = v.get("name") or os.path.basename(v.get("path") or v.get("run_path") or "")
            path = v.get("path") or v.get("run_path") or ""
            object_name = v.get("object_name") or f"{scope}/{id}/{name}"
            out.append(
                {
                    "scope": v.get("scope", scope),
                    "id": v.get("id", id),
                    "name": name,
                    "path": path,
                    "object_name": object_name,
                    **{k: v[k] for k in ("mime", "size") if k in v},
                }
            )
        else:
            raise TypeError("values must contain str or dict entries")
    return out


# ---------------------------------------------------------------------------
# Document upload helper (unchanged apart from minor refactoring)
# ---------------------------------------------------------------------------


def _pretty_size(size: int) -> str:
    """Return *size* in bytes as a human-readable string (e.g. "1.2 MB").

    Iteratively divides by 1024 and appends the appropriate unit all the way up
    to terabytes.
    """

    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}" if unit != "B" else f"{size} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def _upload_session_file(file_path: str, session_id: str) -> dict:
    """Upload file into the current Playground session's file space."""

    token = _ensure_token()
    path = pathlib.Path(file_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(path)

    filename = path.name
    size = path.stat().st_size
    mimetype = mimetypes.guess_type(filename)[0] or "application/octet-stream"

    headers = {"Authorization": f"token {token}", "Content-Type": "application/json"}

    # 1) Get signed upload URL
    resp = requests.post(
        f"{API_BASE}/sessions/{session_id}/files/upload-url",
        json={"filename": filename, "content_type": mimetype, "size": size},
        headers=headers,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    upload_url: str = data["upload_url"]
    notebook_path: str = data.get("notebook_path", "")

    # 2) Upload bytes
    with open(path, "rb") as fp:
        put = requests.put(upload_url, data=fp, headers={"Content-Type": mimetype}, timeout=300)
        put.raise_for_status()

    # 3) Optionally enable docs (idempotent; ignore errors)
    try:
        requests.post(
            f"{API_BASE}/sessions/{session_id}/enable-docs",
            headers=headers,
            timeout=15,
        )
    except Exception:
        pass

    return {"name": filename, "notebook_path": notebook_path}


def _upload_agent_run_file(file_path: str, run_id: str) -> dict:
    """Upload file into the current Agent Run's file space."""

    token = _ensure_token()
    path = pathlib.Path(file_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(path)

    filename = path.name
    size = path.stat().st_size
    mimetype = mimetypes.guess_type(filename)[0] or "application/octet-stream"

    headers = {"Authorization": f"token {token}", "Content-Type": "application/json"}

    # 1) Get signed upload URL for the agent run
    resp = requests.post(
        f"{API_BASE}/agent-runs/{run_id}/files/upload-url",
        json={"filename": filename, "content_type": mimetype, "size": size},
        headers=headers,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    upload_url = data["upload_url"]

    # Prefer returning the structured FileRef if available
    file_ref = data.get("file") if isinstance(data, dict) else None

    # 2) Upload bytes
    with open(path, "rb") as fp:
        put = requests.put(upload_url, data=fp, headers={"Content-Type": mimetype}, timeout=300)
        put.raise_for_status()

    # 3) Return a minimal record, preferring the backend-provided FileRef
    if isinstance(file_ref, dict):
        return file_ref
    # Fallback to a compact shape similar to session uploads
    run_path = (
        data.get("run_path") or data.get("path") or f"/lumera-files/agent_runs/{run_id}/{filename}"
    )
    return {
        "name": filename,
        "run_path": run_path,
        "object_name": data.get("object_name"),
    }


def _upload_document(file_path: str) -> dict:
    """Fallback: Upload file into global Documents collection."""

    token = _ensure_token()
    path = pathlib.Path(file_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(path)

    filename = path.name
    size = path.stat().st_size
    mimetype = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    pretty = _pretty_size(size)

    headers = {"Authorization": f"token {token}", "Content-Type": "application/json"}
    documents_base = f"{API_BASE}/documents"

    # 1) Create
    resp = requests.post(
        documents_base,
        json={
            "title": filename,
            "content": f"File to be uploaded: {filename} ({pretty})",
            "type": mimetype.split("/")[-1],
            "status": "uploading",
        },
        headers=headers,
        timeout=30,
    )
    resp.raise_for_status()
    doc = resp.json()
    doc_id = doc["id"]

    # 2) Signed URL
    resp = requests.post(
        f"{documents_base}/{doc_id}/upload-url",
        json={"filename": filename, "content_type": mimetype, "size": size},
        headers=headers,
        timeout=30,
    )
    resp.raise_for_status()
    upload_url: str = resp.json()["upload_url"]

    # 3) PUT bytes
    with open(path, "rb") as fp:
        put = requests.put(upload_url, data=fp, headers={"Content-Type": mimetype}, timeout=300)
        put.raise_for_status()

    # 4) Finalize
    resp = requests.put(
        f"{documents_base}/{doc_id}",
        json={
            "status": "uploaded",
            "content": f"Uploaded file: {filename} ({pretty})",
        },
        headers=headers,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def save_to_lumera(file_path: str) -> dict:
    """Upload *file_path* to the current context.

    Priority:
      1) If running inside an Agent executor (LUMERA_RUN_ID), upload to that run
      2) Else if running in Playground (LUMERA_SESSION_ID), upload to the session
      3) Else, upload to global Documents
    """

    run_id = os.getenv("LUMERA_RUN_ID", "").strip()
    if run_id:
        return _upload_agent_run_file(file_path, run_id)

    session_id = os.getenv("LUMERA_SESSION_ID", "").strip()
    if session_id:
        return _upload_session_file(file_path, session_id)
    return _upload_document(file_path)
