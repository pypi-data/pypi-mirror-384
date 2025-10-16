
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

from knowrithm_py.knowrithm.client import KnowrithmClient


class CompanyService:
    """
    Wrapper for the company routes located in ``app/blueprints/company/routes.py``.
    Includes helper utilities for CRUD operations, statistics, and cascading
    deletes.
    """

    def __init__(self, client: KnowrithmClient):
        self.client = client

    # ------------------------------------------------------------------ #
    # Creation
    # ------------------------------------------------------------------ #
    def create_company(
        self,
        payload: Dict[str, Any],
        *,
        logo_path: Optional[Path] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a company record. Accepts either JSON (default) or multipart form
        data when a logo file is provided.

        Endpoint:
            ``POST /v1/company`` - typically used internally (no auth requirement).
        """
        files = None
        handle = None
        if logo_path:
            handle = Path(logo_path).expanduser().open("rb")
            files = {"logo": (Path(logo_path).name, handle)}
        try:
            return self.client._make_request(
                "POST",
                "/company",
                data=payload,
                files=files,
                headers=headers,
            )
        finally:
            if handle:
                handle.close()

    # ------------------------------------------------------------------ #
    # Listing and retrieval
    # ------------------------------------------------------------------ #
    def list_companies(
        self,
        *,
        page: Optional[int] = None,
        per_page: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Super-admin only list endpoint.

        Endpoint:
            ``GET /v1/super-admin/company`` - requires JWT with super-admin role.
        """
        params: Dict[str, Any] = {}
        if page is not None:
            params["page"] = page
        if per_page is not None:
            params["per_page"] = per_page
        return self.client._make_request(
            "GET",
            "/super-admin/company",
            params=params or None,
            headers=headers,
        )

    def get_company(self, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Retrieve the authenticated company's profile.

        Endpoint:
            ``GET /v1/company`` - requires read scope or JWT.
        """
        return self.client._make_request("GET", "/company", headers=headers)

    def get_company_statistics(
        self,
        *,
        company_id: Optional[str] = None,
        days: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve lead statistics for the current or specified company.

        Endpoint:
            - ``GET /v1/company/statistics`` for current company.
            - ``GET /v1/company/<company_id>/statistics`` when a company ID is provided.
        """
        params: Dict[str, Any] = {}
        if days is not None:
            params["days"] = days
        endpoint = "/company/statistics"
        if company_id:
            endpoint = f"/company/{company_id}/statistics"
        return self.client._make_request("GET", endpoint, params=params or None, headers=headers)

    def list_deleted_companies(self, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        List soft-deleted companies.

        Endpoint:
            ``GET /v1/company/deleted`` - requires read scope.
        """
        return self.client._make_request("GET", "/company/deleted", headers=headers)

    # ------------------------------------------------------------------ #
    # Updates
    # ------------------------------------------------------------------ #
    def update_company(
        self,
        company_id: str,
        payload: Dict[str, Any],
        *,
        logo_path: Optional[Path] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Replace company details.

        Endpoint:
            ``PUT /v1/company/<company_id>`` - requires admin/super-admin access.
        """
        files = None
        handle = None
        if logo_path:
            handle = Path(logo_path).expanduser().open("rb")
            files = {"logo": (Path(logo_path).name, handle)}
        try:
            return self.client._make_request(
                "PUT",
                f"/company/{company_id}",
                data=payload,
                files=files,
                headers=headers,
            )
        finally:
            if handle:
                handle.close()

    def patch_company(
        self,
        company_id: str,
        payload: Dict[str, Any],
        *,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Partially update company metadata.

        Endpoint:
            ``PATCH /v1/company/<company_id>`` - super-admin only according to spec.
        """
        return self.client._make_request("PATCH", f"/company/{company_id}", data=payload, headers=headers)

    # ------------------------------------------------------------------ #
    # Deletion / restoration
    # ------------------------------------------------------------------ #
    def delete_company(self, company_id: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Soft-delete a company.

        Endpoint:
            ``DELETE /v1/company/<company_id>`` - requires write scope or JWT.
        """
        return self.client._make_request("DELETE", f"/company/{company_id}", headers=headers)

    def restore_company(self, company_id: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Restore a soft-deleted company.

        Endpoint:
            ``PATCH /v1/company/<company_id>/restore`` - same authentication as delete.
        """
        return self.client._make_request("PATCH", f"/company/{company_id}/restore", headers=headers)

    def cascade_delete_company(
        self,
        company_id: str,
        *,
        delete_related: Optional[bool] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Super-admin endpoint that cascades deletion across related data.

        Endpoint:
            ``DELETE /v1/company/<company_id>/cascade-delete``.
        """
        payload: Dict[str, Any] = {}
        if delete_related is not None:
            payload["delete_related"] = delete_related
        return self.client._make_request(
            "DELETE",
            f"/company/{company_id}/cascade-delete",
            data=payload or None,
            headers=headers,
        )

    def get_related_data_summary(
        self,
        company_id: str,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Inspect related data counts before deleting a company.

        Endpoint:
            ``GET /v1/company/<company_id>/related-data`` - super-admin only.
        """
        return self.client._make_request("GET", f"/company/{company_id}/related-data", headers=headers)

    def bulk_delete_companies(
        self,
        company_ids: Sequence[str],
        *,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Soft-delete multiple companies at once.

        Endpoint:
            ``DELETE /v1/company/bulk-delete`` - requires write scope.
        """
        payload = {"company_ids": list(company_ids)}
        return self.client._make_request(
            "DELETE",
            "/company/bulk-delete",
            data=payload,
            headers=headers,
        )

    def bulk_restore_companies(
        self,
        company_ids: Sequence[str],
        *,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Restore multiple companies.

        Endpoint:
            ``PATCH /v1/company/bulk-restore`` - requires write scope.
        """
        payload = {"company_ids": list(company_ids)}
        return self.client._make_request(
            "PATCH",
            "/company/bulk-restore",
            data=payload,
            headers=headers,
        )
