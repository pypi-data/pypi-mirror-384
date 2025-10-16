from typing import Any, Dict, Optional

from knowrithm_py.knowrithm.client import KnowrithmClient


class WebsiteService:
    """
    Client wrapper for the website awareness endpoints exposed under
    ``app/blueprints/website/routes.py``.
    """

    def __init__(self, client: KnowrithmClient):
        self.client = client

    # ------------------------------------------------------------------ #
    # Website source management
    # ------------------------------------------------------------------ #
    def register_source(
        self,
        payload: Dict[str, Any],
        *,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Register a new website source so an agent can crawl a domain.

        Endpoint:
            ``POST /v1/website/source`` - requires API key scope ``write`` or JWT.

        Args:
            payload: Must contain ``agent_id`` and ``base_url`` plus optional crawl settings.
        """
        return self.client._make_request("POST", "/website/source", data=payload, headers=headers)

    def list_sources(
        self,
        *,
        agent_id: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        List registered website sources for the authenticated company.

        Endpoint:
            ``GET /v1/website/source`` - requires API key scope ``read`` or JWT.

        Args:
            agent_id: Optional agent filter.
        """
        params: Dict[str, Any] = {}
        if agent_id is not None:
            params["agent_id"] = agent_id
        return self.client._make_request(
            "GET",
            "/website/source",
            params=params or None,
            headers=headers,
        )

    def list_source_pages(
        self,
        source_id: str,
        *,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve the crawl metadata and page coverage for a website source.

        Endpoint:
            ``GET /v1/website/source/<source_id>/pages`` - requires read scope or JWT.
        """
        return self.client._make_request(
            "GET",
            f"/website/source/{source_id}/pages",
            headers=headers,
        )

    def trigger_crawl(
        self,
        source_id: str,
        *,
        max_pages: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Queue a crawl job for the specified website source.

        Endpoint:
            ``POST /v1/website/source/<source_id>/crawl`` - requires write scope or JWT.

        Args:
            max_pages: Optional override for the crawl limit.
        """
        payload: Dict[str, Any] = {}
        if max_pages is not None:
            payload["max_pages"] = max_pages
        return self.client._make_request(
            "POST",
            f"/website/source/{source_id}/crawl",
            data=payload or None,
            headers=headers,
        )

    # ------------------------------------------------------------------ #
    # Widget handshake
    # ------------------------------------------------------------------ #
    def handshake(
        self,
        agent_id: str,
        url: str,
        *,
        title: Optional[str] = None,
        trigger_crawl: Optional[bool] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Allow the embedded widget to declare its page context and optionally
        request a fresh crawl.

        Endpoint:
            ``POST /v1/website/handshake`` - public endpoint.
        """
        payload: Dict[str, Any] = {"agent_id": agent_id, "url": url}
        if title is not None:
            payload["title"] = title
        if trigger_crawl is not None:
            payload["trigger_crawl"] = trigger_crawl
        return self.client._make_request(
            "POST",
            "/website/handshake",
            data=payload,
            headers=headers,
        )
