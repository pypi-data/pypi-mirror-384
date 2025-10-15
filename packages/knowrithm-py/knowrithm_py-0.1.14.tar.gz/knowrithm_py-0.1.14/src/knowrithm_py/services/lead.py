
from typing import Any, Dict, Optional

from knowrithm_py.knowrithm.client import KnowrithmClient


class LeadService:
    """
    Client abstraction for the lead endpoints located in
    ``app/blueprints/lead/routes.py``.
    """

    def __init__(self, client: KnowrithmClient):
        self.client = client

    def register_lead(
        self,
        payload: Dict[str, Any],
        *,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Public lead registration used by the widget. The endpoint issues a JWT
        that can be used for subsequent authenticated widget calls.

        Endpoint:
            ``POST /v1/lead/register`` - no authentication required.
        """
        return self.client._make_request("POST", "/lead/register", data=payload, headers=headers)

    def create_lead(
        self,
        payload: Dict[str, Any],
        *,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a lead via authenticated API call.

        Endpoint:
            ``POST /v1/lead`` - requires write scope or JWT.
        """
        return self.client._make_request("POST", "/lead", data=payload, headers=headers)

    def get_lead(self, lead_id: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Fetch an individual lead.

        Endpoint:
            ``GET /v1/lead/<lead_id>`` - requires read scope or JWT.
        """
        return self.client._make_request("GET", f"/lead/{lead_id}", headers=headers)

    def list_company_leads(
        self,
        *,
        page: Optional[int] = None,
        per_page: Optional[int] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Paginated list of leads for the authenticated company.

        Endpoint:
            ``GET /v1/lead/company`` - requires read scope or JWT.
        """
        params: Dict[str, Any] = {}
        if page is not None:
            params["page"] = page
        if per_page is not None:
            params["per_page"] = per_page
        if status is not None:
            params["status"] = status
        if search is not None:
            params["search"] = search
        return self.client._make_request("GET", "/lead/company", params=params or None, headers=headers)

    def update_lead(
        self,
        lead_id: str,
        payload: Dict[str, Any],
        *,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Update mutable lead attributes.

        Endpoint:
            ``PUT /v1/lead/<lead_id>`` - requires write scope or JWT.
        """
        return self.client._make_request("PUT", f"/lead/{lead_id}", data=payload, headers=headers)

    def delete_lead(self, lead_id: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Soft-delete a lead.

        Endpoint:
            ``DELETE /v1/lead/<lead_id>`` - requires write scope or JWT.
        """
        return self.client._make_request("DELETE", f"/lead/{lead_id}", headers=headers)
