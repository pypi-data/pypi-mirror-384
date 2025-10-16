
import json
from dataclasses import dataclass
from typing import Any, Dict, Iterator, List, Optional, Sequence, Set, Union

import requests

from knowrithm_py.dataclass.error import KnowrithmAPIError
from knowrithm_py.knowrithm.client import KnowrithmClient


@dataclass
class ChatEvent:
    """Represents a single message emitted through the chat SSE stream."""

    event: str
    data: Any
    id: Optional[str] = None
    retry: Optional[int] = None
    raw: Optional[str] = None


class MessageStream:
    """
    Iterable wrapper around a streaming chat response.

    Iterating over the instance yields :class:`ChatEvent` objects until the
    server closes the stream or ``close()`` is invoked.
    """

    def __init__(
        self,
        *,
        metadata: Dict[str, Any],
        iterator: Iterator[ChatEvent],
        response: requests.Response,
        stream_url: str,
        accepted_events: Optional[Set[str]] = None,
    ) -> None:
        self._metadata = metadata
        self._iterator = iterator
        self._response = response
        self.stream_url = stream_url
        self.accepted_events = accepted_events

    @property
    def metadata(self) -> Dict[str, Any]:
        """Initial metadata associated with the stream (chat response or custom payload)."""
        return self._metadata

    @property
    def task_id(self) -> Optional[str]:
        """Convenience accessor for the Celery task identifier."""
        return self._metadata.get("task_id")

    @property
    def message_id(self) -> Optional[str]:
        """Convenience accessor for the queued message identifier."""
        return self._metadata.get("message_id")

    def close(self) -> None:
        """Close the underlying HTTP response, terminating the stream."""
        if self._response is not None:
            self._response.close()
            self._response = None

    def __iter__(self) -> "MessageStream":
        return self

    def __next__(self) -> ChatEvent:
        try:
            return next(self._iterator)
        except StopIteration:
            self.close()
            raise

    def events(self) -> Iterator[ChatEvent]:
        """Return an iterator over chat events (alias for ``iter(self)``)."""
        return iter(self)

    def __enter__(self) -> "MessageStream":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()


def _parse_sse_event(lines: Sequence[str], *, parse_json: bool) -> Optional[ChatEvent]:
    """
    Convert raw Server-Sent Event lines into a ChatEvent.

    Args:
        lines: The buffered SSE field lines between blank separators.
        parse_json: Attempt to ``json.loads`` the ``data`` payload when True.
    """
    if not lines:
        return None

    event_name = "message"
    data_lines: List[str] = []
    event_id: Optional[str] = None
    retry: Optional[int] = None

    for raw_line in lines:
        if not raw_line or raw_line.startswith(":"):
            # Comments (prefixed with ":") and empty lines are ignored by spec.
            continue
        field, _, value = raw_line.partition(":")
        value = value.lstrip(" ")

        if field == "event" and value:
            event_name = value
        elif field == "data":
            data_lines.append(value)
        elif field == "id" and value:
            event_id = value
        elif field == "retry" and value:
            try:
                retry = int(value)
            except ValueError:
                # Ignore malformed retry values; they are advisory only.
                retry = None

    raw_data = "\n".join(data_lines)
    payload: Any = raw_data
    if parse_json and raw_data:
        try:
            payload = json.loads(raw_data)
        except (TypeError, ValueError):
            # Keep the raw string payload if JSON decoding fails.
            payload = raw_data

    return ChatEvent(
        event=event_name or "message",
        data=payload,
        id=event_id,
        retry=retry,
        raw=raw_data if raw_data else None,
    )


def _iter_sse_events(
    response: requests.Response,
    *,
    allowed_events: Optional[Set[str]],
    parse_json: bool,
) -> Iterator[ChatEvent]:
    """
    Yield ChatEvent objects from a streaming HTTP response.

    The response is closed automatically when the generator exhausts.
    """
    buffer: List[str] = []
    try:
        for raw_line in response.iter_lines(decode_unicode=True):
            if raw_line is None:
                continue

            line = raw_line.rstrip("\r")
            if line == "":
                event = _parse_sse_event(buffer, parse_json=parse_json)
                buffer.clear()
                if event is None:
                    continue
                if allowed_events and event.event not in allowed_events:
                    continue
                yield event
                continue

            buffer.append(line)

        # Flush any trailing event if the stream closed without a blank line.
        if buffer:
            event = _parse_sse_event(buffer, parse_json=parse_json)
            buffer.clear()
            if event and (not allowed_events or event.event in allowed_events):
                yield event
    finally:
        response.close()


