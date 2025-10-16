"""Firebase authentication and Firestore helpers for remote agents."""

from __future__ import annotations

import asyncio
import base64
import contextlib
import json
import os
import queue
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, Iterable, Iterator, Optional

import requests

from python_webchannel import (  # type: ignore[attr-defined]
    EventType,
    WebChannelError,
    WebChannelOptions,
    create_web_channel_transport,
)

HUROZO_FIREBASE_API_KEY = os.getenv("HUROZO_FIREBASE_API_KEY", "AIzaSyD2SmbNJTmnzEiYGzujQPbTX1VixZqxqpo")
HUROZO_FIREBASE_PROJECT = os.getenv("HUROZO_FIREBASE_PROJECT", "hurozo")
HUROZO_FIREBASE_DATABASE = os.getenv("HUROZO_FIREBASE_DATABASE", "hurozo")
EVENT_TTL_SECONDS = int(os.getenv("HUROZO_EVENT_TTL_SECONDS", "3600"))


class FirestoreListenError(RuntimeError):
    """Raised when the Firestore Listen stream fails."""


@dataclass
class ListenClientOptions:
    project_id: str
    database_id: str = "(default)"
    use_ssl: bool = True
    host: str = "firestore.googleapis.com"
    auth_headers: Dict[str, str] = field(default_factory=dict)
    app_id: Optional[str] = None
    debug: bool = False

    def base_url(self) -> str:
        scheme = "https" if self.use_ssl else "http"
        return f"{scheme}://{self.host}/google.firestore.v1.Firestore/Listen/channel"

    @property
    def database_path(self) -> str:
        return f"projects/{self.project_id}/databases/{self.database_id}"

    @property
    def request_params_header(self) -> str:
        return f"database={self.database_path}"


class FirestoreListenClient:
    """Adapter that exposes a synchronous generator interface on python_webchannel."""

    def __init__(self, *, options: ListenClientOptions) -> None:
        self._options = options

    def listen(
        self,
        request: Dict[str, Any],
        *,
        stop_check: Optional[Callable[[], bool]] = None,
    ) -> "_FirestoreListenStream":
        return _FirestoreListenStream(options=self._options, request=request, stop_check=stop_check)


