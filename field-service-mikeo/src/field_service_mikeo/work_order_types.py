"""Work Order Types management for Dynamics 365 Field Service."""

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from .dataverse_client import DataverseClient


@dataclass
class WorkOrderType:
    """Represents a Field Service Work Order Type."""
    
    id: UUID | None
    name: str
    incident_required: bool = False
    taxable: bool = False
    is_active: bool = True
    
    @classmethod
    def from_dataverse(cls, data: dict[str, Any]) -> "WorkOrderType":
        """Create WorkOrderType from Dataverse response."""
        return cls(
            id=UUID(data["msdyn_workordertypeid"]) if data.get("msdyn_workordertypeid") else None,
            name=data.get("msdyn_name", ""),
            incident_required=data.get("msdyn_incidentrequired", False),
            taxable=data.get("msdyn_taxable", False),
            is_active=data.get("statecode", 0) == 0,
        )
    
    def to_dataverse(self) -> dict[str, Any]:
        """Convert to Dataverse payload."""
        payload: dict[str, Any] = {
            "msdyn_name": self.name,
            "msdyn_incidentrequired": self.incident_required,
            "msdyn_taxable": self.taxable,
        }
        return payload


class WorkOrderTypeManager:
    """Manager for CRUD operations on Work Order Types."""
    
    ENTITY_SET = "msdyn_workordertypes"
    
    def __init__(self, client: DataverseClient | None = None):
        self.client = client or DataverseClient()
    
    def list_all(self, active_only: bool = True) -> list[WorkOrderType]:
        """List all work order types."""
        endpoint = self.ENTITY_SET
        params = {
            "$select": "msdyn_workordertypeid,msdyn_name,msdyn_incidentrequired,msdyn_taxable,statecode",
            "$orderby": "msdyn_name asc",
        }
        
        if active_only:
            params["$filter"] = "statecode eq 0"
        
        response = self.client.get(endpoint, params)
        records = response.get("value", [])
        
        return [WorkOrderType.from_dataverse(record) for record in records]
    
    def get_by_id(self, work_order_type_id: UUID | str) -> WorkOrderType | None:
        """Get a specific work order type by ID."""
        endpoint = f"{self.ENTITY_SET}({work_order_type_id})"
        params = {
            "$select": "msdyn_workordertypeid,msdyn_name,msdyn_incidentrequired,msdyn_taxable,statecode",
        }
        
        try:
            response = self.client.get(endpoint, params)
            return WorkOrderType.from_dataverse(response)
        except Exception:
            return None
    
    def get_by_name(self, name: str) -> WorkOrderType | None:
        """Get a work order type by name."""
        endpoint = self.ENTITY_SET
        params = {
            "$select": "msdyn_workordertypeid,msdyn_name,msdyn_incidentrequired,msdyn_taxable,statecode",
            "$filter": f"msdyn_name eq '{name}'",
        }
        
        response = self.client.get(endpoint, params)
        records = response.get("value", [])
        
        return WorkOrderType.from_dataverse(records[0]) if records else None
    
    def create(self, work_order_type: WorkOrderType) -> UUID:
        """Create a new work order type."""
        payload = work_order_type.to_dataverse()
        result = self.client.post(self.ENTITY_SET, payload)
        
        # Extract GUID from OData-EntityId header
        if result and "@odata.id" in result:
            odata_id = result["@odata.id"]
            # Format: .../msdyn_workordertypes(guid)
            guid_str = odata_id.split("(")[-1].rstrip(")")
            return UUID(guid_str)
        
        raise RuntimeError("Failed to create work order type - no ID returned")
    
    def update(self, work_order_type_id: UUID | str, work_order_type: WorkOrderType) -> None:
        """Update an existing work order type."""
        endpoint = f"{self.ENTITY_SET}({work_order_type_id})"
        payload = work_order_type.to_dataverse()
        self.client.patch(endpoint, payload)
    
    def delete(self, work_order_type_id: UUID | str) -> None:
        """Delete a work order type."""
        endpoint = f"{self.ENTITY_SET}({work_order_type_id})"
        self.client.delete(endpoint)
    
    def deactivate(self, work_order_type_id: UUID | str) -> None:
        """Deactivate a work order type (set statecode to 1)."""
        endpoint = f"{self.ENTITY_SET}({work_order_type_id})"
        self.client.patch(endpoint, {"statecode": 1})
    
    def activate(self, work_order_type_id: UUID | str) -> None:
        """Activate a work order type (set statecode to 0)."""
        endpoint = f"{self.ENTITY_SET}({work_order_type_id})"
        self.client.patch(endpoint, {"statecode": 0})
