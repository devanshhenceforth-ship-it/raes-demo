from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class InspectionTask(BaseModel):
    item_id: str = Field(..., description="ID of the item")
    item_name: str = Field(..., description="Name of the item")
    room_id: str = Field(..., description="ID of the room")
    room_name: str = Field(..., description="Name of the room")
    task_type: str = Field(..., description="Type of inspection task (Inspect, Repair, Clean, Replace, etc.)")
    priority: str = Field(default="Medium", description="Priority level (Low, Medium, High, Urgent)")
    description: Optional[str] = Field(None, description="Task description")
    status: str = Field(default="Pending", description="Status (Pending, In Progress, Completed)")
    due_date: Optional[datetime] = Field(None, description="Due date for the task")
    assigned_to: Optional[str] = Field(None, description="Person assigned to the task")
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PropertyInspectionSummary(BaseModel):
    property_id: str
    property_name: str
    total_rooms: int
    total_items: int
    total_tasks: int
    tasks_by_priority: dict = Field(default_factory=dict)
    rooms: List[dict] = Field(default_factory=list)
