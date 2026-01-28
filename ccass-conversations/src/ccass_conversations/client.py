"""Dataverse API client for retrieving conversations."""

import os
from typing import Optional

import httpx
from dotenv import load_dotenv
from msal import ConfidentialClientApplication

from .models import Conversation, ConversationMessage


class DataverseClient:
    """Client for interacting with Microsoft Dataverse to retrieve conversations."""
    
    def __init__(
        self,
        dataverse_url: Optional[str] = None,
        client_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        client_secret: Optional[str] = None,
    ):
        """
        Initialize the Dataverse client.
        
        Args:
            dataverse_url: Dataverse environment URL (or set DATAVERSE_URL env var)
            client_id: Azure AD app client ID (or set AZURE_CLIENT_ID env var)
            tenant_id: Azure AD tenant ID (or set AZURE_TENANT_ID env var)
            client_secret: Azure AD app client secret (or set AZURE_CLIENT_SECRET env var)
        """
        load_dotenv()
        
        self.dataverse_url = (dataverse_url or os.getenv("DATAVERSE_URL", "")).rstrip("/")
        self.client_id = client_id or os.getenv("AZURE_CLIENT_ID", "")
        self.tenant_id = tenant_id or os.getenv("AZURE_TENANT_ID", "")
        self.client_secret = client_secret or os.getenv("AZURE_CLIENT_SECRET", "")
        
        if not all([self.dataverse_url, self.client_id, self.tenant_id, self.client_secret]):
            raise ValueError(
                "Missing required configuration. Please set DATAVERSE_URL, "
                "AZURE_CLIENT_ID, AZURE_TENANT_ID, and AZURE_CLIENT_SECRET "
                "environment variables or pass them to the constructor."
            )
        
        self._access_token: Optional[str] = None
        self._http_client: Optional[httpx.Client] = None
    
    def _get_access_token(self) -> str:
        """Acquire an access token using MSAL."""
        if self._access_token:
            return self._access_token
        
        authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        scope = [f"{self.dataverse_url}/.default"]
        
        app = ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=authority,
        )
        
        result = app.acquire_token_for_client(scopes=scope)
        
        if "access_token" not in result:
            error = result.get("error_description", result.get("error", "Unknown error"))
            raise RuntimeError(f"Failed to acquire access token: {error}")
        
        self._access_token = result["access_token"]
        return self._access_token
    
    @property
    def http_client(self) -> httpx.Client:
        """Get or create the HTTP client with authentication."""
        if self._http_client is None:
            token = self._get_access_token()
            self._http_client = httpx.Client(
                base_url=f"{self.dataverse_url}/api/data/v9.2",
                headers={
                    "Authorization": f"Bearer {token}",
                    "OData-MaxVersion": "4.0",
                    "OData-Version": "4.0",
                    "Accept": "application/json",
                    "Content-Type": "application/json; charset=utf-8",
                    "Prefer": "odata.include-annotations=*",
                },
                timeout=60.0,
            )
        return self._http_client
    
    def get_conversations(
        self,
        top: int = 100,
        filter_query: Optional[str] = None,
        select_fields: Optional[list[str]] = None,
        order_by: str = "createdon desc",
    ) -> list[Conversation]:
        """
        Retrieve conversations from Dataverse.
        
        Args:
            top: Maximum number of records to retrieve
            filter_query: OData filter query (e.g., "statecode eq 0")
            select_fields: List of fields to select (None for all)
            order_by: OData order by clause
            
        Returns:
            List of Conversation objects
        """
        # Build query parameters
        params: dict[str, str] = {
            "$top": str(top),
            "$orderby": order_by,
        }
        
        if filter_query:
            params["$filter"] = filter_query
        
        if select_fields:
            params["$select"] = ",".join(select_fields)
        
        # Query the msdyn_ocliveworkitem entity (Omnichannel conversations)
        response = self.http_client.get("/msdyn_ocliveworkitems", params=params)
        response.raise_for_status()
        
        data = response.json()
        records = data.get("value", [])
        
        return [Conversation.from_dataverse(record) for record in records]
    
    def get_conversation_by_id(self, conversation_id: str) -> Optional[Conversation]:
        """
        Retrieve a specific conversation by ID.
        
        Args:
            conversation_id: The conversation GUID
            
        Returns:
            Conversation object or None if not found
        """
        try:
            response = self.http_client.get(f"/msdyn_ocliveworkitems({conversation_id})")
            response.raise_for_status()
            return Conversation.from_dataverse(response.json())
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise
    
    def get_conversation_messages(
        self,
        conversation_id: str,
        top: int = 500,
    ) -> list[ConversationMessage]:
        """
        Retrieve messages for a specific conversation.
        
        Args:
            conversation_id: The conversation GUID
            top: Maximum number of messages to retrieve
            
        Returns:
            List of ConversationMessage objects
        """
        params = {
            "$top": str(top),
            "$filter": f"_msdyn_ocliveworkitemid_value eq {conversation_id}",
            "$orderby": "createdon asc",
        }
        
        response = self.http_client.get("/msdyn_ocsessionparticipantevents", params=params)
        response.raise_for_status()
        
        data = response.json()
        records = data.get("value", [])
        
        return [ConversationMessage.from_dataverse(record) for record in records]
    
    def get_recent_conversations(
        self,
        days: int = 7,
        status: Optional[str] = None,
    ) -> list[Conversation]:
        """
        Retrieve recent conversations.
        
        Args:
            days: Number of days to look back
            status: Filter by status ("open", "active", "closed")
            
        Returns:
            List of Conversation objects
        """
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        filter_parts = [f"createdon ge {cutoff_date.isoformat()}Z"]
        
        if status:
            status_map = {"open": 0, "active": 1, "closed": 2}
            if status.lower() in status_map:
                filter_parts.append(f"statecode eq {status_map[status.lower()]}")
        
        return self.get_conversations(
            filter_query=" and ".join(filter_parts),
            top=500,
        )
    
    def close(self) -> None:
        """Close the HTTP client."""
        if self._http_client:
            self._http_client.close()
            self._http_client = None
    
    def __enter__(self) -> "DataverseClient":
        return self
    
    def __exit__(self, *args) -> None:
        self.close()
