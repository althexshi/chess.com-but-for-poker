from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from poker_coach.api.coach import get_coaching
from poker_coach.api.database import (
    get_connection,
    get_or_create_user,
    get_random_scenario,
    get_scenario_by_id,
    init_db,
    insert_telemetry,
)
from poker_coach.api.models import (
    CoachFeedback,
    EvaluateRequest,
    EvaluateResponse,
    GtoComparison,
    ScenarioResponse,
    UserCreate,
    UserResponse,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Poker GTO Spot Trainer", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/scenarios/next", response_model=ScenarioResponse)
def next_scenario():
    conn = get_connection()
    try:
        scenario = get_random_scenario(conn)
        if scenario is None:
            raise HTTPException(status_code=404, detail="No scenarios in database")
        return ScenarioResponse(
            id=scenario["id"],
            board=scenario["board"],
            hole_cards=scenario["hole_cards"],
            position=scenario["position"],
            pot_size=scenario["pot_size"],
            stack_size=scenario["stack_size"],
            opponent_action=scenario["opponent_action"],
        )
    finally:
        conn.close()


@app.post("/api/evaluate", response_model=EvaluateResponse)
def evaluate_action(req: EvaluateRequest):
    conn = get_connection()
    try:
        scenario = get_scenario_by_id(conn, req.scenario_id)
        if scenario is None:
            raise HTTPException(status_code=404, detail="Scenario not found")

        user_id = get_or_create_user(conn, req.username)

        gto = scenario["gto_strategy"]
        user_action_key = req.action.lower()
        match_pct = gto.get(user_action_key, 0.0)

        coaching_data = get_coaching(
            board=scenario["board"],
            hole_cards=scenario["hole_cards"],
            position=scenario["position"],
            opponent_action=scenario["opponent_action"],
            pot_size=scenario["pot_size"],
            stack_size=scenario["stack_size"],
            user_action=req.action,
            gto_strategy=gto,
        )

        insert_telemetry(
            conn,
            user_id=user_id,
            scenario_id=req.scenario_id,
            action=req.action,
            bet_size=req.bet_size,
            prev_outcome=req.prev_outcome,
            response_time_ms=req.response_time_ms,
        )

        return EvaluateResponse(
            comparison=GtoComparison(
                user_action=req.action,
                gto_strategy=gto,
                match_pct=match_pct,
            ),
            coaching=CoachFeedback(**coaching_data),
        )
    finally:
        conn.close()


@app.post("/api/users", response_model=UserResponse)
def create_user(req: UserCreate):
    conn = get_connection()
    try:
        user_id = get_or_create_user(conn, req.username)
        return UserResponse(id=user_id, username=req.username)
    finally:
        conn.close()