class _FirestoreListenStream(Iterator[Dict[str, Any]]):
    """Run the async WebChannel client on a background event loop."""

    _CLOSE_SENTINEL = object()
    _ERROR_SENTINEL = object()

    def __init__(
        self,
        *,
        options: ListenClientOptions,
        request: Dict[str, Any],
        stop_check: Optional[Callable[[], bool]] = None,
    ) -> None:
        self._options = options
        self._request = request
        self._stop_check = stop_check
        self._queue: "queue.Queue[Any]" = queue.Queue()
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, name="firestore-listen", daemon=True)
        self._channel = None
        self._error: Optional[FirestoreListenError] = None
        self._closed = False
        self._closing = threading.Event()
        self._thread.start()
        self._startup_future = asyncio.run_coroutine_threadsafe(self._open_channel(), self._loop)
        try:
            self._startup_future.result()
        except Exception as exc:  # pragma: no cover - startup errors are surfaced
            self._error = self._to_listen_error(exc)
            self.close()
            raise self._error

    def __iter__(self) -> "_FirestoreListenStream":
        return self

    def __next__(self) -> Dict[str, Any]:
        while True:
            if self._stop_check and self._stop_check():
                self.close()
                raise StopIteration
            if self._error is not None:
                error = self._error
                self.close()
                raise error
            if self._closed and self._queue.empty():
                self.close()
                raise StopIteration
            try:
                item = self._queue.get(timeout=0.2)
            except queue.Empty:
                continue
            if item is self._CLOSE_SENTINEL:
                self._closed = True
                self.close()
                raise StopIteration
            if item is self._ERROR_SENTINEL:
                assert self._error is not None
                error = self._error
                self.close()
                raise error
            return item

    def close(self) -> None:
        if self._closing.is_set():
            return
        self._closing.set()
        self._closed = True
        if self._loop.is_running():
            if self._channel is not None:
                future = asyncio.run_coroutine_threadsafe(self._channel.close(), self._loop)
                with contextlib.suppress(Exception):
                    future.result(timeout=5)
            self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join(timeout=5)

    # ------------------------------------------------------------------
    def _run_loop(self) -> None:
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_forever()
        finally:
            tasks = [task for task in asyncio.all_tasks(self._loop) if not task.done()]
            for task in tasks:
                task.cancel()
            with contextlib.suppress(Exception):
                if tasks:
                    self._loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
            self._loop.close()

    async def _open_channel(self) -> None:
        origin = os.getenv("HUROZO_FIREBASE_ORIGIN", "https://hurozo.com")
        referer = os.getenv("HUROZO_FIREBASE_REFERER", "https://hurozo.com/")

        inner_headers = {
            "Content-Type": "text/plain",
            "X-Goog-Api-Client": "gl-python/3 python-webchannel/0.1",
            "google-cloud-resource-prefix": self._options.database_path,
            "x-goog-request-params": self._options.request_params_header,
        }
        if self._options.app_id:
            inner_headers["X-Firebase-GMPID"] = self._options.app_id
        inner_headers.update(self._options.auth_headers)

        fetch_headers = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": os.getenv("HUROZO_FIREBASE_ACCEPT_LANGUAGE", "en-US,en;q=0.9"),
            "cache-control": "no-cache",
            "pragma": "no-cache",
            "origin": origin,
            "referer": referer,
            "user-agent": os.getenv(
                "HUROZO_FIREBASE_USER_AGENT",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
            ),
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "sec-fetch-storage-access": "active",
            "sec-ch-ua": os.getenv(
                "HUROZO_FIREBASE_SEC_CH_UA",
                '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
            ),
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": os.getenv("HUROZO_FIREBASE_SEC_CH_UA_PLATFORM", '"macOS"'),
            "x-browser-channel": "stable",
            "x-browser-copyright": "Copyright 2025 Google LLC. All rights reserved.",
            "x-browser-validation": os.getenv(
                "HUROZO_FIREBASE_BROWSER_VALIDATION",
                "jFliu1AvGMEE7cpr93SSytkZ8D4=",
            ),
            "x-browser-year": "2025",
            "x-client-data": os.getenv(
                "HUROZO_FIREBASE_CLIENT_DATA",
                "CJS2yQEIpLbJAQipncoBCNSHywEIlKHLAQiGoM0BCICEzwEIkIfPAQ==",
            ),
            "priority": "u=1, i",
        }

        channel_options = WebChannelOptions(
            message_url_params={"database": self._options.database_path},
            init_message_headers=inner_headers.copy(),
            message_headers=inner_headers,
            send_raw_json=True,
            encode_init_message_headers=True,
            http_session_id_param="gsessionid",
            client_protocol_header_required=True,
            fetch_headers=fetch_headers,
        )

        transport = create_web_channel_transport()
        channel = transport.create_web_channel(self._options.base_url(), channel_options)
        self._channel = channel
        channel.listen(EventType.MESSAGE, self._handle_message)
        channel.listen(EventType.ERROR, self._handle_error)
        channel.listen(EventType.CLOSE, self._handle_close)

        await channel.send(self._request)
        await channel.open()

    def _handle_message(self, event: Any) -> None:
        payload = getattr(event, "data", event)
        if payload is None:
            return
        self._queue.put(payload)

    def _handle_error(self, error: Exception) -> None:
        listen_error = self._to_listen_error(error)
        self._error = listen_error
        self._queue.put(self._ERROR_SENTINEL)

    def _handle_close(self, _payload: Any) -> None:
        self._queue.put(self._CLOSE_SENTINEL)

    def _to_listen_error(self, error: Exception) -> FirestoreListenError:
        if isinstance(error, FirestoreListenError):
            return error
        if isinstance(error, WebChannelError):
            status = error.status
            message = error.message or "Firestore listen stream failed"
            if status:
                message = f"{message} ({status})"
            return FirestoreListenError(message)
        return FirestoreListenError(str(error))


class FirebaseAuthError(RuntimeError):
    """Raised when Firebase authentication fails."""


def _timestamp_after(seconds: int) -> Optional[datetime]:
    if seconds <= 0:
        return None
    return datetime.now(timezone.utc) + timedelta(seconds=seconds)


def _decode_value(value: Dict[str, Any]) -> Any:
    if "nullValue" in value:
        return None
    if "booleanValue" in value:
        return bool(value["booleanValue"])
    if "integerValue" in value:
        return int(value["integerValue"])
    if "doubleValue" in value:
        return float(value["doubleValue"])
    if "stringValue" in value:
        return value["stringValue"]
    if "timestampValue" in value:
        return value["timestampValue"]
    if "arrayValue" in value:
        array = value["arrayValue"].get("values", [])
        return [_decode_value(item) for item in array]
    if "mapValue" in value:
        fields = value["mapValue"].get("fields", {})
        return {key: _decode_value(val) for key, val in fields.items()}
    if "referenceValue" in value:
        return value["referenceValue"]
    if "bytesValue" in value:
        return value["bytesValue"]
    return value


