"""Data models for CCaSS Conversations."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class Conversation:
    """Represents a conversation record from Dataverse."""
    
    conversation_id: str
    subject: Optional[str] = None
    created_on: Optional[datetime] = None
    modified_on: Optional[datetime] = None
    status: Optional[str] = None
    status_reason: Optional[str] = None
    owner_id: Optional[str] = None
    owner_name: Optional[str] = None
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    channel: Optional[str] = None
    raw_data: dict = field(default_factory=dict)
    
    @classmethod
    def from_dataverse(cls, data: dict[str, Any]) -> "Conversation":
        """Create a Conversation instance from Dataverse API response data."""
        return cls(
            conversation_id=data.get("msdyn_conversationid", data.get("activityid", "")),
            subject=data.get("subject"),
            created_on=cls._parse_datetime(data.get("createdon")),
            modified_on=cls._parse_datetime(data.get("modifiedon")),
            status=cls._get_status_label(data.get("statecode")),
            status_reason=cls._get_status_reason_label(data.get("statuscode")),
            owner_id=data.get("_ownerid_value"),
            owner_name=data.get("_ownerid_value@OData.Community.Display.V1.FormattedValue"),
            customer_id=data.get("_msdyn_customer_value"),
            customer_name=data.get("_msdyn_customer_value@OData.Community.Display.V1.FormattedValue"),
            channel=data.get("msdyn_channel@OData.Community.Display.V1.FormattedValue"),
            raw_data=data,
        )
    
    @staticmethod
    def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
        """Parse a datetime string from Dataverse."""
        if not value:
            return None
        try:
            # Handle ISO format with or without microseconds
            if "." in value:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def _get_status_label(statecode: Optional[int]) -> Optional[str]:
        """Convert state code to label."""
        if statecode is None:
            return None
        status_map = {
            0: "Open",
            1: "Active",
            2: "Closed",
            3: "Cancelled",
        }
        return status_map.get(statecode, f"Unknown ({statecode})")
    
    @staticmethod
    def _get_status_reason_label(statuscode: Optional[int]) -> Optional[str]:
        """Convert status code to label."""
        if statuscode is None:
            return None
        # Common status reasons - extend as needed
        reason_map = {
            1: "Open",
            2: "Active",
            3: "Resolved",
            4: "Cancelled",
        }
        return reason_map.get(statuscode, f"Unknown ({statuscode})")


@dataclass
class ConversationMessage:
    """Represents a message within a conversation."""
    
    message_id: str
    conversation_id: str
    content: Optional[str] = None
    sender_type: Optional[str] = None  # "Agent" or "Customer"
    sender_name: Optional[str] = None
    created_on: Optional[datetime] = None
    raw_data: dict = field(default_factory=dict)
    
    @classmethod
    def from_dataverse(cls, data: dict[str, Any]) -> "ConversationMessage":
        """Create a ConversationMessage instance from Dataverse API response data."""
        return cls(
            message_id=data.get("msdyn_ocliveworkitemmessageid", ""),
            conversation_id=data.get("_msdyn_ocliveworkitemid_value", ""),
            content=data.get("msdyn_content"),
            sender_type=data.get("msdyn_sendertype@OData.Community.Display.V1.FormattedValue"),
            sender_name=data.get("msdyn_sendername"),
            created_on=Conversation._parse_datetime(data.get("createdon")),
            raw_data=data,
        )
