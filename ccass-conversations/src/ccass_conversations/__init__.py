"""CCaSS Conversations - Retrieve conversations from Microsoft Dataverse."""

from .client import DataverseClient
from .models import Conversation

__all__ = ["DataverseClient", "Conversation"]
__version__ = "0.1.0"
