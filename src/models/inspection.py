from typing import List, Optional
from pydantic import BaseModel, Field

class VideoEvent(BaseModel):
    timestamp: int
    item: str
    description: str

class AllAnalyzerResponse(BaseModel):
    issues: List[VideoEvent] = Field(
        ..., description="List of identified items."
    )

class ItemComparisonResult(BaseModel):
    changes_detected: list[str] = Field(..., description="List of changes detected (damage, wear, etc.)")
    condition_change: str = Field(..., description="Improved / Deteriorated / Same")
    severity: str = Field(..., description="Severity level: Low / Medium / High")
    recommendations: list[str] = Field(..., description="Maintenance or repair recommendations")
    analysis: str = Field(..., description="Detailed textual analysis")