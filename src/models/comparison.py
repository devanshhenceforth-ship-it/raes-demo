from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class ItemComparison(BaseModel):
    item_id: str
    previous_image_url: str
    current_image_url: str
    changes_detected: List[str] = Field(default_factory=list)
    condition_change: Optional[str] = Field(None, description="Change in condition (Improved, Deteriorated, Same)")
    severity: str = Field(default="Low", description="Severity of changes (Low, Medium, High)")
    recommendations: List[str] = Field(default_factory=list)
    ai_analysis: str = Field(..., description="Full AI analysis text")
    inspection_date: datetime = Field(default_factory=datetime.utcnow)
    
class ItemInspectionResult(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None)
    item_id: str
    room_id: str
    comparison: ItemComparison
    created_at: datetime = Field(default_factory=datetime.utcnow)