class ConversationService:
    """
    Wrapper for conversation endpoints. Handles creation, listing, restoration,
    and bulk message management in accordance with
    ``app/blueprints/conversation/routes.py``.
    """

    def __init__(self, client: KnowrithmClient):
        self.client = client

    def create_conversation(
        self,
        agent_id: str,
        *,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        max_context_length: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a conversation scoped to the authenticated entity.

        Endpoint:
            ``POST /v1/conversation`` - requires ``write`` scope or JWT.
        """
        payload: Dict[str, Any] = {"agent_id": agent_id}
        if title is not None:
            payload["title"] = title
        if metadata is not None:
            payload["metadata"] = metadata
        if max_context_length is not None:
            payload["max_context_length"] = max_context_length
        return self.client._make_request("POST", "/conversation", data=payload, headers=headers)

    def list_conversations(
        self,
        *,
        page: Optional[int] = None,
        per_page: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        List active company conversations.

        Endpoint:
            ``GET /v1/conversation`` - requires ``read`` scope or JWT.
        """
        params: Dict[str, Any] = {}
        if page is not None:
            params["page"] = page
        if per_page is not None:
            params["per_page"] = per_page
        return self.client._make_request("GET", "/conversation", params=params or None, headers=headers)

    def list_conversations_for_entity(
        self,
        *,
        page: Optional[int] = None,
        per_page: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        List conversations for the currently authenticated entity (user or lead).

        Endpoint:
            ``GET /v1/conversation/entity`` - requires ``read`` scope or JWT.
        """
        params: Dict[str, Any] = {}
        if page is not None:
            params["page"] = page
        if per_page is not None:
            params["per_page"] = per_page
        return self.client._make_request("GET", "/conversation/entity", params=params or None, headers=headers)

    def list_conversations_by_entity(
        self,
        entity_id: str,
        *,
        entity_type: Optional[str] = None,
        status: Optional[str] = None,
        page: Optional[int] = None,
        per_page: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve conversations for the provided entity identifier.

        Endpoint:
            ``GET /v1/conversation/entity/<entity_id>`` - requires read scope or JWT.
        """
        if not entity_id:
            raise ValueError("list_conversations_by_entity requires a non-empty entity_id.")

        params: Dict[str, Any] = {}
        if entity_type is not None:
            params["entity_type"] = entity_type
        if status is not None:
            params["status"] = status
        if page is not None:
            params["page"] = page
        if per_page is not None:
            params["per_page"] = per_page
        return self.client._make_request(
            "GET",
            f"/conversation/entity/{entity_id}",
            params=params or None,
            headers=headers,
        )

    def list_conversations_by_agent(
        self,
        agent_id: str,
        *,
        status: Optional[str] = None,
        page: Optional[int] = None,
        per_page: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve conversations handled by the specified agent.

        Endpoint:
            ``GET /v1/conversation/agent/<agent_id>`` - requires read scope or JWT.
        """
        if not agent_id:
            raise ValueError("list_conversations_by_agent requires a non-empty agent_id.")

        params: Dict[str, Any] = {}
        if status is not None:
            params["status"] = status
        if page is not None:
            params["page"] = page
        if per_page is not None:
            params["per_page"] = per_page
        return self.client._make_request(
            "GET",
            f"/conversation/agent/{agent_id}",
            params=params or None,
            headers=headers,
        )

    def list_deleted_conversations(self, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        List soft-deleted conversations.

        Endpoint:
            ``GET /v1/conversation/deleted`` - requires read scope.
        """
        return self.client._make_request("GET", "/conversation/deleted", headers=headers)

    def list_conversation_messages(
        self,
        conversation_id: str,
        *,
        page: Optional[int] = None,
        per_page: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve paginated messages for a conversation.

        Endpoint:
            ``GET /v1/conversation/<conversation_id>/messages`` - requires read scope.
        """
        params: Dict[str, Any] = {}
        if page is not None:
            params["page"] = page
        if per_page is not None:
            params["per_page"] = per_page
        return self.client._make_request(
            "GET",
            f"/conversation/{conversation_id}/messages",
            params=params or None,
            headers=headers,
        )

    def delete_conversation(self, conversation_id: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Soft-delete a conversation and its messages.

        Endpoint:
            ``DELETE /v1/conversation/<conversation_id>`` - requires write scope.
        """
        return self.client._make_request("DELETE", f"/conversation/{conversation_id}", headers=headers)

    def delete_conversation_messages(
        self,
        conversation_id: str,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Soft-delete every message in a conversation.

        Endpoint:
            ``DELETE /v1/conversation/<conversation_id>/messages`` - requires write scope.
        """
        return self.client._make_request(
            "DELETE",
            f"/conversation/{conversation_id}/messages",
            headers=headers,
        )

    def restore_conversation(self, conversation_id: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Restore a soft-deleted conversation.

        Endpoint:
            ``PATCH /v1/conversation/<conversation_id>/restore`` - requires write scope.
        """
        return self.client._make_request(
            "PATCH",
            f"/conversation/{conversation_id}/restore",
            headers=headers,
        )

    def restore_all_messages(
        self,
        conversation_id: str,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Restore every message within a conversation in a single call.

        Endpoint:
            ``PATCH /v1/conversation/<conversation_id>/message/restore-all`` - requires write scope.
        """
        return self.client._make_request(
            "PATCH",
            f"/conversation/{conversation_id}/message/restore-all",
            headers=headers,
        )


class MessageService:
    """
    Conversation message helper mirroring message-specific endpoints.
    """

    def __init__(self, client: KnowrithmClient):
        self.client = client

    def send_message(
        self,
        conversation_id: str,
        message: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        stream: bool = False,
        stream_url: Optional[str] = None,
        stream_timeout: Optional[float] = None,
        event_types: Optional[Sequence[str]] = None,
        raw_events: bool = False,
    ) -> Union[Dict[str, Any], MessageStream]:
        """
        Send a message and optionally subscribe to the streaming AI reply.

        Endpoint:
            ``POST /v1/conversation/<conversation_id>/chat`` - requires write scope or JWT.

        Args:
            conversation_id: Target conversation identifier.
            message: Plain-text prompt to send to the assistant.
            headers: Optional override headers (e.g. Authorization bearer token).
            stream: When True, return a :class:`MessageStream` yielding :class:`ChatEvent` objects.
            stream_url: Optional absolute or relative SSE endpoint override. Required unless the
                client's configuration defines ``stream_path_template`` or the API response
                returns a ``stream_url`` field.
            stream_timeout: Optional timeout (seconds) for establishing/consuming the stream.
            event_types: Optional iterable of event names to emit (others are dropped).
            raw_events: When True, do not attempt JSON decoding of ``data`` payloads.

        Returns:
            The JSON response from the chat endpoint when ``stream`` is False, otherwise
            a :class:`MessageStream` handle for iterating over real-time events.
        """
        payload = {"message": message}
        response_payload = self.client._make_request(
            "POST",
            f"/conversation/{conversation_id}/chat",
            data=payload,
            headers=headers,
        )

        if not stream:
            return response_payload

        return self.stream_conversation_messages(
            conversation_id,
            headers=headers,
            stream_url=stream_url,
            stream_timeout=stream_timeout,
            event_types=event_types,
            raw_events=raw_events,
            _initial_metadata=response_payload,
        )

    def delete_message(self, message_id: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Soft-delete a single message.

        Endpoint:
            ``DELETE /v1/message/<message_id>`` - requires write scope.
        """
        return self.client._make_request("DELETE", f"/message/{message_id}", headers=headers)

    def restore_message(self, message_id: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Restore a soft-deleted message.

        Endpoint:
            ``PATCH /v1/message/<message_id>/restore`` - requires write scope.
        """
        return self.client._make_request("PATCH", f"/message/{message_id}/restore", headers=headers)

    def list_deleted_messages(self, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        List soft-deleted messages for the company.

        Endpoint:
            ``GET /v1/message/deleted`` - requires read scope.
        """
        return self.client._make_request("GET", "/message/deleted", headers=headers)

    def stream_conversation_messages(
        self,
        conversation_id: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        stream_url: Optional[str] = None,
        stream_timeout: Optional[float] = None,
        event_types: Optional[Sequence[str]] = None,
        raw_events: bool = False,
        _initial_metadata: Optional[Dict[str, Any]] = None,
    ) -> MessageStream:
        """
        Open a Server-Sent Events stream for a conversation.

        Endpoint:
            ``GET /v1/conversation/<conversation_id>/messages/stream`` - requires read scope.

        Args:
            conversation_id: Target conversation identifier.
            headers: Optional override headers (e.g. Authorization bearer token).
            stream_url: Optional absolute/relative SSE endpoint override.
            stream_timeout: Optional timeout (seconds) for establishing/consuming the stream.
            event_types: Optional iterable of event names to emit (others are dropped).
            raw_events: When True, do not attempt JSON decoding of ``data`` payloads.

        Returns:
            A :class:`MessageStream` that yields :class:`ChatEvent` objects.
        """
        resolved_url = self._resolve_stream_url(
            conversation_id,
            _initial_metadata,
            stream_url_override=stream_url,
        )
        if resolved_url is None:
            raise KnowrithmAPIError(
                "Streaming is not configured. Provide 'stream_url' or set "
                "KnowrithmConfig.stream_path_template/stream_base_url."
            )

        allowed_events = set(event_types) if event_types else None
        metadata: Dict[str, Any] = {"conversation_id": conversation_id}
        if _initial_metadata:
            metadata.update(_initial_metadata)

        return self._open_stream(
            stream_url=resolved_url,
            initial_payload=metadata,
            headers=headers,
            timeout_override=stream_timeout,
            allowed_events=allowed_events,
            parse_json=not raw_events,
        )

    def _resolve_stream_url(
        self,
        conversation_id: str,
        response_payload: Optional[Dict[str, Any]],
        *,
        stream_url_override: Optional[str] = None,
    ) -> Optional[str]:
        """
        Determine the SSE endpoint for the conversation message stream.
        """
        if stream_url_override:
            return self._normalize_stream_url(stream_url_override)

        payload = response_payload or {}

        for key in ("stream_url", "sse_url", "socket_url"):
            candidate = payload.get(key)
            if candidate:
                return self._normalize_stream_url(str(candidate))

        config = getattr(self.client, "config", None)
        template = getattr(config, "stream_path_template", None) if config else None
        if not template:
            return None

        tokens = {
            "conversation_id": conversation_id,
            "message_id": payload.get("message_id"),
            "task_id": payload.get("task_id"),
        }

        try:
            formatted_path = template.format(**{k: v for k, v in tokens.items() if v is not None})
        except KeyError:
            # Fallback: substitute missing tokens with empty strings for convenience.
            safe_tokens = {k: (v if v is not None else "") for k, v in tokens.items()}
            try:
                formatted_path = template.format(**safe_tokens)
            except KeyError as exc:
                raise ValueError(f"Invalid stream_path_template placeholder: {exc}") from exc

        return self._normalize_stream_url(formatted_path)

    def _normalize_stream_url(
        self,
        path_or_url: str,
    ) -> str:
        """
        Convert a potentially relative stream path into an absolute URL.
        """
        if path_or_url.startswith(("http://", "https://")):
            return path_or_url
        if path_or_url.startswith(("ws://", "wss://")):
            raise ValueError("WebSocket URLs are not supported; provide an SSE http(s) endpoint.")

        # Allow passing a chat response field that already includes the base URL.
        if path_or_url.startswith("stream://"):
            raise ValueError("The 'stream://' schema is not supported; provide http(s) URLs.")

        base_override = getattr(self.client.config, "stream_base_url", None)
        base_url = base_override or self.client.base_url

        if path_or_url.startswith("/"):
            return f"{base_url.rstrip('/')}{path_or_url}"
        return f"{base_url.rstrip('/')}/{path_or_url}"

    def _open_stream(
        self,
        *,
        stream_url: str,
        initial_payload: Optional[Dict[str, Any]],
        headers: Optional[Dict[str, str]],
        timeout_override: Optional[float],
        allowed_events: Optional[Set[str]],
        parse_json: bool,
    ) -> MessageStream:
        """
        Initiate the SSE connection and wrap it in a MessageStream helper.
        """
        request_headers: Dict[str, str] = {}
        if headers:
            request_headers.update(headers)
        request_headers.setdefault("Accept", "text/event-stream")
        request_headers.pop("Content-Type", None)

        timeout = (
            timeout_override
            if timeout_override is not None
            else getattr(self.client.config, "stream_timeout", None)
        )
        if timeout is None:
            timeout = self.client.config.timeout

        try:
            response = self.client._session.get(
                stream_url,
                headers=request_headers or None,
                stream=True,
                timeout=timeout,
                verify=self.client.config.verify_ssl,
            )
        except requests.exceptions.RequestException as exc:
            raise KnowrithmAPIError(f"Failed to open chat stream: {exc}") from exc

        if response.status_code >= 400:
            error_data: Dict[str, Any]
            try:
                error_data = response.json()
            except ValueError:
                error_data = {"detail": response.text}
            response.close()
            base_message = error_data.get(
                "detail",
                error_data.get("message", f"HTTP {response.status_code}"),
            )
            message = f"{base_message} (GET {stream_url})"
            raise KnowrithmAPIError(
                message=message,
                status_code=response.status_code,
                response_data=error_data,
                error_code=error_data.get("error_code"),
            )

        iterator = _iter_sse_events(
            response,
            allowed_events=allowed_events,
            parse_json=parse_json,
        )

        metadata = dict(initial_payload) if initial_payload else {}
        metadata.setdefault("stream_url", stream_url)

        return MessageStream(
            metadata=metadata,
            iterator=iterator,
            response=response,
            stream_url=stream_url,
            accepted_events=allowed_events,
        )
