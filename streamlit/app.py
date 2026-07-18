import random
import time

import streamlit as st


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
        "hand": "AA",
        "position": "UTG",
        "opponent_action": "Everyone folded",
        "stack_size": 100,
        "pot_size": 10.0,
        "call_amount": 2.5,
        "scenarios_completed": 0,
        "session_start": time.time(),
        "aggressive_recommendations": 0,
        "last_recommendation": None,
        "show_result": False,
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

    .recommendation-card {
        padding: 1.2rem;
        border-radius: 16px;
        border: 1px solid rgba(34,197,94,0.35);
        background: rgba(34,197,94,0.08);
        margin-top: 1rem;
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
HANDS = [
    "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77",
    "AKs", "AKo", "AQs", "AQo", "AJs", "ATs",
    "KQs", "KJs", "QJs", "JTs", "T9s", "QJo",
]

POSITIONS = ["UTG", "HJ", "CO", "BTN", "SB", "BB"]

ACTIONS = [
    "Everyone folded",
    "One player called",
    "One player raised",
    "Raise and re-raise",
]


def seat_class(seat_name: str, selected_position: str) -> str:
    base_class = seat_name.lower()
    if seat_name == selected_position:
        return f"seat {base_class} active-seat"
    return f"seat {base_class}"


def split_hand_label(hand: str) -> tuple[str, str]:
    return hand[0], hand[1]


def deal_practice_scenario() -> None:
    st.session_state.hand = random.choice(HANDS)
    st.session_state.position = random.choice(POSITIONS)
    st.session_state.opponent_action = random.choice(ACTIONS)
    st.session_state.stack_size = random.choice([20, 30, 50, 75, 100, 150])
    st.session_state.pot_size = random.choice([3.0, 5.0, 7.5, 10.0, 15.0])
    st.session_state.call_amount = random.choice([0.0, 1.0, 2.0, 2.5, 5.0])
    st.session_state.show_result = False
    st.session_state.last_recommendation = None


def get_recommendation(
    hand: str,
    position: str,
    opponent_action: str,
    stack_size: int,
) -> tuple[int, int, int, str, str]:
    """
    Temporary hardcoded poker logic.

    Later, replace the inside of this function with the trained model.
    """
    premium_hands = {"AA", "KK", "QQ", "JJ", "AKs", "AKo"}
    playable_hands = {
        "TT", "99", "88", "77",
        "AQs", "AQo", "AJs", "ATs",
        "KQs", "KJs", "QJs", "JTs", "T9s",
    }
    late_positions = {"CO", "BTN"}

    if hand in premium_hands:
        raise_pct, call_pct, fold_pct = 78, 18, 4
        recommendation = "Raise"
        explanation = (
            "This is a premium starting hand. Raising is usually reasonable, "
            "although stack size and earlier action still matter."
        )

    elif hand in playable_hands:
        if (
            position in late_positions
            and opponent_action in {"Everyone folded", "One player called"}
        ):
            raise_pct, call_pct, fold_pct = 48, 37, 15
            recommendation = "Raise or call"
            explanation = (
                "This hand is more playable from a later position because you "
                "have more information about the other players."
            )
        else:
            raise_pct, call_pct, fold_pct = 28, 44, 28
            recommendation = "Call or play carefully"
            explanation = (
                "This hand has potential, but earlier position or aggressive "
                "opponent action makes it less comfortable."
            )

    else:
        raise_pct, call_pct, fold_pct = 10, 20, 70
        recommendation = "Fold or play carefully"
        explanation = (
            "This is a weaker starting hand in this simplified prototype."
        )

    if opponent_action == "Raise and re-raise":
        raise_pct = max(5, raise_pct - 15)
        call_pct = max(10, call_pct - 5)
        fold_pct = 100 - raise_pct - call_pct
        explanation += " A raise and re-raise before your turn increases the risk."

    if stack_size <= 25:
        explanation += " Your stack is short, so short-stack strategy matters."

    return raise_pct, call_pct, fold_pct, recommendation, explanation


def analyze_scenario() -> None:
    (
        raise_pct,
        call_pct,
        fold_pct,
        recommendation,
        explanation,
    ) = get_recommendation(
        hand=st.session_state.hand,
        position=st.session_state.position,
        opponent_action=st.session_state.opponent_action,
        stack_size=st.session_state.stack_size,
    )

    st.session_state.last_recommendation = {
        "raise_pct": raise_pct,
        "call_pct": call_pct,
        "fold_pct": fold_pct,
        "recommendation": recommendation,
        "explanation": explanation,
    }

    st.session_state.scenarios_completed += 1

    if recommendation in {"Raise", "Raise or call"}:
        st.session_state.aggressive_recommendations += 1

    st.session_state.show_result = True


def reset_session() -> None:
    for key in list(st.session_state.keys()):
        del st.session_state[key]

    initialize_session()


# =========================================================
# HEADER
# =========================================================
st.markdown(
    '<div class="main-title">♠️ Poker AI Coach</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="subtitle">'
    "Practice poker decisions and review your session activity."
    "</div>",
    unsafe_allow_html=True,
)

coach_tab, session_tab = st.tabs(["Poker Coach", "My Session"])


# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.header("Practice Settings")

    st.selectbox(
        "Starting hand",
        HANDS,
        key="hand",
        help="s = suited, o = offsuit",
    )

    st.selectbox(
        "Your position",
        POSITIONS,
        key="position",
    )

    st.selectbox(
        "Action before your turn",
        ACTIONS,
        key="opponent_action",
    )

    st.slider(
        "Your stack size (big blinds)",
        min_value=10,
        max_value=200,
        step=5,
        key="stack_size",
    )

    st.number_input(
        "Pot size (big blinds)",
        min_value=0.0,
        step=0.5,
        key="pot_size",
    )

    st.number_input(
        "Amount to call (big blinds)",
        min_value=0.0,
        step=0.5,
        key="call_amount",
    )

    st.divider()

    if st.button("Deal Practice Scenario", use_container_width=True):
        deal_practice_scenario()
        st.rerun()

    if st.button("Reset Session", use_container_width=True):
        reset_session()
        st.rerun()

    st.caption(
        "This is a practice simulator. The recommendation logic is temporary "
        "and can later be replaced with the trained model."
    )


# =========================================================
# POKER COACH TAB
# =========================================================
with coach_tab:
    left_col, right_col = st.columns([1.45, 1])

    with left_col:
        st.subheader("Table View")

        table_html = f"""
<div class="poker-table">
    <div class="{seat_class('CO', st.session_state.position)}">CO<br>100 bb</div>
    <div class="{seat_class('HJ', st.session_state.position)}">HJ<br>100 bb</div>
    <div class="{seat_class('BTN', st.session_state.position)}">BTN<br>100 bb</div>
    <div class="{seat_class('UTG', st.session_state.position)}">UTG<br>100 bb</div>
    <div class="{seat_class('BB', st.session_state.position)}">BB<br>99 bb</div>
    <div class="{seat_class('SB', st.session_state.position)}">SB<br>99.5 bb</div>
    <div class="pot">POT<br>{st.session_state.pot_size:.1f} bb</div>
</div>
"""
        st.markdown(table_html, unsafe_allow_html=True)

        card_one, card_two = split_hand_label(st.session_state.hand)

        if st.session_state.hand.endswith("s"):
            suited_text = "Suited"
            first_suit = "♠"
            second_suit = "♠"
        elif st.session_state.hand.endswith("o"):
            suited_text = "Offsuit"
            first_suit = "♠"
            second_suit = "♥"
        else:
            suited_text = "Pocket pair"
            first_suit = "♠"
            second_suit = "♥"

        st.markdown("#### Your Starting Hand")
        st.markdown(
            f"""
<div class="playing-card">{card_one}<br><br>{first_suit}</div>
<div class="playing-card">{card_two}<br><br>{second_suit}</div>
""",
            unsafe_allow_html=True,
        )
        st.caption(f"{st.session_state.hand} · {suited_text}")

    with right_col:
        st.subheader("Decision Details")

        st.markdown(
            f"""
<div class="info-card">
    <strong>Position:</strong> {st.session_state.position}<br>
    <strong>Opponent action:</strong> {st.session_state.opponent_action}<br>
    <strong>Stack:</strong> {st.session_state.stack_size} big blinds<br>
    <strong>Pot:</strong> {st.session_state.pot_size:.1f} big blinds<br>
    <strong>Amount to call:</strong> {st.session_state.call_amount:.1f} big blinds
</div>
""",
            unsafe_allow_html=True,
        )

        if st.button(
            "Analyze Poker Decision",
            type="primary",
            use_container_width=True,
        ):
            analyze_scenario()
            st.rerun()

        if st.session_state.show_result and st.session_state.last_recommendation:
            result = st.session_state.last_recommendation

            st.markdown("### Action Mix")

            st.write(f"Raise — {result['raise_pct']}%")
            st.progress(result["raise_pct"] / 100)

            st.write(f"Call — {result['call_pct']}%")
            st.progress(result["call_pct"] / 100)

            st.write(f"Fold — {result['fold_pct']}%")
            st.progress(result["fold_pct"] / 100)

            st.markdown(
                f"""
<div class="recommendation-card">
    <h3>Recommended action: {result['recommendation']}</h3>
    <p>{result['explanation']}</p>
</div>
""",
                unsafe_allow_html=True,
            )

            if st.session_state.call_amount > 0:
                pot_odds = (
                    st.session_state.call_amount
                    / (
                        st.session_state.pot_size
                        + st.session_state.call_amount
                    )
                )
                st.metric("Estimated pot odds", f"{pot_odds:.2%}")

            with st.expander("What do these percentages mean?"):
                st.write(
                    "These are simplified hardcoded examples for the prototype. "
                    "Later, they can be replaced by probabilities or strategy "
                    "frequencies produced by the trained model."
                )
        else:
            st.info(
                "Choose a situation or click Deal Practice Scenario, then press "
                "Analyze Poker Decision."
            )


# =========================================================
# MY SESSION TAB
# =========================================================
with session_tab:
    st.header("My Session")

    session_minutes = int(
        (time.time() - st.session_state.session_start) / 60
    )

    if st.session_state.scenarios_completed > 0:
        aggressive_rate = (
            st.session_state.aggressive_recommendations
            / st.session_state.scenarios_completed
        )
    else:
        aggressive_rate = 0

    metric1, metric2, metric3, metric4 = st.columns(4)

    with metric1:
        st.metric(
            "Scenarios analyzed",
            st.session_state.scenarios_completed,
        )

    with metric2:
        st.metric(
            "Session length",
            f"{session_minutes} min",
        )

    with metric3:
        st.metric(
            "Aggressive recommendations",
            st.session_state.aggressive_recommendations,
        )

    with metric4:
        st.metric(
            "Aggressive rate",
            f"{aggressive_rate:.0%}",
        )

    st.markdown("### Current Session Status")

    if session_minutes >= 60:
        st.warning(
            "You have been practicing for at least one hour. "
            "Consider taking a break."
        )
    elif st.session_state.scenarios_completed >= 25:
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