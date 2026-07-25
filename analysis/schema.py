from typing import Literal
from pydantic import BaseModel, Field


class Analysis(BaseModel):
    team: str
    product: str
    market: str
    risks: list[str]
    score: int = Field(ge=0, le=100)
    score_breakdown: dict[str, int]
    recommendation: Literal["Pass", "Watch", "Take a meeting"]
    change_my_mind: list[str]
    sources: list[str]
