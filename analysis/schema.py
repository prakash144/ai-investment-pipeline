from typing import Literal
from pydantic import BaseModel, Field


class Analysis(BaseModel):
    executive_summary: str
    team: str
    product: str
    market: str
    traction_signals: str
    risks: list[str]
    thesis_alignment: str
    score: int = Field(ge=0, le=100)
    score_breakdown: dict[str, int]
    confidence: Literal["High", "Medium", "Low"]
    recommendation: Literal["Pass", "Watch", "Take a meeting"]
    change_my_mind: list[str]
    sources: list[str]