def _encode_value(value: Any) -> Dict[str, Any]:
    if value is None:
        return {"nullValue": None}
    if isinstance(value, bool):
        return {"booleanValue": value}
    if isinstance(value, int):
        return {"integerValue": str(value)}
    if isinstance(value, float):
        return {"doubleValue": value}
    if isinstance(value, str):
        return {"stringValue": value}
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return {"timestampValue": value.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")}
    if isinstance(value, (list, tuple)):
        return {"arrayValue": {"values": [_encode_value(item) for item in value]}}
    if isinstance(value, dict):
        return {"mapValue": {"fields": {key: _encode_value(val) for key, val in value.items()}}}
    return {"stringValue": str(value)}


def _encode_fields(mapping: Dict[str, Any]) -> Dict[str, Any]:
    return {key: _encode_value(val) for key, val in mapping.items()}


def _decode_fields(mapping: Dict[str, Any]) -> Dict[str, Any]:
    return {key: _decode_value(val) for key, val in mapping.items()}


@dataclass
class RemoteRequest:
    uuid: str
    inputs: Dict[str, Any]
    raw: Dict[str, Any]


class FirebaseRealtimeBridge:
    """Handle authentication and Firestore interactions for remote agents."""

    def __init__(
        self,
        *,
        api_key: str = HUROZO_FIREBASE_API_KEY,
        project_id: str = HUROZO_FIREBASE_PROJECT,
        database_id: str = HUROZO_FIREBASE_DATABASE,
        debug: bool = False,
    ) -> None:
        self.api_key = api_key
        self.project_id = project_id
        self.database_id = database_id
        self.debug = debug
        self.user_id: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self._access_token: Optional[str] = None
        self._access_token_expiry: float = 0.0
        self._session = requests.Session()
        self._resume_token: Optional[str] = None
        self._base_url: Optional[str] = None
        self._bearer_token: Optional[str] = None
        self._listen_agent_name: Optional[str] = None

    def _log(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        if not self.debug:
            return
        prefix = "[FirebaseRealtime]"
        if extra:
            try:
                payload = json.dumps(extra, default=str)
            except Exception:
                payload = str(extra)
            print(f"{prefix} {message} :: {payload}", flush=True)
        else:
            print(f"{prefix} {message}", flush=True)

    @property
    def _database_path(self) -> str:
        return f"projects/{self.project_id}/databases/{self.database_id}"

    @property
    def _documents_base(self) -> str:
        return f"https://firestore.googleapis.com/v1/{self._database_path}/documents"

    def bootstrap(self, base_url: str, bearer_token: str) -> None:
        self._base_url = base_url
        self._bearer_token = bearer_token
        custom_token = self._fetch_custom_token(base_url, bearer_token)
        self._sign_in_with_custom_token(custom_token)

    def _fetch_custom_token(self, base_url: str, bearer_token: str) -> str:
        headers = {"Authorization": f"Bearer {bearer_token}"}
        url = f"{base_url}/api/firebase_token"
        res = self._session.get(url, headers=headers, timeout=15)
        if not res.ok:
            raise FirebaseAuthError(f"Failed to fetch Firebase token ({res.status_code}): {res.text}")
        data = res.json() or {}
        token = data.get("token")
        if not token:
            raise FirebaseAuthError("Response missing custom token")
        return token

    def _sign_in_with_custom_token(self, custom_token: str) -> None:
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key={self.api_key}"
        payload = {"token": custom_token, "returnSecureToken": True}
        res = self._session.post(url, json=payload, timeout=20)
        if not res.ok:
            raise FirebaseAuthError(f"Firebase sign-in failed ({res.status_code}): {res.text}")
        data = res.json() or {}
        local_id = data.get("localId")
        id_token = data.get("idToken")
        if not local_id and id_token:
            local_id = self._extract_local_id(id_token)
        refresh_token = data.get("refreshToken")
        expires_in = int(data.get("expiresIn", "3600") or 3600)
        if not local_id:
            raise FirebaseAuthError("Firebase response missing user identifier")
        self.user_id = local_id
        self._refresh_token = refresh_token
        if refresh_token:
            self._access_token = None
            self._access_token_expiry = 0.0
            self._refresh_access_token()
        elif id_token:
            self._access_token = id_token
            self._access_token_expiry = time.time() + max(expires_in - 60, 60)
        else:
            raise FirebaseAuthError("Firebase response missing id token")

    def _refresh_access_token(self) -> None:
        if not self._refresh_token:
            # Fall back to minting a new custom token when the auth emulator does not return refresh tokens.
            self._reauthenticate_using_custom_token()
            return
        url = f"https://securetoken.googleapis.com/v1/token?key={self.api_key}"
        data = {"grant_type": "refresh_token", "refresh_token": self._refresh_token}
        res = self._session.post(url, data=data, timeout=20)
        if not res.ok:
            raise FirebaseAuthError(f"Refresh token failed ({res.status_code}): {res.text}")
        payload = res.json() or {}
        access_token = payload.get("access_token")
        expires_in = int(payload.get("expires_in", "3600"))
        refresh_token = payload.get("refresh_token")
        if not access_token:
            raise FirebaseAuthError("No access_token in refresh response")
        self._access_token = access_token
        self._access_token_expiry = time.time() + max(expires_in - 60, 60)
        if refresh_token:
            self._refresh_token = refresh_token

    def _ensure_access_token(self) -> str:
        if not self._access_token or time.time() >= self._access_token_expiry:
            if self._refresh_token:
                self._refresh_access_token()
            else:
                self._reauthenticate_using_custom_token()
        assert self._access_token is not None  # for type checkers
        return self._access_token

    def _reauthenticate_using_custom_token(self) -> None:
        if not self._base_url or not self._bearer_token:
            raise FirebaseAuthError("Cannot mint replacement Firebase token without bootstrap context")
        custom_token = self._fetch_custom_token(self._base_url, self._bearer_token)
        self._sign_in_with_custom_token(custom_token)

    @staticmethod
    def _extract_local_id(id_token: str) -> Optional[str]:
        parts = id_token.split('.')
        if len(parts) < 2:
            return None
        payload_b64 = parts[1]
        padding = '=' * (-len(payload_b64) % 4)
        try:
            decoded = base64.urlsafe_b64decode(payload_b64 + padding)
            payload = json.loads(decoded)
        except Exception:
            return None
        return payload.get("user_id") or payload.get("uid")

    def listen_remote_requests(
        self,
        agent_name: str,
        callback: Callable[[RemoteRequest], None],
        stop_check: Callable[[], bool],
    ) -> None:
        if not self.user_id:
            raise FirebaseAuthError("Not authenticated")
        self._listen_agent_name = agent_name
        parent = f"{self._database_path}/documents/users/{self.user_id}"
        backoff_seconds = 2.0
        target_id = 1
        while not stop_check():
            access_token = self._ensure_access_token()
            options = ListenClientOptions(
                project_id=self.project_id,
                database_id=self.database_id,
                auth_headers={"Authorization": f"Bearer {access_token}"},
                debug=self.debug,
            )
            listen_client = FirestoreListenClient(options=options)
            request = self._build_listen_request(parent, agent_name, target_id)
            stream: Optional[_FirestoreListenStream] = None
            try:
                stream = listen_client.listen(request, stop_check=stop_check)
                self._log("opening WebChannel listen stream", {"target_id": target_id})
                for payload in stream:
                    if stop_check():
                        return
                    self._handle_listen_payload(payload, callback)
                break
            except FirestoreListenError as exc:
                self._log("listen stream error", {"error": str(exc)})
                time.sleep(backoff_seconds)
                backoff_seconds = min(backoff_seconds * 2, 30.0)
            except Exception as exc:
                self._log("listen unexpected error", {"error": str(exc)})
                time.sleep(backoff_seconds)
                backoff_seconds = min(backoff_seconds * 2, 30.0)
            finally:
                if stream is not None:
                    stream.close()
        self._listen_agent_name = None

    def _build_listen_request(self, parent: str, agent_name: str, target_id: int) -> Dict[str, Any]:
        structured_query = {
            "from": [
                {
                    "collectionId": "remote_requests",
                }
            ],
            "where": {
                "fieldFilter": {
                    "field": {"fieldPath": "status"},
                    "op": "EQUAL",
                    "value": {"stringValue": "pending"},
                }
            },
            "orderBy": [
                {
                    "field": {"fieldPath": "createdAt"},
                    "direction": "ASCENDING",
                },
                {
                    "field": {"fieldPath": "__name__"},
                    "direction": "ASCENDING",
                },
            ],
        }
        add_target: Dict[str, Any] = {
            "targetId": target_id,
            "query": {
                "parent": parent,
                "structuredQuery": structured_query,
            },
        }
        if self._resume_token:
            add_target["resumeToken"] = self._resume_token
        return {
            "database": self._database_path,
            "addTarget": add_target,
        }

    def _handle_listen_payload(self, payload: Dict[str, Any], callback: Callable[[RemoteRequest], None]) -> None:
        if isinstance(payload, list):
            for item in payload:
                if isinstance(item, dict):
                    self._handle_listen_payload(item, callback)
                else:
                    self._log(
                        "listen payload not dict",
                        {"type": type(item).__name__, "payload": item},
                    )
            return
        if not isinstance(payload, dict):
            self._log(
                "listen payload not dict",
                {"type": type(payload).__name__, "payload": payload},
            )
            return
        target_change = payload.get("targetChange")
        if isinstance(target_change, dict):
            resume_token = target_change.get("resumeToken")
            if isinstance(resume_token, str) and resume_token:
                self._resume_token = resume_token
            cause = target_change.get("cause")
            if isinstance(cause, dict):
                message = cause.get("message") or json.dumps(cause)
                code = cause.get("code")
                detail = f"{message} (code={code})" if code is not None else message
                raise FirestoreListenError(detail)
            return

        document_change = payload.get("documentChange")
        if not isinstance(document_change, dict):
            return
        document = document_change.get("document")
        if not isinstance(document, dict):
            return
        fields_payload = document.get("fields") or {}
        if not isinstance(fields_payload, dict):
            fields_payload = {}
        fields = _decode_fields(fields_payload)
        status = fields.get("status")
        if isinstance(status, str) and status != "pending":
            return
        expected_agent = self._listen_agent_name
        agent_field = fields.get("agent")
        if expected_agent and isinstance(agent_field, str) and agent_field != expected_agent:
            return
        document_name = document.get("name", "")
        request_id = fields.get("uuid") or document_name.rsplit("/", 1)[-1]
        inputs = fields.get("inputs")
        if not isinstance(inputs, dict):
            inputs = {}
        callback(RemoteRequest(uuid=request_id, inputs=inputs, raw=fields))


    def update_remote_request(
        self,
        uuid: str,
        status: str,
        *,
        outputs: Optional[Dict[str, Any]] = None,
        error: Optional[Dict[str, Any]] = None,
    ) -> bool:
        if not self.user_id:
            raise FirebaseAuthError("Not authenticated")
        access_token = self._ensure_access_token()
        url = f"{self._documents_base}/users/{self.user_id}/remote_requests/{uuid}"
        now_dt = datetime.now(timezone.utc)
        fields: Dict[str, Any] = {
            "status": status,
            "updatedAt": now_dt,
        }
        if status == "in_progress":
            fields["startedAt"] = now_dt
            fields["error"] = None
        elif status == "done":
            fields["outputs"] = outputs if outputs is not None else {}
            fields["respondedAt"] = now_dt
            fields["error"] = None
        elif status == "error":
            fields["error"] = error if error is not None else {"message": "remote agent error"}
            fields["respondedAt"] = now_dt
            fields["outputs"] = None
        params: Iterable[tuple[str, str]] = [("currentDocument.exists", "true")]
        update_mask = sorted(fields.keys())
        params = list(params) + [("updateMask.fieldPaths", key) for key in update_mask]
        body = {"fields": _encode_fields(fields)}
        res = self._session.patch(url, headers={"Authorization": f"Bearer {access_token}"}, params=params, json=body, timeout=15)
        if res.status_code == 409:
            self._log("conflict updating request", {"uuid": uuid, "status": status, "body": res.text})
            return False
        if not res.ok:
            self._log("failed to update request", {"uuid": uuid, "status": status, "status_code": res.status_code, "body": res.text})
            res.raise_for_status()
        return True

    def create_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        if not self.user_id:
            raise FirebaseAuthError("Not authenticated")
        access_token = self._ensure_access_token()
        ttl_at = _timestamp_after(EVENT_TTL_SECONDS)
        fields = {
            "type": event_type,
            "payload": payload,
            "createdAt": datetime.now(timezone.utc),
            "delivered": False,
            "source": "remote_agent",
        }
        if ttl_at:
            fields["ttlAt"] = ttl_at
        body = {"fields": _encode_fields(fields)}
        url = f"{self._documents_base}/users/{self.user_id}/events"
        res = self._session.post(url, headers={"Authorization": f"Bearer {access_token}"}, json=body, timeout=15)
        if not res.ok:
            self._log("failed to create event", {"status": res.status_code, "body": res.text})
            res.raise_for_status()
