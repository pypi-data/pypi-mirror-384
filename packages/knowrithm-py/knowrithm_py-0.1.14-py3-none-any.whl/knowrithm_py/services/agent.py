
from typing import Any, Dict, List, Optional

from knowrithm_py.knowrithm.client import KnowrithmClient


class AgentService:
    """
    Thin wrapper around ``app/blueprints/agent/routes.py`` endpoints. Provides a
    typed, well documented interface for creating and managing Knowrithm agents.
    """

    def __init__(self, client: KnowrithmClient):
        self.client = client

    def create_agent(
        self,
        payload: Dict[str, Any],
        *,
        settings: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new agent and provision dedicated LLM settings.

        Endpoint:
            ``POST /v1/agent`` - requires API key scope ``write`` or JWT with equivalent rights.

        Args:
            payload: Must include ``name`` plus either provider/model IDs or, when combined with
                ``settings``, the required identifiers or names.
            settings: Optional dictionary. When it contains provider/model *names* (for example
                ``llm_provider``), the SDK will call ``POST /v1/sdk/agent`` automatically. When it
                only contains ID-based keys, those values are merged into ``payload`` and the
                standard endpoint is used.

        Raises:
            ValueError: If required identifiers are missing.
        """
        if settings:
            has_provider_names = all(
                settings.get(field)
                for field in ("llm_provider", "llm_model", "embedding_provider", "embedding_model")
            )
            if has_provider_names:
                return self.create_agent_with_provider_names(
                    payload=payload, settings=settings, headers=headers
                )

            allowed_setting_keys = {
                "llm_provider_id",
                "llm_model_id",
                "llm_api_key",
                "llm_api_base_url",
                "llm_temperature",
                "llm_max_tokens",
                "llm_additional_params",
                "embedding_provider_id",
                "embedding_model_id",
                "embedding_api_key",
                "embedding_api_base_url",
                "embedding_dimension",
                "embedding_additional_params",
                "widget_script_url",
                "widget_config",
            }
            payload = dict(payload)
            for key in allowed_setting_keys:
                if key in settings and settings[key] is not None:
                    payload[key] = settings[key]

        required_fields = (
            "name",
            "llm_provider_id",
            "llm_model_id",
            "embedding_provider_id",
            "embedding_model_id",
        )
        missing_fields = [field for field in required_fields if not payload.get(field)]
        if missing_fields:
            raise ValueError(
                "create_agent requires the following fields so that LLM settings can "
                f"be provisioned automatically: {', '.join(missing_fields)}."
            )

        return self.client._make_request("POST", "/agent", data=payload, headers=headers)

    def create_agent_with_provider_names(
        self,
        payload: Optional[Dict[str, Any]] = None,
        *,
        settings: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new agent by supplying provider and model names instead of IDs.

        Endpoint:
            ``POST /v1/sdk/agent`` - requires API key scope ``write`` or JWT with equivalent rights.

        Args:
            payload: Base agent fields (for example ``name``, ``description``, ``languages``).
            settings: Required settings dictionary containing provider/model names and optional
                overrides. The dictionary supports the keys accepted by
                ``POST /v1/sdk/settings`` (for example ``llm_provider``, ``llm_model``,
                ``embedding_provider``, ``embedding_model``, and optional API credentials).

        Raises:
            ValueError: If ``name`` or any of the required provider/model values are missing.
        """
        request_payload: Dict[str, Any] = {}
        if payload:
            request_payload.update(payload)

        settings_payload: Dict[str, Any] = {}
        if settings:
            allowed_setting_keys = {
                "llm_provider",
                "llm_provider_id",
                "llm_model",
                "llm_model_id",
                "llm_api_key",
                "llm_api_base_url",
                "llm_temperature",
                "llm_max_tokens",
                "llm_additional_params",
                "embedding_provider",
                "embedding_provider_id",
                "embedding_model",
                "embedding_model_id",
                "embedding_api_key",
                "embedding_api_base_url",
                "embedding_dimension",
                "embedding_additional_params",
                "widget_script_url",
                "widget_config",
                "is_default",
            }
            for key in allowed_setting_keys:
                if key in settings and settings[key] is not None:
                    settings_payload[key] = settings[key]

        required_settings_fields = (
            "llm_provider",
            "llm_model",
            "embedding_provider",
            "embedding_model",
        )
        missing_settings = [field for field in required_settings_fields if not settings_payload.get(field)]
        if missing_settings:
            raise ValueError(
                "create_agent_with_provider_names requires settings to include "
                f"{', '.join(missing_settings)}."
            )

        if not request_payload.get("name"):
            raise ValueError("create_agent_with_provider_names requires the agent payload to include 'name'.")

        request_payload["settings"] = settings_payload

        return self.client._make_request("POST", "/sdk/agent", data=request_payload, headers=headers)

    def get_agent(self, agent_id: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Retrieve agent details by identifier (public endpoint).

        Endpoint:
            ``GET /v1/agent/<agent_id>`` - no authentication required.
        """
        return self.client._make_request("GET", f"/agent/{agent_id}", headers=headers)

    def list_agents(
        self,
        *,
        company_id: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        page: Optional[int] = None,
        per_page: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        List agents that belong to the current company or to a specific company
        for super admins.

        Endpoint:
            ``GET /v1/agent`` - requires ``read`` scope or a JWT.

        Query parameters:
            ``company_id`` (super admins), ``status``, ``search``, ``page``, ``per_page``.
        """
        params: Dict[str, Any] = {}
        if company_id is not None:
            params["company_id"] = company_id
        if status is not None:
            params["status"] = status
        if search is not None:
            params["search"] = search
        if page is not None:
            params["page"] = page
        if per_page is not None:
            params["per_page"] = per_page
        return self.client._make_request("GET", "/agent", params=params or None, headers=headers)

    def update_agent(
        self,
        agent_id: str,
        payload: Dict[str, Any],
        *,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Replace an agent's metadata and associated LLM settings.

        Endpoint:
            ``PUT /v1/agent/<agent_id>`` - requires ``write`` scope or JWT.
        """
        return self.client._make_request("PUT", f"/agent/{agent_id}", data=payload, headers=headers)

    def delete_agent(self, agent_id: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Soft-delete an agent (must have no active conversations).

        Endpoint:
            ``DELETE /v1/agent/<agent_id>`` - requires agent write permissions.
        """
        return self.client._make_request("DELETE", f"/agent/{agent_id}", headers=headers)

    def restore_agent(self, agent_id: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Restore a soft-deleted agent.

        Endpoint:
            ``PATCH /v1/agent/<agent_id>/restore`` - requires write scope.
        """
        return self.client._make_request("PATCH", f"/agent/{agent_id}/restore", headers=headers)

    def get_embed_code(self, agent_id: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Retrieve the embed code that powers the public chat widget for this agent.

        Endpoint:
            ``GET /v1/agent/<agent_id>/embed-code`` - requires read scope or JWT.
        """
        return self.client._make_request("GET", f"/agent/{agent_id}/embed-code", headers=headers)

    def test_agent(
        self,
        agent_id: str,
        *,
        query: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Run a test prompt against the agent.

        Endpoint:
            ``POST /v1/agent/<agent_id>/test`` - requires read scope or JWT.

        Args:
            query: Optional free-form prompt; omitted defaults to a sample prompt on the server.
        """
        payload: Optional[Dict[str, Any]] = None
        if query is not None:
            payload = {"query": query}
        return self.client._make_request(
            "POST",
            f"/agent/{agent_id}/test",
            data=payload,
            headers=headers,
        )

    def get_agent_stats(self, agent_id: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Retrieve aggregate statistics for an agent.

        Endpoint:
            ``GET /v1/agent/<agent_id>/stats`` - requires read scope or JWT.
        """
        return self.client._make_request("GET", f"/agent/{agent_id}/stats", headers=headers)

    def clone_agent(
        self,
        agent_id: str,
        *,
        name: Optional[str] = None,
        llm_settings_id: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Duplicate an agent configuration.

        Endpoint:
            ``POST /v1/agent/<agent_id>/clone`` - requires write scope.

        Payload options:
            ``name`` for the new agent; ``llm_settings_id`` to override the copied settings.
        """
        payload: Dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if llm_settings_id is not None:
            payload["llm_settings_id"] = llm_settings_id
        return self.client._make_request("POST", f"/agent/{agent_id}/clone", data=payload or None, headers=headers)

    def fetch_widget_script(self, headers: Optional[Dict[str, str]] = None) -> str:
        """
        Download the public widget JavaScript bundle.

        Endpoint:
            ``GET /widget.js`` - no authentication required.

        Returns:
            Raw JavaScript text as delivered by the API.
        """
        response = self.client._make_request("GET", "/widget.js", headers=headers)
        if isinstance(response, bytes):
            return response.decode("utf-8")
        if isinstance(response, str):
            return response
        raise TypeError("Expected widget.js to return a JavaScript string, received JSON payload instead.")

    def render_test_page(
        self,
        body_html: str,
        *,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Request the internal widget test page.

        Endpoint:
            ``POST /test`` - intended for internal QA flows; no authentication.

        Payload:
            ``body`` containing an HTML snippet.
        """
        payload = {"body": body_html}
        return self.client._make_request("POST", "/test", data=payload, headers=headers)
