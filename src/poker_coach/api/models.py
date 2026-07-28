from typing import Literal

from pydantic import BaseModel


class ScenarioResponse(BaseModel):
    id: int
    board: str
    hole_cards: str
    position: str
    pot_size: float
    stack_size: float
    opponent_action: str


class EvaluateRequest(BaseModel):
    scenario_id: int
    username: str
    action: str
    bet_size: float | None = None
    prev_outcome: str | None = None
    response_time_ms: int | None = None


class GtoComparison(BaseModel):
    user_action: str
    gto_strategy: dict[str, float]
    match_pct: float


class CoachFeedback(BaseModel):
    verdict: Literal["good", "okay", "mistake"]
    concept: str
    summary: str
    advice: str


class EvaluateResponse(BaseModel):
    comparison: GtoComparison
    coaching: CoachFeedback


class UserCreate(BaseModel):
    username: str


class UserResponse(BaseModel):
    id: int
    username: str
