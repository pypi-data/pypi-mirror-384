
from typing import Any, Dict, Optional

from knowrithm_py.knowrithm.client import KnowrithmClient


class AnalyticsService:
    """
    Convenience layer for analytics and search endpoints described under
    ``app/blueprints/dashboard/routes.py``.
    """

    def __init__(self, client: KnowrithmClient):
        self.client = client

    def get_dashboard_overview(
        self,
        *,
        company_id: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Fetch high-level analytics for documents, conversations, leads, and agents.

        Endpoint:
            ``GET /v1/analytic/dashboard`` - requires read scope or JWT.
        """
        params: Dict[str, Any] = {}
        if company_id is not None:
            params["company_id"] = company_id
        return self.client._make_request("GET", "/analytic/dashboard", params=params or None, headers=headers)

    def get_agent_analytics(
        self,
        agent_id: str,
        *,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve detailed analytics for a single agent over an optional time range.

        Endpoint:
            ``GET /v1/analytic/agent/<agent_id>`` - requires read scope or JWT.
        """
        params: Dict[str, Any] = {}
        if start_date is not None:
            params["start_date"] = start_date
        if end_date is not None:
            params["end_date"] = end_date
        return self.client._make_request(
            "GET",
            f"/analytic/agent/{agent_id}",
            params=params or None,
            headers=headers,
        )

    def get_agent_performance_comparison(
        self,
        agent_id: str,
        *,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Compare agent metrics against company averages.

        Endpoint:
            ``GET /v1/analytic/agent/<agent_id>/performance-comparison``.
        """
        params: Dict[str, Any] = {}
        if start_date is not None:
            params["start_date"] = start_date
        if end_date is not None:
            params["end_date"] = end_date
        return self.client._make_request(
            "GET",
            f"/analytic/agent/{agent_id}/performance-comparison",
            params=params or None,
            headers=headers,
        )

    def get_conversation_analytics(
        self,
        conversation_id: str,
        *,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve analytics baked for a specific conversation.

        Endpoint:
            ``GET /v1/analytic/conversation/<conversation_id>``.
        """
        return self.client._make_request(
            "GET",
            f"/analytic/conversation/{conversation_id}",
            headers=headers,
        )

    def get_lead_analytics(
        self,
        *,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        company_id: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Fetch lead analytics for the company.

        Endpoint:
            ``GET /v1/analytic/leads`` - super admins can override company via query param.
        """
        params: Dict[str, Any] = {}
        if start_date is not None:
            params["start_date"] = start_date
        if end_date is not None:
            params["end_date"] = end_date
        if company_id is not None:
            params["company_id"] = company_id
        return self.client._make_request("GET", "/analytic/leads", params=params or None, headers=headers)

    def get_usage_metrics(
        self,
        *,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve platform usage metrics such as API calls and agent activity.

        Endpoint:
            ``GET /v1/analytic/usage`` - requires read scope.
        """
        params: Dict[str, Any] = {}
        if start_date is not None:
            params["start_date"] = start_date
        if end_date is not None:
            params["end_date"] = end_date
        return self.client._make_request("GET", "/analytic/usage", params=params or None, headers=headers)

    def search_documents(
        self,
        query: str,
        agent_id: str,
        *,
        limit: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Perform semantic document search.

        Endpoint:
            ``POST /v1/search/document`` - requires write scope or JWT.
        """
        payload: Dict[str, Any] = {"query": query, "agent_id": agent_id}
        if limit is not None:
            payload["limit"] = limit
        return self.client._make_request("POST", "/search/document", data=payload, headers=headers)

    def search_database(
        self,
        query: str,
        *,
        connection_id: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Perform semantic database search.

        Endpoint:
            ``POST /v1/search/database`` - requires write scope or JWT.
        """
        payload: Dict[str, Any] = {"query": query}
        if connection_id is not None:
            payload["connection_id"] = connection_id
        return self.client._make_request("POST", "/search/database", data=payload, headers=headers)

    def trigger_system_metric_collection(
        self,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Kick off asynchronous system metric collection.

        Endpoint:
            ``POST /v1/system-metric`` - requires write scope.
        """
        return self.client._make_request("POST", "/system-metric", headers=headers)

    def export_analytics(
        self,
        export_type: str,
        export_format: str,
        *,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Export analytics data in JSON or CSV format.

        Endpoint:
            ``POST /v1/analytic/export`` - requires read scope.

        Payload:
            ``type`` (conversations | leads | agents | usage),
            ``format`` (json | csv),
            optional ``start_date`` and ``end_date``.
        """
        payload: Dict[str, Any] = {"type": export_type, "format": export_format}
        if start_date is not None:
            payload["start_date"] = start_date
        if end_date is not None:
            payload["end_date"] = end_date
        return self.client._make_request("POST", "/analytic/export", data=payload, headers=headers)

    def health_check(self, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Perform a basic service availability check.

        Endpoint:
            ``GET /health`` - public.
        """
        return self.client._make_request("GET", "/health", headers=headers)


