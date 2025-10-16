
from typing import Any, Dict, List, Optional

from knowrithm_py.knowrithm.client import KnowrithmClient


class AdminService:
    """
    High-level wrapper for the administrative routes described in
    ``app/blueprints/admin/routes.py``. Use these helpers to manage users,
    system metrics, configuration, and impersonation flows.
    """

    def __init__(self, client: KnowrithmClient):
        self.client = client

    def list_users(
        self,
        *,
        company_id: Optional[str] = None,
        page: Optional[int] = None,
        per_page: Optional[int] = None,
        status: Optional[str] = None,
        role: Optional[str] = None,
        email_verified: Optional[bool] = None,
        two_factor_enabled: Optional[bool] = None,
        search: Optional[str] = None,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None,
        last_login_after: Optional[str] = None,
        last_login_before: Optional[str] = None,
        never_logged_in: Optional[bool] = None,
        locked: Optional[bool] = None,
        high_login_attempts: Optional[bool] = None,
        timezone: Optional[str] = None,
        language: Optional[str] = None,
        include_deleted: Optional[bool] = None,
        only_deleted: Optional[bool] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        List users with extensive filtering support.

        Endpoint:
            - ``GET /v1/admin/user`` for company admins.
            - ``GET /v1/super-admin/company/<company_id>/user`` when ``company_id`` is supplied.

        Authentication:
            ``X-API-Key`` + ``X-API-Secret`` with ``admin`` scope, or
            ``Authorization: Bearer <JWT>`` for admin / super-admin roles.

        Returns:
            Paginated response that includes user records and pagination metadata.
        """
        params: Dict[str, Any] = {}
        if page is not None:
            params["page"] = page
        if per_page is not None:
            params["per_page"] = per_page
        if status is not None:
            params["status"] = status
        if role is not None:
            params["role"] = role
        if email_verified is not None:
            params["email_verified"] = email_verified
        if two_factor_enabled is not None:
            params["two_factor_enabled"] = two_factor_enabled
        if search is not None:
            params["search"] = search
        if created_after is not None:
            params["created_after"] = created_after
        if created_before is not None:
            params["created_before"] = created_before
        if last_login_after is not None:
            params["last_login_after"] = last_login_after
        if last_login_before is not None:
            params["last_login_before"] = last_login_before
        if never_logged_in is not None:
            params["never_logged_in"] = never_logged_in
        if locked is not None:
            params["locked"] = locked
        if high_login_attempts is not None:
            params["high_login_attempts"] = high_login_attempts
        if timezone is not None:
            params["timezone"] = timezone
        if language is not None:
            params["language"] = language
        if include_deleted is not None:
            params["include_deleted"] = include_deleted
        if only_deleted is not None:
            params["only_deleted"] = only_deleted
        if sort_by is not None:
            params["sort_by"] = sort_by
        if sort_order is not None:
            params["sort_order"] = sort_order

        endpoint = "/admin/user"
        if company_id:
            endpoint = f"/super-admin/company/{company_id}/user"
        return self.client._make_request("GET", endpoint, params=params or None, headers=headers)

    def get_user(self, user_id: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Fetch a single user scoped to the authenticated company.

        Endpoint:
            ``GET /v1/admin/user/<user_id>``

        Returns:
            User record for the supplied identifier.
        """
        return self.client._make_request("GET", f"/admin/user/{user_id}", headers=headers)

    def get_company_system_metrics(
        self,
        *,
        company_id: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve the latest system metrics for the active company or a specific one.

        Endpoint:
            - ``GET /v1/admin/system-metric`` for company context.
            - ``GET /v1/super-admin/company/<company_id>/system-metric`` when ``company_id`` provided.

        Returns:
            Metrics payload with usage, latency, and availability figures.
        """
        endpoint = "/admin/system-metric"
        if company_id:
            endpoint = f"/super-admin/company/{company_id}/system-metric"
        return self.client._make_request("GET", endpoint, headers=headers)

    def get_audit_logs(
        self,
        *,
        entity_type: Optional[str] = None,
        event_type: Optional[str] = None,
        risk_level: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        List audit log entries for compliance reporting.

        Endpoint:
            ``GET /v1/audit-log`` - requires API keys with ``admin`` scope.

        Args follow the documented query parameters (entity type, event type,
        risk level and pagination).
        """
        params: Dict[str, Any] = {}
        if entity_type is not None:
            params["entity_type"] = entity_type
        if event_type is not None:
            params["event_type"] = event_type
        if risk_level is not None:
            params["risk_level"] = risk_level
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        return self.client._make_request("GET", "/audit-log", params=params or None, headers=headers)

    def get_system_configuration(self, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Read system configuration values.

        Endpoint:
            ``GET /v1/config`` - requires admin scope.

        Returns:
            Dictionary of configuration keys and values (sensitive values hidden from non super-admins).
        """
        return self.client._make_request("GET", "/config", headers=headers)

    def upsert_system_configuration(
        self,
        config_key: str,
        config_value: Any,
        *,
        config_type: Optional[str] = None,
        description: Optional[str] = None,
        is_sensitive: Optional[bool] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Create or update a configuration entry.

        Endpoint:
            ``PATCH /v1/config`` - requires admin scope.

        Payload mirrors the README documentation.
        """
        payload: Dict[str, Any] = {
            "config_key": config_key,
            "config_value": config_value,
        }
        if config_type is not None:
            payload["config_type"] = config_type
        if description is not None:
            payload["description"] = description
        if is_sensitive is not None:
            payload["is_sensitive"] = is_sensitive
        return self.client._make_request("PATCH", "/config", data=payload, headers=headers)

    def force_password_reset(self, user_id: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Force a password reset for the specified user and send a notification email.

        Endpoint:
            ``POST /v1/user/<user_id>/force-password-reset`` - requires admin scope.
        """
        return self.client._make_request(
            "POST",
            f"/user/{user_id}/force-password-reset",
            headers=headers,
        )

    def impersonate_user(self, user_id: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Start an impersonation session as a super admin.

        Endpoint:
            ``POST /v1/user/<user_id>/impersonate`` - super-admin only.
        """
        return self.client._make_request("POST", f"/user/{user_id}/impersonate", headers=headers)

    def update_user_status(
        self,
        user_id: str,
        status: str,
        *,
        reason: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Change a user's account status.

        Endpoint:
            ``PATCH /v1/user/<user_id>/status`` - requires admin scope.

        Payload matches the README specification.
        """
        payload: Dict[str, Any] = {"status": status}
        if reason is not None:
            payload["reason"] = reason
        return self.client._make_request("PATCH", f"/user/{user_id}/status", data=payload, headers=headers)

    def update_user_role(
        self,
        user_id: str,
        role: str,
        *,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Update a user's role (super-admins only).

        Endpoint:
            ``PATCH /v1/user/<user_id>/role`` - requires super-admin privileges.
        """
        payload = {"role": role}
        return self.client._make_request("PATCH", f"/user/{user_id}/role", data=payload, headers=headers)


