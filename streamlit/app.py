import time

import httpx
import streamlit as st

API_BASE = "http://127.0.0.1:8000"


# =========================================================
# PAGE SETUP
# =========================================================
st.set_page_config(
    page_title="Poker AI Coach",
    page_icon="♠️",
    layout="wide",
)


# =========================================================
# SESSION STATE
# =========================================================
def initialize_session() -> None:
    defaults = {
        "username": "",
        "logged_in": False,
        "scenario": None,
        "user_action": None,
        "action_start_time": None,
        "last_result": None,
        "show_result": False,
        "scenarios_completed": 0,
        "session_start": time.time(),
        "verdicts": [],
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


initialize_session()


# =========================================================
# STYLING
# =========================================================
st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.4rem;
        font-weight: 800;
        margin-bottom: 0.1rem;
    }

    .subtitle {
        color: #9ca3af;
        margin-bottom: 1.2rem;
    }

    .poker-table {
        width: 560px;
        height: 320px;
        border-radius: 50%;
        background: radial-gradient(circle, #166534 0%, #064e3b 72%);
        border: 7px solid #5b3a1f;
        position: relative;
        margin: 20px auto;
        box-shadow: 0 0 30px rgba(0,0,0,0.45);
    }

    .seat {
        position: absolute;
        background-color: #111827;
        color: white;
        padding: 10px 14px;
        border-radius: 12px;
        font-weight: bold;
        text-align: center;
        border: 2px solid #374151;
        min-width: 72px;
    }

    .active-seat {
        border: 3px solid #22c55e;
        color: #22c55e;
        box-shadow: 0 0 14px rgba(34,197,94,0.6);
    }

    .pot {
        position: absolute;
        top: 128px;
        left: 220px;
        color: white;
        font-size: 22px;
        font-weight: bold;
        text-align: center;
    }

    .co { top: 18px; left: 235px; }
    .hj { top: 100px; left: 35px; }
    .btn { top: 100px; right: 35px; }
    .utg { bottom: 35px; left: 95px; }
    .bb { bottom: 22px; left: 240px; }
    .sb { bottom: 35px; right: 95px; }

    .info-card {
        padding: 1rem;
        border-radius: 14px;
        border: 1px solid rgba(255,255,255,0.12);
        background: rgba(255,255,255,0.04);
        margin-bottom: 1rem;
    }

    .coaching-card {
        padding: 1.2rem;
        border-radius: 16px;
        margin-top: 1rem;
    }
    .coaching-good {
        border: 1px solid rgba(34,197,94,0.35);
        background: rgba(34,197,94,0.08);
    }
    .coaching-okay {
        border: 1px solid rgba(234,179,8,0.35);
        background: rgba(234,179,8,0.08);
    }
    .coaching-mistake {
        border: 1px solid rgba(239,68,68,0.35);
        background: rgba(239,68,68,0.08);
    }

    .verdict-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 8px;
        font-weight: 700;
        font-size: 0.85rem;
        text-transform: uppercase;
        margin-right: 8px;
    }
    .verdict-good { background: #166534; color: #4ade80; }
    .verdict-okay { background: #854d0e; color: #facc15; }
    .verdict-mistake { background: #991b1b; color: #fca5a5; }

    .concept-tag {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 6px;
        background: rgba(99,102,241,0.15);
        color: #a5b4fc;
        font-size: 0.8rem;
        font-weight: 600;
    }

    .playing-card {
        display: inline-block;
        width: 78px;
        height: 110px;
        background: white;
        color: #111827;
        border-radius: 10px;
        margin-right: 10px;
        padding: 10px;
        font-size: 24px;
        font-weight: 800;
        box-shadow: 0 8px 20px rgba(0,0,0,0.25);
        vertical-align: top;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# HELPERS
# =========================================================
POSITIONS = ["UTG", "HJ", "CO", "BTN", "SB", "BB"]

VERDICT_EMOJI = {"good": "✅", "okay": "⚠️", "mistake": "❌"}


def seat_class(seat_name: str, selected_position: str) -> str:
    base_class = seat_name.lower()
    if seat_name == selected_position:
        return f"seat {base_class} active-seat"
    return f"seat {base_class}"


def parse_hole_cards(hole_cards: str) -> tuple[str, str, str, str]:
    suits = {"s": "♠", "h": "♥", "d": "♦", "c": "♣"}
    card1_rank = hole_cards[0]
    card1_suit = suits.get(hole_cards[1].lower(), "")
    card2_rank = hole_cards[2]
    card2_suit = suits.get(hole_cards[3].lower(), "") if len(hole_cards) > 3 else ""
    return card1_rank, card1_suit, card2_rank, card2_suit


def fetch_scenario() -> None:
    try:
        resp = httpx.get(f"{API_BASE}/api/scenarios/next", timeout=5.0)
        resp.raise_for_status()
        st.session_state.scenario = resp.json()
        st.session_state.show_result = False
        st.session_state.last_result = None
        st.session_state.user_action = None
        st.session_state.action_start_time = time.time()
    except httpx.HTTPError as e:
        st.error(f"Could not load scenario: {e}")


def submit_action(action: str) -> None:
    scenario = st.session_state.scenario
    if scenario is None:
        return

    response_time_ms = None
    if st.session_state.action_start_time:
        response_time_ms = int(
            (time.time() - st.session_state.action_start_time) * 1000
        )

    prev_outcome = None
    if st.session_state.verdicts:
        prev_outcome = st.session_state.verdicts[-1]

    try:
        resp = httpx.post(
            f"{API_BASE}/api/evaluate",
            json={
                "scenario_id": scenario["id"],
                "username": st.session_state.username,
                "action": action,
                "response_time_ms": response_time_ms,
                "prev_outcome": prev_outcome,
            },
            timeout=15.0,
        )
        resp.raise_for_status()
        result = resp.json()
        st.session_state.last_result = result
        st.session_state.user_action = action
        st.session_state.show_result = True
        st.session_state.scenarios_completed += 1
        st.session_state.verdicts.append(result["coaching"]["verdict"])
    except httpx.HTTPError as e:
        st.error(f"Evaluation failed: {e}")


def reset_session() -> None:
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    initialize_session()


# =========================================================
# LOGIN GATE
# =========================================================
if not st.session_state.logged_in:
    st.markdown(
        '<div class="main-title">♠️ Poker AI Coach</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="subtitle">Enter a username to start practicing.</div>',
        unsafe_allow_html=True,
    )
    username = st.text_input("Username", max_chars=30)
    if st.button("Start Training", type="primary"):
        if username.strip():
            st.session_state.username = username.strip()
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.warning("Please enter a username.")
    st.stop()


# =========================================================
# HEADER
# =========================================================
st.markdown(
    '<div class="main-title">♠️ Poker AI Coach</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="subtitle">'
    f"Playing as <strong>{st.session_state.username}</strong> · "
    "Practice poker decisions and review your session activity."
    "</div>",
    unsafe_allow_html=True,
)

coach_tab, session_tab = st.tabs(["Poker Coach", "My Session"])


# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.header("Controls")

    if st.button("Deal New Scenario", use_container_width=True, type="primary"):
        fetch_scenario()
        st.rerun()

    if st.button("Reset Session", use_container_width=True):
        reset_session()
        st.rerun()

    st.divider()
    st.caption(
        f"Logged in as **{st.session_state.username}** · "
        f"Scenarios completed: {st.session_state.scenarios_completed}"
    )


# =========================================================
# POKER COACH TAB
# =========================================================
with coach_tab:
    scenario = st.session_state.scenario

    if scenario is None:
        st.info("Click **Deal New Scenario** in the sidebar to begin.")
        st.stop()

    left_col, right_col = st.columns([1.45, 1])

    with left_col:
        st.subheader("Table View")

        position = scenario["position"]
        pot_size = scenario["pot_size"]

        table_html = f"""
<div class="poker-table">
    <div class="{seat_class('CO', position)}">CO<br>100 bb</div>
    <div class="{seat_class('HJ', position)}">HJ<br>100 bb</div>
    <div class="{seat_class('BTN', position)}">BTN<br>100 bb</div>
    <div class="{seat_class('UTG', position)}">UTG<br>100 bb</div>
    <div class="{seat_class('BB', position)}">BB<br>99 bb</div>
    <div class="{seat_class('SB', position)}">SB<br>99.5 bb</div>
    <div class="pot">POT<br>{pot_size:.1f} bb</div>
</div>
"""
        st.markdown(table_html, unsafe_allow_html=True)

        card1_rank, card1_suit, card2_rank, card2_suit = parse_hole_cards(
            scenario["hole_cards"]
        )

        st.markdown("#### Your Hole Cards")
        st.markdown(
            f'<div class="playing-card">{card1_rank}<br><br>{card1_suit}</div>'
            f'<div class="playing-card">{card2_rank}<br><br>{card2_suit}</div>',
            unsafe_allow_html=True,
        )

        st.markdown(f"**Board:** {scenario['board']}")

    with right_col:
        st.subheader("Decision Details")

        st.markdown(
            f"""
<div class="info-card">
    <strong>Position:</strong> {scenario['position']}<br>
    <strong>Opponent action:</strong> {scenario['opponent_action']}<br>
    <strong>Stack:</strong> {scenario['stack_size']:.0f} big blinds<br>
    <strong>Pot:</strong> {scenario['pot_size']:.1f} big blinds
</div>
""",
            unsafe_allow_html=True,
        )

        if not st.session_state.show_result:
            st.markdown("#### Choose your action:")
            action_cols = st.columns(3)
            with action_cols[0]:
                if st.button("Raise", use_container_width=True):
                    submit_action("raise")
                    st.rerun()
            with action_cols[1]:
                if st.button("Call", use_container_width=True):
                    submit_action("call")
                    st.rerun()
            with action_cols[2]:
                if st.button("Fold", use_container_width=True):
                    submit_action("fold")
                    st.rerun()

            actions_with_bet = ["check", "bet"]
            extra_cols = st.columns(2)
            with extra_cols[0]:
                if st.button("Check", use_container_width=True):
                    submit_action("check")
                    st.rerun()
            with extra_cols[1]:
                if st.button("Bet", use_container_width=True):
                    submit_action("bet")
                    st.rerun()

        if st.session_state.show_result and st.session_state.last_result:
            result = st.session_state.last_result
            comparison = result["comparison"]
            coaching = result["coaching"]
            gto = comparison["gto_strategy"]

            st.markdown("### GTO Action Frequencies")
            for action_name, freq in gto.items():
                st.write(f"{action_name.capitalize()} — {freq:.0f}%")
                st.progress(freq / 100)

            verdict = coaching["verdict"]
            emoji = VERDICT_EMOJI.get(verdict, "")
            card_class = f"coaching-{verdict}"
            badge_class = f"verdict-{verdict}"

            st.markdown(
                f"""
<div class="coaching-card {card_class}">
    <div style="margin-bottom: 8px;">
        <span class="verdict-badge {badge_class}">{emoji} {verdict}</span>
        <span class="concept-tag">{coaching['concept']}</span>
    </div>
    <p style="margin: 6px 0;"><strong>You chose:</strong> {st.session_state.user_action}</p>
    <p style="margin: 6px 0;">{coaching['summary']}</p>
    <p style="margin: 6px 0; opacity: 0.85;"><em>{coaching['advice']}</em></p>
</div>
""",
                unsafe_allow_html=True,
            )

            if st.button("Next Scenario →", type="primary", use_container_width=True):
                fetch_scenario()
                st.rerun()


# =========================================================
# MY SESSION TAB
# =========================================================
with session_tab:
    st.header("My Session")

    session_minutes = int(
        (time.time() - st.session_state.session_start) / 60
    )

    verdicts = st.session_state.verdicts
    good_count = verdicts.count("good")
    mistake_count = verdicts.count("mistake")
    total = len(verdicts)

    metric1, metric2, metric3, metric4 = st.columns(4)

    with metric1:
        st.metric("Scenarios analyzed", total)

    with metric2:
        st.metric("Session length", f"{session_minutes} min")

    with metric3:
        st.metric("Good decisions", good_count)

    with metric4:
        accuracy = f"{good_count / total:.0%}" if total > 0 else "—"
        st.metric("Accuracy", accuracy)

    if total > 0:
        st.markdown("### Decision History")
        for i, v in enumerate(reversed(verdicts), 1):
            emoji = VERDICT_EMOJI.get(v, "")
            st.write(f"{emoji} Scenario {total - i + 1}: **{v}**")

    st.markdown("### Current Session Status")

    if session_minutes >= 60:
        st.warning(
            "You have been practicing for at least one hour. "
            "Consider taking a break."
        )
    elif total >= 25:
        st.warning(
            "You have completed many scenarios in one session. "
            "A short break may be helpful."
        )
    else:
        st.success(
            "No concerning session pattern has been detected."
        )

    st.caption(
        "This session summary is not a diagnosis. It only reports activity "
        "inside this practice app."
    )
