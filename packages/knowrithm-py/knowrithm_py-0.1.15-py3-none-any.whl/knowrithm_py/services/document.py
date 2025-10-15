
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from knowrithm_py.knowrithm.client import KnowrithmClient


class DocumentService:
    """
    Interface for ``app/blueprints/document/routes.py``. Handles uploads, deletes,
    restores, and list operations for documents and their chunk metadata.
    """

    def __init__(self, client: KnowrithmClient):
        self.client = client

    # ------------------------------------------------------------------ #
    # Upload
    # ------------------------------------------------------------------ #
    def upload_documents(
        self,
        agent_id: str,
        *,
        file_paths: Optional[Sequence[Path]] = None,
        urls: Optional[Sequence[str]] = None,
        url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Upload one or more documents or instruct the API to scrape remote URLs.
        
        Endpoint:
            ``POST /v1/document/upload`` - requires API key scope ``write`` or JWT.
        
        Args:
            agent_id: UUID of the agent to ingest documents for.
            file_paths: Optional iterable of file paths that should be streamed via multipart form data.
            urls: Optional list of remote URLs to scrape (sent in JSON payload).
            url: Convenience single URL alias (mutually exclusive with ``urls``).
            metadata: Additional fields accepted by the ingestion pipeline (e.g., ``tags``).
            headers: Optional header overrides.
        
        Returns:
            JSON payload describing the uploaded documents and ingestion jobs.
        """
        file_handles: List[Any] = []
        
        try:
            # When uploading files, use multipart/form-data with all fields as form data
            if file_paths:
                # Build form data payload
                data_payload: Dict[str, Any] = {"agent_id": agent_id}
                if metadata:
                    data_payload.update(metadata)
                
                # Add URLs to form data if provided
                if urls:
                    data_payload["urls"] = list(urls)
                if url:
                    data_payload["url"] = url
                
                # Build files list
                files: List[Tuple[str, Tuple[str, Any]]] = []
                for path in file_paths:
                    file_path = Path(path).expanduser()
                    
                    # Check if file exists
                    if not file_path.exists():
                        raise FileNotFoundError(f"File not found: {file_path}")
                    
                    if not file_path.is_file():
                        raise ValueError(f"Path is not a file: {file_path}")
                    
                    handle = file_path.open("rb")
                    file_handles.append(handle)
                    files.append(("files", (file_path.name, handle)))
                
                return self.client._make_request(
                    "POST",
                    "/document/upload",
                    data=data_payload,
                    files=files,
                    headers=headers,
                )
            
            # When only URLs (no files), send as JSON payload
            else:
                json_payload: Dict[str, Any] = {"agent_id": agent_id}
                if metadata:
                    json_payload.update(metadata)
                if urls:
                    json_payload["urls"] = list(urls)
                if url:
                    json_payload["url"] = url
                
                return self.client._make_request(
                    "POST",
                    "/document/upload",
                    json=json_payload,
                    headers=headers,
                )
        
        finally:
            # Always close file handles
            for handle in file_handles:
                try:
                    handle.close()
                except Exception:
                    pass
                
    # ------------------------------------------------------------------ #
    # Listing
    # ------------------------------------------------------------------ #
    def list_documents(
        self,
        *,
        page: Optional[int] = None,
        per_page: Optional[int] = None,
        status: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        List documents for the authenticated company.

        Endpoint:
            ``GET /v1/document`` - requires API key scope ``read`` or JWT.

        Returns:
            Paginated response containing document metadata.
        """
        params: Dict[str, Any] = {}
        if page is not None:
            params["page"] = page
        if per_page is not None:
            params["per_page"] = per_page
        if status is not None:
            params["status"] = status
        return self.client._make_request("GET", "/document", params=params or None, headers=headers)

    def list_deleted_documents(self, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        List soft-deleted documents.

        Endpoint:
            ``GET /v1/document/deleted`` - requires read scope.
        """
        return self.client._make_request("GET", "/document/deleted", headers=headers)

    def list_deleted_chunks(self, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        List soft-deleted document chunks.

        Endpoint:
            ``GET /v1/document/chunk/deleted`` - requires read scope.
        """
        return self.client._make_request("GET", "/document/chunk/deleted", headers=headers)

    # ------------------------------------------------------------------ #
    # Delete / restore
    # ------------------------------------------------------------------ #
    def delete_document(self, document_id: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Soft-delete a document.

        Endpoint:
            ``DELETE /v1/document/<document_id>`` - requires write scope.
        """
        return self.client._make_request("DELETE", f"/document/{document_id}", headers=headers)

    def restore_document(self, document_id: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Restore a soft-deleted document.

        Endpoint:
            ``PATCH /v1/document/<document_id>/restore`` - requires write scope.
        """
        return self.client._make_request("PATCH", f"/document/{document_id}/restore", headers=headers)

    def delete_document_chunk(self, chunk_id: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Soft-delete a single document chunk.

        Endpoint:
            ``DELETE /v1/document/chunk/<chunk_id>`` - requires write scope.
        """
        return self.client._make_request("DELETE", f"/document/chunk/{chunk_id}", headers=headers)

    def restore_document_chunk(self, chunk_id: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Restore a soft-deleted chunk.

        Endpoint:
            ``PATCH /v1/document/chunk/<chunk_id>/restore`` - requires write scope.
        """
        return self.client._make_request("PATCH", f"/document/chunk/{chunk_id}/restore", headers=headers)

    def delete_document_chunks(
        self,
        document_id: str,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Soft-delete every chunk for a document.

        Endpoint:
            ``DELETE /v1/document/<document_id>/chunk`` - requires write scope.
        """
        return self.client._make_request("DELETE", f"/document/{document_id}/chunk", headers=headers)

    def restore_all_document_chunks(
        self,
        document_id: str,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Restore all chunks associated with a document.

        Endpoint:
            ``PATCH /v1/document/<document_id>/chunk/restore-all`` - requires write scope.
        """
        return self.client._make_request(
            "PATCH",
            f"/document/{document_id}/chunk/restore-all",
            headers=headers,
        )

    def bulk_delete_documents(
        self,
        document_ids: Sequence[str],
        *,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Soft-delete multiple documents in one request.

        Endpoint:
            ``DELETE /v1/document/bulk-delete`` - requires write scope.

        Payload:
            ``{"document_ids": [...]}``
        """
        payload = {"document_ids": list(document_ids)}
        return self.client._make_request(
            "DELETE",
            "/document/bulk-delete",
            data=payload,
            headers=headers,
        )
