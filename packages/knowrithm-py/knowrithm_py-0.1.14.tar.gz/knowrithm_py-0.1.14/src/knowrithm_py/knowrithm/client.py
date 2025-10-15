



import time
import requests
from typing import Any, Dict, Optional
from knowrithm_py.config.config import Config
from knowrithm_py.dataclass.config import KnowrithmConfig
from knowrithm_py.dataclass.error import KnowrithmAPIError

class KnowrithmClient:
    """
    Main client for interacting with the Knowrithm API using API Key authentication
    
    Example usage:
        # Initialize with API credentials
        client = KnowrithmClient(
            api_key="your_api_key_here",
            api_secret="your_api_secret_here",
            base_url="https://app.knowrithm.org"
        )
        
        # Create a company
        company = client.companies.create({
            "name": "Acme Corp",
            "email": "contact@acme.com"
        })
        
        # Create an agent
        agent = client.agents.create({
            "name": "Customer Support Bot",
            "company_id": company["id"]
        })
    """
    
    def __init__(self, api_key: str, api_secret: str, config: Optional[KnowrithmConfig] = None):
        """
        Initialize the client with API key and secret
        
        Args:
            api_key: Your API key
            api_secret: Your API secret
            config: Optional configuration object
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.config = config or KnowrithmConfig(base_url=Config.KNOWRITHM_BASE_URL)
        self._session = requests.Session()
        
        # Set up authentication headers
        self._setup_authentication()
        
        # Initialize service modules
        from knowrithm_py.services.address import AddressService
        from knowrithm_py.services.admin import AdminService
        from knowrithm_py.services.agent import AgentService
        from knowrithm_py.services.auth import ApiKeyService, AuthService, UserService
        from knowrithm_py.services.company import CompanyService
        from knowrithm_py.services.conversation import ConversationService, MessageService
        from knowrithm_py.services.dashboard import AnalyticsService
        from knowrithm_py.services.database import DatabaseService
        from knowrithm_py.services.document import DocumentService
        from knowrithm_py.services.settings import SettingsService
        from knowrithm_py.services.lead import LeadService
        
        self.auth = AuthService(self)
        self.api_keys = ApiKeyService(self)
        self.users = UserService(self)
        self.companies = CompanyService(self)
        self.agents = AgentService(self)
        self.leads = LeadService(self)
        self.documents = DocumentService(self)
        self.databases = DatabaseService(self)
        self.conversations = ConversationService(self)
        self.messages = MessageService(self)
        self.analytics = AnalyticsService(self)
        self.settings = SettingsService(self)
        self.addresses = AddressService(self)
        self.admin = AdminService(self)
    
    def _setup_authentication(self):
        """Set up API key authentication headers"""
        self._session.headers.update({
            "X-API-Key": self.api_key,
            "X-API-Secret": self.api_secret,
        })
    
    @property
    def base_url(self) -> str:
        return f"{self.config.base_url}/{self.config.api_version}"
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        files: Optional[Any] = None,
        headers: Optional[Dict] = None
    ) -> Any:
        """Make HTTP request with error handling and retries"""
        url = f"{self.base_url}{endpoint}"
        request_headers = {}
        if headers:
            request_headers.update(headers)
        
        # Add content type for JSON requests
        if data and not files and "Content-Type" not in request_headers:
            request_headers['Content-Type'] = 'application/json'
        if files:
            # Let requests set the multipart boundary automatically.
            request_headers.pop("Content-Type", None)
        
        for attempt in range(self.config.max_retries):
            try:
                response = self._session.request(
                    method=method,
                    url=url,
                    json=data if data and not files else None,
                    data=data if files else None,
                    params=params,
                    files=files,
                    headers=request_headers,
                    timeout=self.config.timeout,
                    verify=self.config.verify_ssl
                )
                
                if response.status_code >= 400:
                    error_data = {}
                    try:
                        error_data = response.json()
                    except ValueError:
                        error_data = {"detail": response.text}
                    
                    raise KnowrithmAPIError(
                        message=error_data.get("detail", error_data.get("message", f"HTTP {response.status_code}")),
                        status_code=response.status_code,
                        response_data=error_data,
                        error_code=error_data.get("error_code")
                    )
                
                # Return empty dict for successful requests with no content
                if not response.content:
                    return {"success": True}
                
                try:
                    return response.json()
                except ValueError:
                    # Non-JSON responses are returned as raw text or bytes
                    return response.content if files else response.text
                
            except requests.exceptions.RequestException as e:
                if attempt == self.config.max_retries - 1:
                    raise KnowrithmAPIError(f"Request failed after {self.config.max_retries} attempts: {str(e)}")
                time.sleep(self.config.retry_backoff_factor ** attempt)
        
        raise KnowrithmAPIError("Max retries exceeded")
