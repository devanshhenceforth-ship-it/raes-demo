from typing import List, Optional,Literal
from pydantic import BaseModel, Field

class VideoEvent(BaseModel):
    # timestamp: int
    item: str
    description: str

class AllAnalyzerResponse(BaseModel):
    issues: List[VideoEvent] = Field(
        ..., description="List of identified items."
    )
class ItemComparisonResult(BaseModel):
    changes_detected: list[str] = Field(
        ..., description="Detected changes between previous and current images."
    )
    condition_status: Literal["no_change", "minor_change", "moderate_change", "major_change","different_item"] = Field(
        ..., description="Overall condition change level."
    )
    severity: Literal["low", "medium", "high"] = Field(
        ..., description="Severity level of detected changes."
    )
    recommendations: list[str] = Field(
        ..., description="Recommended actions based on detected changes."
    )
    analysis: str = Field(
        ..., description="Summary of the observed differences."
    )

