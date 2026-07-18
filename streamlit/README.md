# ♠️ Poker AI Coach — Streamlit Prototype

This folder contains the Streamlit front end for the Poker AI Coach project.

The current version is a **poker decision-training prototype**, not a complete playable poker game. A user can choose a poker situation manually or generate a random practice scenario, then click **Analyze Poker Decision** to receive a temporary raise, call, or fold recommendation.

The current recommendations use simplified hardcoded rules. When the team finishes the trained model, the recommendation function can be replaced with a model prediction while keeping the same Streamlit interface.

## What the App Currently Does

The Streamlit app has two tabs:

### 1. Poker Coach

The user can:

- Select a starting hand
- Select a table position
- Select what happened before their turn
- Enter stack size
- Enter pot size
- Enter the amount needed to call
- Generate a random practice scenario
- Analyze the decision

The app displays:

- The selected table position
- Two visual starting cards
- Raise percentage
- Call percentage
- Fold percentage
- A recommended action
- A short explanation
- Estimated pot odds

### 2. My Session

The app tracks:

- Number of scenarios analyzed
- Session length
- Number of aggressive recommendations
- Aggressive recommendation rate

This session information is stored temporarily with Streamlit session state.

---

## How to Run the App

From the project root, run:

```bash
python -m streamlit run streamlit/app.py