from typing import List, Optional,Literal
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
    changes_detected: list[str] = Field(
        ..., description="List of changes detected by comparing the previous and current images (e.g., damage, wear, anomalies)"
    )
    condition_change: Literal["same", "changed"] = Field(
        ..., description="Overall condition change observed from the comparison: 'same' if no/minimal changes, 'changed' if any differences detected"
    )
    severity: Literal["low", "medium", "high"] = Field(
        ..., description="Severity level of the changes detected during the comparison: 'low' / 'medium' / 'high'"
    )
    recommendations: list[str] = Field(
        ..., description="Maintenance or repair recommendations based on the comparison of previous and current images"
    )
    analysis: str = Field(
        ..., description="Detailed textual analysis explaining the changes observed between the previous and current images"
    )

