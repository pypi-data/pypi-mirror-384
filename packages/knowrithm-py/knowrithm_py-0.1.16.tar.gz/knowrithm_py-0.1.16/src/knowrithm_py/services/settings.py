from typing import Any, Dict, List, Optional

from knowrithm_py.knowrithm.client import KnowrithmClient


class SettingsService:
    """
    Wrapper for the routes defined in ``app/blueprints/settings/routes.py``.
    Enables management of LLM configuration records for companies and agents.
    """

    def __init__(self, client: KnowrithmClient):
        self.client = client

    def create_settings(
        self,
        llm_provider_id: str,
        llm_model_id: str,
        embedding_provider_id: str,
        embedding_model_id: str,
        *,
        agent_id: Optional[str] = None,
        llm_api_key: Optional[str] = None,
        llm_api_base_url: Optional[str] = None,
        llm_temperature: Optional[float] = None,
        llm_max_tokens: Optional[int] = None,
        llm_additional_params: Optional[Dict[str, Any]] = None,
        embedding_api_key: Optional[str] = None,
        embedding_api_base_url: Optional[str] = None,
        embedding_dimension: Optional[int] = None,
        embedding_additional_params: Optional[Dict[str, Any]] = None,
        widget_script_url: Optional[str] = None,
        widget_config: Optional[Dict[str, Any]] = None,
        is_default: Optional[bool] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Create an LLM settings record for a company or agent.

        Endpoint:
            ``POST /v1/settings`` - requires API key scope ``write`` or JWT.
        """
        payload: Dict[str, Any] = {
            "llm_provider_id": llm_provider_id,
            "llm_model_id": llm_model_id,
            "embedding_provider_id": embedding_provider_id,
            "embedding_model_id": embedding_model_id,
        }
        if agent_id is not None:
            payload["agent_id"] = agent_id
        if llm_api_key is not None:
            payload["llm_api_key"] = llm_api_key
        if llm_api_base_url is not None:
            payload["llm_api_base_url"] = llm_api_base_url
        if llm_temperature is not None:
            payload["llm_temperature"] = llm_temperature
        if llm_max_tokens is not None:
            payload["llm_max_tokens"] = llm_max_tokens
        if llm_additional_params is not None:
            payload["llm_additional_params"] = llm_additional_params
        if embedding_api_key is not None:
            payload["embedding_api_key"] = embedding_api_key
        if embedding_api_base_url is not None:
            payload["embedding_api_base_url"] = embedding_api_base_url
        if embedding_dimension is not None:
            payload["embedding_dimension"] = embedding_dimension
        if embedding_additional_params is not None:
            payload["embedding_additional_params"] = embedding_additional_params
        if widget_script_url is not None:
            payload["widget_script_url"] = widget_script_url
        if widget_config is not None:
            payload["widget_config"] = widget_config
        if is_default is not None:
            payload["is_default"] = is_default
        return self.client._make_request("POST", "/settings", data=payload, headers=headers)

    def create_settings_with_provider_names(
        self,
        llm_provider: str,
        llm_model: str,
        embedding_provider: str,
        embedding_model: str,
        *,
        agent_id: Optional[str] = None,
        llm_provider_id: Optional[str] = None,
        llm_model_id: Optional[str] = None,
        llm_api_key: Optional[str] = None,
        llm_api_base_url: Optional[str] = None,
        llm_temperature: Optional[float] = None,
        llm_max_tokens: Optional[int] = None,
        llm_additional_params: Optional[Dict[str, Any]] = None,
        embedding_provider_id: Optional[str] = None,
        embedding_model_id: Optional[str] = None,
        embedding_api_key: Optional[str] = None,
        embedding_api_base_url: Optional[str] = None,
        embedding_dimension: Optional[int] = None,
        embedding_additional_params: Optional[Dict[str, Any]] = None,
        widget_script_url: Optional[str] = None,
        widget_config: Optional[Dict[str, Any]] = None,
        is_default: Optional[bool] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Create an LLM settings record by referencing provider/model names.

        Endpoint:
            ``POST /v1/sdk/settings`` - requires API key scope ``write`` or JWT.
        """
        payload: Dict[str, Any] = {
            "llm_provider": llm_provider,
            "llm_model": llm_model,
            "embedding_provider": embedding_provider,
            "embedding_model": embedding_model,
        }
        if agent_id is not None:
            payload["agent_id"] = agent_id
        if llm_provider_id is not None:
            payload["llm_provider_id"] = llm_provider_id
        if llm_model_id is not None:
            payload["llm_model_id"] = llm_model_id
        if llm_api_key is not None:
            payload["llm_api_key"] = llm_api_key
        if llm_api_base_url is not None:
            payload["llm_api_base_url"] = llm_api_base_url
        if llm_temperature is not None:
            payload["llm_temperature"] = llm_temperature
        if llm_max_tokens is not None:
            payload["llm_max_tokens"] = llm_max_tokens
        if llm_additional_params is not None:
            payload["llm_additional_params"] = llm_additional_params
        if embedding_provider_id is not None:
            payload["embedding_provider_id"] = embedding_provider_id
        if embedding_model_id is not None:
            payload["embedding_model_id"] = embedding_model_id
        if embedding_api_key is not None:
            payload["embedding_api_key"] = embedding_api_key
        if embedding_api_base_url is not None:
            payload["embedding_api_base_url"] = embedding_api_base_url
        if embedding_dimension is not None:
            payload["embedding_dimension"] = embedding_dimension
        if embedding_additional_params is not None:
            payload["embedding_additional_params"] = embedding_additional_params
        if widget_script_url is not None:
            payload["widget_script_url"] = widget_script_url
        if widget_config is not None:
            payload["widget_config"] = widget_config
        if is_default is not None:
            payload["is_default"] = is_default

        return self.client._make_request("POST", "/sdk/settings", data=payload, headers=headers)

    def update_settings(
        self,
        settings_id: str,
        *,
        llm_provider_id: Optional[str] = None,
        llm_model_id: Optional[str] = None,
        embedding_provider_id: Optional[str] = None,
        embedding_model_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        llm_api_key: Optional[str] = None,
        llm_api_base_url: Optional[str] = None,
        llm_temperature: Optional[float] = None,
        llm_max_tokens: Optional[int] = None,
        llm_additional_params: Optional[Dict[str, Any]] = None,
        embedding_api_key: Optional[str] = None,
        embedding_api_base_url: Optional[str] = None,
        embedding_dimension: Optional[int] = None,
        embedding_additional_params: Optional[Dict[str, Any]] = None,
        widget_script_url: Optional[str] = None,
        widget_config: Optional[Dict[str, Any]] = None,
        is_default: Optional[bool] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Update a stored LLM settings record.

        Endpoint:
            ``PUT /v1/settings/<settings_id>`` - requires write scope.
        """
        payload: Dict[str, Any] = {}
        if llm_provider_id is not None:
            payload["llm_provider_id"] = llm_provider_id
        if llm_model_id is not None:
            payload["llm_model_id"] = llm_model_id
        if embedding_provider_id is not None:
            payload["embedding_provider_id"] = embedding_provider_id
        if embedding_model_id is not None:
            payload["embedding_model_id"] = embedding_model_id
        if agent_id is not None:
            payload["agent_id"] = agent_id
        if llm_api_key is not None:
            payload["llm_api_key"] = llm_api_key
        if llm_api_base_url is not None:
            payload["llm_api_base_url"] = llm_api_base_url
        if llm_temperature is not None:
            payload["llm_temperature"] = llm_temperature
        if llm_max_tokens is not None:
            payload["llm_max_tokens"] = llm_max_tokens
        if llm_additional_params is not None:
            payload["llm_additional_params"] = llm_additional_params
        if embedding_api_key is not None:
            payload["embedding_api_key"] = embedding_api_key
        if embedding_api_base_url is not None:
            payload["embedding_api_base_url"] = embedding_api_base_url
        if embedding_dimension is not None:
            payload["embedding_dimension"] = embedding_dimension
        if embedding_additional_params is not None:
            payload["embedding_additional_params"] = embedding_additional_params
        if widget_script_url is not None:
            payload["widget_script_url"] = widget_script_url
        if widget_config is not None:
            payload["widget_config"] = widget_config
        if is_default is not None:
            payload["is_default"] = is_default
        return self.client._make_request(
            "PUT",
            f"/settings/{settings_id}",
            data=payload,
            headers=headers,
        )

    def get_settings(self, settings_id: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Fetch a specific LLM settings record.

        Endpoint:
            ``GET /v1/settings/<settings_id>`` - requires read scope or JWT.
        """
        return self.client._make_request("GET", f"/settings/{settings_id}", headers=headers)

    def list_company_settings(
        self,
        company_id: str,
        *,
        headers: Optional[Dict[str, str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        List all LLM settings associated with a company.

        Endpoint:
            ``GET /v1/settings/company/<company_id>`` - requires read scope.
        """
        return self.client._make_request(
            "GET",
            f"/settings/company/{company_id}",
            headers=headers,
        )

    def list_agent_settings(
        self,
        agent_id: str,
        *,
        headers: Optional[Dict[str, str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        List LLM settings linked to a specific agent.

        Endpoint:
            ``GET /v1/settings/agent/<agent_id>`` - requires read scope.
        """
        return self.client._make_request(
            "GET",
            f"/settings/agent/{agent_id}",
            headers=headers,
        )

    def delete_settings(
        self,
        settings_id: str,
        *,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Permanently remove an LLM settings record.

        Endpoint:
            ``DELETE /v1/settings/<settings_id>`` - requires write scope.
        """
        return self.client._make_request("DELETE", f"/settings/{settings_id}", headers=headers)

    def test_settings(
        self,
        settings_id: str,
        overrides: Optional[Dict[str, Any]] = None,
        *,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Validate and test an LLM settings record. Optional overrides can be
        supplied for runtime validation (e.g., alternate credentials).

        Endpoint:
            ``POST /v1/settings/test/<settings_id>`` - requires write scope.
        """
        return self.client._make_request(
            "POST",
            f"/settings/test/{settings_id}",
            data=overrides,
            headers=headers,
        )

    def list_settings_providers(
        self,
        *,
        headers: Optional[Dict[str, str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve providers alongside settings context (e.g., defaults).

        Endpoint:
            ``GET /v1/settings/providers`` - requires read scope.
        """
        return self.client._make_request("GET", "/settings/providers", headers=headers)

    def seed_settings_providers(
        self,
        overrides: Optional[Dict[str, Any]] = None,
        *,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Seed the system with default provider/model definitions.

        Endpoint:
            ``POST /v1/settings/providers/seed`` - requires write scope.
        """
        return self.client._make_request(
            "POST",
            "/settings/providers/seed",
            data=overrides,
            headers=headers,
        )


class ProviderService:
    """
    Wraps provider and provider model CRUD endpoints exposed under
    ``app/blueprints/settings/routes.py``.
    """

    def __init__(self, client: KnowrithmClient):
        self.client = client

    def create_provider(
        self,
        name: str,
        type: str,
        *,
        description: Optional[str] = None,
        api_base_url: Optional[str] = None,
        pricing: Optional[Dict[str, Any]] = None,
        status: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new provider definition.

        Endpoint:
            ``POST /v1/providers`` - requires API key scope ``write`` or JWT.
        """
        payload: Dict[str, Any] = {"name": name, "type": type}
        if description is not None:
            payload["description"] = description
        if api_base_url is not None:
            payload["api_base_url"] = api_base_url
        if pricing is not None:
            payload["pricing"] = pricing
        if status is not None:
            payload["status"] = status
        return self.client._make_request("POST", "/providers", data=payload, headers=headers)

    def update_provider(
        self,
        provider_id: str,
        *,
        name: Optional[str] = None,
        type: Optional[str] = None,
        description: Optional[str] = None,
        api_base_url: Optional[str] = None,
        pricing: Optional[Dict[str, Any]] = None,
        status: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Update metadata for an existing provider.

        Endpoint:
            ``PUT /v1/providers/<provider_id>`` - requires write scope.
        """
        payload: Dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if type is not None:
            payload["type"] = type
        if description is not None:
            payload["description"] = description
        if api_base_url is not None:
            payload["api_base_url"] = api_base_url
        if pricing is not None:
            payload["pricing"] = pricing
        if status is not None:
            payload["status"] = status
        return self.client._make_request(
            "PUT",
            f"/providers/{provider_id}",
            data=payload,
            headers=headers,
        )

    def delete_provider(self, provider_id: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Delete a provider record.

        Endpoint:
            ``DELETE /v1/providers/<provider_id>`` - requires write scope.
        """
        return self.client._make_request("DELETE", f"/providers/{provider_id}", headers=headers)

    def list_providers(
        self,
        *,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        List provider records. Optional query params are forwarded for filters.

        Endpoint:
            ``GET /v1/providers`` - requires read scope.
        """
        return self.client._make_request("GET", "/providers", params=params, headers=headers)

    def get_provider(self, provider_id: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Retrieve details for a specific provider.

        Endpoint:
            ``GET /v1/providers/<provider_id>`` - requires read scope.
        """
        return self.client._make_request("GET", f"/providers/{provider_id}", headers=headers)

    def bulk_import_providers(
        self,
        payload: Dict[str, Any],
        *,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Bulk import provider and model definitions using a structured payload.

        Endpoint:
            ``POST /v1/providers/bulk-import`` - requires write scope.
        """
        return self.client._make_request("POST", "/providers/bulk-import", data=payload, headers=headers)

    def create_model(
        self,
        provider_id: str,
        name: str,
        type: str,
        *,
        provider_model_id: Optional[str] = None,
        context_window: Optional[int] = None,
        input_price: Optional[float] = None,
        output_price: Optional[float] = None,
        currency: Optional[str] = None,
        embedding_dimension: Optional[int] = None,
        status: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a model entry under a provider.

        Endpoint:
            ``POST /v1/providers/<provider_id>/models`` - requires write scope.
        """
        payload: Dict[str, Any] = {"name": name, "type": type}
        if provider_model_id is not None:
            payload["provider_model_id"] = provider_model_id
        if context_window is not None:
            payload["context_window"] = context_window
        if input_price is not None:
            payload["input_price"] = input_price
        if output_price is not None:
            payload["output_price"] = output_price
        if currency is not None:
            payload["currency"] = currency
        if embedding_dimension is not None:
            payload["embedding_dimension"] = embedding_dimension
        if status is not None:
            payload["status"] = status
        return self.client._make_request(
            "POST",
            f"/providers/{provider_id}/models",
            data=payload,
            headers=headers,
        )

    def update_model(
        self,
        provider_id: str,
        model_id: str,
        *,
        name: Optional[str] = None,
        type: Optional[str] = None,
        provider_model_id: Optional[str] = None,
        context_window: Optional[int] = None,
        input_price: Optional[float] = None,
        output_price: Optional[float] = None,
        currency: Optional[str] = None,
        embedding_dimension: Optional[int] = None,
        status: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Update a provider model definition.

        Endpoint:
            ``PUT /v1/providers/<provider_id>/models/<model_id>`` - requires write scope.
        """
        payload: Dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if type is not None:
            payload["type"] = type
        if provider_model_id is not None:
            payload["provider_model_id"] = provider_model_id
        if context_window is not None:
            payload["context_window"] = context_window
        if input_price is not None:
            payload["input_price"] = input_price
        if output_price is not None:
            payload["output_price"] = output_price
        if currency is not None:
            payload["currency"] = currency
        if embedding_dimension is not None:
            payload["embedding_dimension"] = embedding_dimension
        if status is not None:
            payload["status"] = status
        return self.client._make_request(
            "PUT",
            f"/providers/{provider_id}/models/{model_id}",
            data=payload,
            headers=headers,
        )

    def delete_model(
        self,
        provider_id: str,
        model_id: str,
        *,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Delete a provider model record.

        Endpoint:
            ``DELETE /v1/providers/<provider_id>/models/<model_id>`` - requires write scope.
        """
        return self.client._make_request(
            "DELETE",
            f"/providers/{provider_id}/models/{model_id}",
            headers=headers,
        )

    def list_models(
        self,
        provider_id: str,
        *,
        headers: Optional[Dict[str, str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        List models associated with a provider.

        Endpoint:
            ``GET /v1/providers/<provider_id>/models`` - requires read scope.
        """
        return self.client._make_request(
            "GET",
            f"/providers/{provider_id}/models",
            headers=headers,
        )

    def get_model(
        self,
        provider_id: str,
        model_id: str,
        *,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve a single provider model definition.

        Endpoint:
            ``GET /v1/providers/<provider_id>/models/<model_id>`` - requires read scope.
        """
        return self.client._make_request(
            "GET",
            f"/providers/{provider_id}/models/{model_id}",
            headers=headers,
        )
