
from typing import Any, Dict, List, Optional

from knowrithm_py.knowrithm.client import KnowrithmClient


class DatabaseService:
    """
    Helper around ``app/blueprints/database/routes.py`` endpoints. The methods in
    this class provide typed signatures and detailed descriptions so you can
    manage database connections, metadata, and semantic resources directly from
    Python.
    """

    def __init__(self, client: KnowrithmClient):
        self.client = client

    # ------------------------------------------------------------------ #
    # Connection lifecycle
    # ------------------------------------------------------------------ #
    def create_connection(
        self,
        name: str,
        url: str,
        database_type: str,
        agent_id: str,
        *,
        connection_params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Create and immediately test a database connection.

        Endpoint:
            ``POST /v1/database-connection`` - requires API key scope ``write``
            or a JWT with matching permissions.

        Payload:
            - ``name`` (required)
            - ``url`` (required - SQLAlchemy connection string)
            - ``database_type`` (required, e.g. ``postgres`` or ``mysql``)
            - ``agent_id`` (required, UUID string)
            - ``connection_params`` (optional dict with provider-specific flags)

        Args:
            name: Friendly connection name displayed in the dashboard.
            url: SQL connection string.
            database_type: Backend type identifier.
            agent_id: Agent UUID that owns this data source.
            connection_params: Extra driver configuration such as SSL details.
            headers: Optional header overrides (for JWT based auth flows).

        Returns:
            JSON payload containing connection metadata and validation results.
        """
        payload: Dict[str, Any] = {
            "name": name,
            "url": url,
            "database_type": database_type,
            "agent_id": agent_id,
        }
        if connection_params is not None:
            payload["connection_params"] = connection_params
        return self.client._make_request("POST", "/database-connection", data=payload, headers=headers)

    def list_connections(
        self,
        *,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        List database connections associated with the authenticated entity.

        Endpoint:
            ``GET /v1/database-connection`` - requires ``read`` scope or JWT.

        Args:
            headers: Optional header overrides.
            params: Optional raw query parameters forwarded to the API for future
                filters (e.g., pagination or filtering by agent/company).

        Returns:
            List of database connection records.
        """
        return self.client._make_request("GET", "/database-connection", params=params, headers=headers)

    def get_connection(self, connection_id: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Retrieve metadata for a single connection.

        Endpoint:
            ``GET /v1/database-connection/<connection_id>`` - requires read access.

        Args:
            connection_id: UUID of the connection.
            headers: Optional header overrides.

        Returns:
            Connection metadata including stored configuration.
        """
        return self.client._make_request("GET", f"/database-connection/{connection_id}", headers=headers)

    def update_connection(
        self,
        connection_id: str,
        *,
        name: Optional[str] = None,
        url: Optional[str] = None,
        database_type: Optional[str] = None,
        connection_params: Optional[Dict[str, Any]] = None,
        agent_id: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Replace all stored fields for a connection (PUT semantics).

        Endpoint:
            ``PUT /v1/database-connection/<connection_id>`` - requires write scope.

        Args:
            connection_id: UUID for the target connection.
            name: Replacement connection name.
            url: Replacement connection string.
            database_type: Replacement backend type.
            connection_params: Replacement driver configuration object.
            agent_id: Optionally reassign to a different agent.
            headers: Optional header overrides.

        Returns:
            Updated connection payload.
        """
        payload: Dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if url is not None:
            payload["url"] = url
        if database_type is not None:
            payload["database_type"] = database_type
        if connection_params is not None:
            payload["connection_params"] = connection_params
        if agent_id is not None:
            payload["agent_id"] = agent_id
        return self.client._make_request(
            "PUT",
            f"/database-connection/{connection_id}",
            data=payload,
            headers=headers,
        )

    def patch_connection(
        self,
        connection_id: str,
        updates: Dict[str, Any],
        *,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Apply a partial update to a connection.

        Endpoint:
            ``PATCH /v1/database-connection/<connection_id>`` - requires write scope.

        Args:
            connection_id: UUID for the target connection.
            updates: Dictionary containing a subset of valid connection fields.
            headers: Optional header overrides.

        Returns:
            Updated connection payload.
        """
        return self.client._make_request(
            "PATCH",
            f"/database-connection/{connection_id}",
            data=updates,
            headers=headers,
        )

    def delete_connection(self, connection_id: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Soft-delete a connection and all derived metadata.

        Endpoint:
            ``DELETE /v1/database-connection/<connection_id>`` - requires write scope.

        Args:
            connection_id: UUID for the target connection.
            headers: Optional header overrides.

        Returns:
            Confirmation payload including deletion metadata.
        """
        return self.client._make_request("DELETE", f"/database-connection/{connection_id}", headers=headers)

    def restore_connection(self, connection_id: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Restore a previously soft-deleted connection.

        Endpoint:
            ``PATCH /v1/database-connection/<connection_id>/restore`` - requires write scope.

        Args:
            connection_id: UUID for the target connection.
            headers: Optional header overrides.

        Returns:
            Restored connection payload.
        """
        return self.client._make_request(
            "PATCH",
            f"/database-connection/{connection_id}/restore",
            headers=headers,
        )

    def list_deleted_connections(self, headers: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """
        Fetch soft-deleted connections. Useful for internal restore tooling.

        Endpoint:
            ``GET /v1/database-connection/deleted`` - requires read scope.

        Args:
            headers: Optional header overrides.

        Returns:
            List of deleted connection records.
        """
        return self.client._make_request("GET", "/database-connection/deleted", headers=headers)

    # ------------------------------------------------------------------ #
    # Connection diagnostics
    # ------------------------------------------------------------------ #
    def test_connection(self, connection_id: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Revalidate a stored connection.

        Endpoint:
            ``POST /v1/database-connection/<connection_id>/test`` - requires write scope.

        Args:
            connection_id: UUID for the target connection.
            headers: Optional header overrides.

        Returns:
            JSON payload with connectivity test results.
        """
        return self.client._make_request(
            "POST",
            f"/database-connection/{connection_id}/test",
            headers=headers,
        )

    def analyze_connection(self, connection_id: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Kick off semantic analysis for a single connection.

        Endpoint:
            ``POST /v1/database-connection/<connection_id>/analyze`` - requires write scope.

        Args:
            connection_id: UUID for the target connection.
            headers: Optional header overrides.

        Returns:
            Task or status payload indicating analysis progress.
        """
        return self.client._make_request(
            "POST",
            f"/database-connection/{connection_id}/analyze",
            headers=headers,
        )

    def analyze_multiple_connections(
        self,
        payload: Optional[Dict[str, Any]] = None,
        *,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Batch analyze multiple connections.

        Endpoint:
            ``POST /v1/database-connection/analyze`` - requires write scope.

        Args:
            payload: Optional filters or specific connection IDs as defined by the
                backend implementation.
            headers: Optional header overrides.

        Returns:
            Analysis dispatch response.
        """
        return self.client._make_request(
            "POST",
            "/database-connection/analyze",
            data=payload,
            headers=headers,
        )

    # ------------------------------------------------------------------ #
    # Table metadata
    # ------------------------------------------------------------------ #
    def list_tables(
        self,
        connection_id: str,
        *,
        headers: Optional[Dict[str, str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        List tables that belong to the supplied connection.

        Endpoint:
            ``GET /v1/database-connection/<connection_id>/table`` - requires read scope.

        Args:
            connection_id: UUID for the target connection.
            headers: Optional header overrides.

        Returns:
            List of table metadata dictionaries.
        """
        return self.client._make_request(
            "GET",
            f"/database-connection/{connection_id}/table",
            headers=headers,
        )

    def get_table(self, table_id: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Retrieve metadata for a single table.

        Endpoint:
            ``GET /v1/database-connection/table/<table_id>`` - requires read scope.

        Args:
            table_id: Metadata table identifier.
            headers: Optional header overrides.

        Returns:
            Table metadata entry.
        """
        return self.client._make_request(
            "GET",
            f"/database-connection/table/{table_id}",
            headers=headers,
        )

    def delete_table(self, table_id: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Soft-delete a specific table metadata record.

        Endpoint:
            ``DELETE /v1/database-connection/table/<table_id>`` - requires write scope.

        Args:
            table_id: Metadata table identifier.
            headers: Optional header overrides.

        Returns:
            Confirmation payload.
        """
        return self.client._make_request(
            "DELETE",
            f"/database-connection/table/{table_id}",
            headers=headers,
        )

    def delete_tables_for_connection(
        self,
        connection_id: str,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Soft-delete all table metadata entries for a connection.

        Endpoint:
            ``DELETE /v1/database-connection/<connection_id>/table`` - requires write scope.

        Args:
            connection_id: UUID for the target connection.
            headers: Optional header overrides.

        Returns:
            Confirmation payload.
        """
        return self.client._make_request(
            "DELETE",
            f"/database-connection/{connection_id}/table",
            headers=headers,
        )

    def restore_table(self, table_id: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Restore a previously deleted table metadata entry.

        Endpoint:
            ``PATCH /v1/database-connection/table/<table_id>/restore`` - requires write scope.

        Args:
            table_id: Metadata table identifier.
            headers: Optional header overrides.

        Returns:
            Restored table payload.
        """
        return self.client._make_request(
            "PATCH",
            f"/database-connection/table/{table_id}/restore",
            headers=headers,
        )

    def list_deleted_tables(self, headers: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """
        List deleted table metadata records.

        Endpoint:
            ``GET /v1/database-connection/table/deleted`` - requires read scope.

        Args:
            headers: Optional header overrides.

        Returns:
            List of deleted table metadata dictionaries.
        """
        return self.client._make_request("GET", "/database-connection/table/deleted", headers=headers)

    # ------------------------------------------------------------------ #
    # Semantic resources and tooling
    # ------------------------------------------------------------------ #
    def get_semantic_snapshot(self, connection_id: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Fetch the stored semantic snapshot for a connection.

        Endpoint:
            ``GET /v1/database-connection/<connection_id>/semantic-snapshot`` - read scope.
        """
        return self.client._make_request(
            "GET",
            f"/database-connection/{connection_id}/semantic-snapshot",
            headers=headers,
        )

    def get_knowledge_graph(self, connection_id: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Retrieve the semantic knowledge graph JSON payload.

        Endpoint:
            ``GET /v1/database-connection/<connection_id>/knowledge-graph`` - read scope.
        """
        return self.client._make_request(
            "GET",
            f"/database-connection/{connection_id}/knowledge-graph",
            headers=headers,
        )

    def get_sample_queries(self, connection_id: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Fetch generated SQL sample queries for a connection.

        Endpoint:
            ``GET /v1/database-connection/<connection_id>/sample-queries`` - read scope.
        """
        return self.client._make_request(
            "GET",
            f"/database-connection/{connection_id}/sample-queries",
            headers=headers,
        )

    def text_to_sql(
        self,
        connection_id: str,
        question: str,
        *,
        execute: Optional[bool] = None,
        result_limit: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Generate (and optionally execute) SQL from natural language.

        Endpoint:
            ``POST /v1/database-connection/<connection_id>/text-to-sql`` - read scope.

        Payload:
            - ``question`` (required)
            - ``execute`` (optional boolean flag indicating execution)
            - ``result_limit`` (optional integer)

        Args:
            connection_id: UUID of the connection to target.
            question: Natural language prompt to convert into SQL.
            execute: Whether to execute the SQL on the source database.
            result_limit: Optional maximum number of rows when executing.
            headers: Optional header overrides.

        Returns:
            Response payload containing generated SQL and execution results.
        """
        payload: Dict[str, Any] = {"question": question}
        if execute is not None:
            payload["execute"] = execute
        if result_limit is not None:
            payload["result_limit"] = result_limit
        return self.client._make_request(
            "POST",
            f"/database-connection/{connection_id}/text-to-sql",
            data=payload,
            headers=headers,
        )

    def export_connection(
        self,
        connection_id: str,
        *,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Export the contents of a connection into the document ingestion pipeline.

        Endpoint:
            ``POST /v1/database-connection/export`` - requires write scope.

        Payload:
            ``connection_id`` (UUID string).

        Args:
            connection_id: UUID to export.
            headers: Optional header overrides.

        Returns:
            Export job metadata.
        """
        payload = {"connection_id": connection_id}
        return self.client._make_request(
            "POST",
            "/database-connection/export",
            data=payload,
            headers=headers,
        )

        
