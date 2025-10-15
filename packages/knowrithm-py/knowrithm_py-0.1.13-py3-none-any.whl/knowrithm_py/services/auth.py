
from typing import Any, Dict, Optional

from knowrithm_py.knowrithm.client import KnowrithmClient


class AuthService:
    """
    Handles the authentication routes defined in ``app/blueprints/auth/routes.py``.
    """ 

    def __init__(self, client: KnowrithmClient):
        self.client = client

    # def seed_super_admin(self, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    #     """
    #     Seed the platform super admin from environment configuration.

    #     Endpoint:
    #         ``GET /v1/auth/super-admin`` - no authentication required.
    #     """
    #     return self.client._make_request("GET", "/auth/super-admin", headers=headers)

    def register_admin(
        self,
        payload: Dict[str, Any],
        *,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Register a new admin for a company.

        Endpoint:
            ``POST /v1/auth/register`` - public.
        """
        return self.client._make_request("POST", "/auth/register", data=payload, headers=headers)

    def login(
        self,
        email: str,
        password: str,
        *,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Authenticate a user and obtain JWT tokens.

        Endpoint:
            ``POST /v1/auth/login`` - public.
        """
        payload = {"email": email, "password": password}
        return self.client._make_request("POST", "/auth/login", data=payload, headers=headers)

    def refresh_access_token(
        self,
        refresh_token: str,
        *,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Refresh an access token using a refresh token.

        Endpoint:
            ``POST /v1/auth/refresh`` - supply ``Authorization: Bearer <refresh JWT>``.
        """
        refresh_headers = headers.copy() if headers else {}
        refresh_headers["Authorization"] = f"Bearer {refresh_token}"
        return self.client._make_request("POST", "/auth/refresh", headers=refresh_headers)

    def logout(self, headers: Dict[str, str]) -> Dict[str, Any]:
        """
        Revoke the current session using an access token.

        Endpoint:
            ``POST /v1/auth/logout`` - requires ``Authorization: Bearer <JWT>``.
        """
        return self.client._make_request("POST", "/auth/logout", headers=headers)

    def send_verification_email(
        self,
        email: str,
        *,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Trigger a verification email to a user.

        Endpoint:
            ``POST /v1/send`` - public.
        """
        return self.client._make_request("POST", "/send", data={"email": email}, headers=headers)

    def verify_email(
        self,
        token: str,
        *,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Verify an email address using the provided token.

        Endpoint:
            ``POST /v1/verify`` - public.
        """
        return self.client._make_request("POST", "/verify", data={"token": token}, headers=headers)

    def get_current_user(self, headers: Dict[str, str]) -> Dict[str, Any]:
        """
        Return the current user profile alongside company metadata.

        Endpoint:
            ``GET /v1/auth/user/me`` - requires JWT or API keys with read scope.
        """
        return self.client._make_request("GET", "/auth/user/me", headers=headers)

    def create_user(
        self,
        payload: Dict[str, Any],
        *,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Add a user under the authenticated company.

        Endpoint:
            ``POST /v1/auth/user`` - requires API key scope ``write`` or admin JWT.
        """
        return self.client._make_request("POST", "/auth/user", data=payload, headers=headers)


class ApiKeyService:
    """
    Handles API key management and analytics endpoints under the OAuth & API keys
    blueprint.
    """

    def __init__(self, client: KnowrithmClient):
        self.client = client

    def create_api_key(
        self,
        payload: Dict[str, Any],
        *,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new API key for the authenticated JWT user.

        Endpoint:
            ``POST /v1/auth/api-keys`` - requires JWT.
        """
        return self.client._make_request("POST", "/auth/api-keys", data=payload, headers=headers)

    def list_api_keys(self, headers: Dict[str, str]) -> Dict[str, Any]:
        """
        List active API keys created by the current JWT user.

        Endpoint:
            ``GET /v1/auth/api-keys`` - requires JWT.
        """
        return self.client._make_request("GET", "/auth/api-keys", headers=headers)

    def delete_api_key(self, api_key_id: str, headers: Dict[str, str]) -> Dict[str, Any]:
        """
        Revoke an API key.

        Endpoint:
            ``DELETE /v1/auth/api-keys/<api_key_id>`` - requires JWT.
        """
        return self.client._make_request("DELETE", f"/auth/api-keys/{api_key_id}", headers=headers)

    def validate_credentials(self, headers: Dict[str, str]) -> Dict[str, Any]:
        """
        Validate current credentials and retrieve metadata.

        Endpoint:
            ``GET /v1/auth/validate`` - requires JWT.
        """
        return self.client._make_request("GET", "/auth/validate", headers=headers)

    def get_api_key_overview(
        self,
        *,
        days: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve high-level API key analytics.

        Endpoint:
            ``GET /v1/overview``.
        """
        params: Dict[str, Any] = {}
        if days is not None:
            params["days"] = days
        return self.client._make_request("GET", "/overview", params=params or None, headers=headers)

    def get_usage_trends(
        self,
        *,
        days: Optional[int] = None,
        granularity: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve API key usage trends.

        Endpoint:
            ``GET /v1/usage-trends``.
        """
        params: Dict[str, Any] = {}
        if days is not None:
            params["days"] = days
        if granularity is not None:
            params["granularity"] = granularity
        return self.client._make_request("GET", "/usage-trends", params=params or None, headers=headers)

    def get_top_endpoints(
        self,
        *,
        days: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve top used endpoints per company.

        Endpoint:
            ``GET /v1/top-endpoints``.
        """
        params: Dict[str, Any] = {}
        if days is not None:
            params["days"] = days
        return self.client._make_request("GET", "/top-endpoints", params=params or None, headers=headers)

    def get_api_key_performance(
        self,
        *,
        days: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve performance metrics per API key.

        Endpoint:
            ``GET /v1/api-key-performance``.
        """
        params: Dict[str, Any] = {}
        if days is not None:
            params["days"] = days
        return self.client._make_request("GET", "/api-key-performance", params=params or None, headers=headers)

    def get_error_analysis(
        self,
        *,
        days: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve API key error distribution.

        Endpoint:
            ``GET /v1/error-analysis``.
        """
        params: Dict[str, Any] = {}
        if days is not None:
            params["days"] = days
        return self.client._make_request("GET", "/error-analysis", params=params or None, headers=headers)

    def get_rate_limit_analysis(
        self,
        *,
        days: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve rate limit usage insights.

        Endpoint:
            ``GET /v1/rate-limit-analysis``.
        """
        params: Dict[str, Any] = {}
        if days is not None:
            params["days"] = days
        return self.client._make_request("GET", "/rate-limit-analysis", params=params or None, headers=headers)

    def get_detailed_usage(
        self,
        api_key_id: str,
        *,
        days: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve detailed usage logs for a specific API key.

        Endpoint:
            ``GET /v1/detailed-usage/<api_key_id>``.
        """
        params: Dict[str, Any] = {}
        if days is not None:
            params["days"] = days
        return self.client._make_request(
            "GET",
            f"/detailed-usage/{api_key_id}",
            params=params or None,
            headers=headers,
        )


class UserService:
    """
    Combines user profile endpoints (``Profile`` blueprint) and user retrieval
    endpoints under ``Auth``.
    """

    def __init__(self, client: KnowrithmClient):
        self.client = client

    def get_profile(self, headers: Dict[str, str]) -> Dict[str, Any]:
        """
        Retrieve the authenticated user profile.

        Endpoint:
            ``GET /v1/user/profile`` - requires read scope or JWT.
        """
        return self.client._make_request("GET", "/user/profile", headers=headers)

    def update_profile(
        self,
        payload: Dict[str, Any],
        *,
        headers: Dict[str, str],
    ) -> Dict[str, Any]:
        """
        Update profile details.

        Endpoint:
            ``PUT /v1/user/profile`` - requires write scope or JWT.
        """
        return self.client._make_request("PUT", "/user/profile", data=payload, headers=headers)

    def get_user(self, user_id: str, headers: Dict[str, str]) -> Dict[str, Any]:
        """
        Fetch an individual user record.

        Endpoint:
            ``GET /v1/user/<user_id>`` - requires admin role or API keys with read scope.
        """
        return self.client._make_request("GET", f"/user/{user_id}", headers=headers)

