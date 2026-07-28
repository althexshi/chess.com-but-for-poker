from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai

load_dotenv(Path(__file__).resolve().parents[3] / ".env")

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        use_vertex = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").lower() == "true"
        _client = genai.Client(
            vertexai=use_vertex,
            project=os.getenv("GOOGLE_CLOUD_PROJECT"),
            location=os.getenv("GOOGLE_CLOUD_LOCATION"),
        )
    return _client


SYSTEM_PROMPT = """\
You are an expert poker coach. Given a board, the player's hole cards, \
their position, the action before their turn, and the GTO solver's optimal \
frequencies, analyze the player's decision.

You MUST respond with valid JSON matching this exact schema:
{
  "verdict": "good" | "okay" | "mistake",
  "concept": "<the single most relevant poker concept, e.g. 'range advantage', 'blockers', 'pot odds', 'position leverage', 'equity denial'>",
  "summary": "<one sentence: what the player did and how it compares to GTO>",
  "advice": "<one sentence: what to think about next time in this spot>"
}

Rules:
- verdict is "good" if the player chose the GTO-preferred action, "okay" if their action has >20% frequency, "mistake" if <20%.
- concept should name the ONE most important strategic idea driving the solver's preference.
- Do NOT repeat the GTO percentages in summary or advice.
- Be direct and instructive. No filler.
- Return ONLY the JSON object, no markdown fences or extra text.\
"""

MODEL = "gemini-2.0-flash"


def build_prompt(
    board: str,
    hole_cards: str,
    position: str,
    opponent_action: str,
    pot_size: float,
    stack_size: float,
    user_action: str,
    gto_strategy: dict[str, float],
) -> str:
    gto_lines = ", ".join(f"{a}: {w:.0f}%" for a, w in gto_strategy.items())
    return (
        f"Board: {board}\n"
        f"Hole cards: {hole_cards}\n"
        f"Position: {position}\n"
        f"Action before turn: {opponent_action}\n"
        f"Pot: {pot_size:.1f} bb | Stack: {stack_size:.1f} bb\n"
        f"GTO frequencies: {gto_lines}\n"
        f"Player chose: {user_action}\n\n"
        "Explain the strategic reasoning behind the solver's preferred action "
        "and whether the player's choice is reasonable."
    )


def _fallback_coaching(
    user_action: str, gto_strategy: dict[str, float],
) -> dict:
    user_action_key = user_action.lower()
    match_pct = gto_strategy.get(user_action_key, 0.0)
    best_action = max(gto_strategy, key=gto_strategy.get)

    if user_action_key == best_action:
        verdict = "good"
        summary = f"Your choice of '{user_action}' matches the GTO-preferred action."
        advice = "Keep applying this logic in similar spots."
    elif match_pct >= 20.0:
        verdict = "okay"
        summary = f"'{user_action}' is a reasonable alternative, but '{best_action}' is preferred."
        advice = f"Consider why '{best_action}' might be stronger here."
    else:
        verdict = "mistake"
        summary = f"'{user_action}' deviates significantly from GTO, which favors '{best_action}'."
        advice = "Review the board texture and your range before choosing this action."

    return {
        "verdict": verdict,
        "concept": "general strategy",
        "summary": summary,
        "advice": advice,
    }


def get_coaching(
    board: str,
    hole_cards: str,
    position: str,
    opponent_action: str,
    pot_size: float,
    stack_size: float,
    user_action: str,
    gto_strategy: dict[str, float],
) -> dict:
    prompt = build_prompt(
        board=board,
        hole_cards=hole_cards,
        position=position,
        opponent_action=opponent_action,
        pot_size=pot_size,
        stack_size=stack_size,
        user_action=user_action,
        gto_strategy=gto_strategy,
    )
    try:
        client = _get_client()
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.4,
                max_output_tokens=256,
            ),
        )
        import json
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        return json.loads(text)
    except Exception:
        return _fallback_coaching(user_action, gto_strategy)
