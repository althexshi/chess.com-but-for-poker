# Poker AI Coach with Addiction Screening

An AI poker coach that teaches Hold'em strategy while silently logging behavioral telemetry (bet sizes, outcomes, response times) to screen for loss-chasing and gambling-risk patterns.

The project has two threads:

- **Play/learn:** a Streamlit poker app (playable now) — heads-up Hold'em vs. a bot or another person, with an optional Learning Coach that scores each decision.
- **Research:** notebooks analyzing a real gambling dataset (bustabit) for loss-chasing behavior, feeding an XGBoost model that screens players into risk tiers. A FastAPI backend for a solver-driven GTO trainer exists but isn't wired to a frontend yet — see [Status](#status) below.

## Project layout

| Path | What it is |
|---|---|
| `streamlit/` | Playable Streamlit poker app + its own FastAPI multiplayer backend |
| `src/poker_coach/api/` | FastAPI backend for the GTO spot trainer (scenarios, evaluation, telemetry) |
| `src/poker_coach/upi_parser.py`, `upi_engine.py`, `pipeline.py` | PioSOLVER integration — parses solver output into scenario JSON |
| `notebooks/` | Data exploration and the risk-tier model training/evaluation |
| `Data/` | `bustabit.csv` (raw gambling data), `player_stats.csv` (engineered features), `sample_scenarios.json` (GTO trainer seed data) |
| `models/` | Trained `xgboost_risk_screener.pkl` |
| `tests/` | pytest suite for the API, pipeline, and UPI parser/engine |
| `plans/backend_spec.md` | Spec for the GTO trainer backend |

## Setup

### 1. Clone the repo

**HTTPS**
```bash
git clone https://github.com/althexshi/chess.com-but-for-poker.git
```

**SSH**
```bash
git clone git@github.com:althexshi/chess.com-but-for-poker.git
```

### 2. Create a virtual environment

**Windows**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -e ".[dev]"
```

This installs everything: data analysis (pandas, seaborn, matplotlib, scipy, scikit-learn, xgboost, imbalanced-learn), the FastAPI/Streamlit app stack, and the `jupyter`/`pytest` dev tooling — and makes `poker_coach` (the code in `src/poker_coach`) importable from the notebooks. One `pip install` covers the Streamlit app too; you don't need to separately install `streamlit/requirements.txt`.

### 4. Environment variables

The GTO trainer backend's LLM coaching feature (`src/poker_coach/api/coach.py`) uses Gemini via Vertex AI, configured through a `.env` file at the project root:

```env
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_CLOUD_LOCATION=global
GOOGLE_GENAI_USE_VERTEXAI=True
```

This is only needed if you're running the FastAPI GTO backend's coaching endpoint. The Streamlit app's Learning Coach is a self-contained heuristic and needs no API key.

### 5. Tell your editor where Python is (Configure IDE)

Your IDE needs to know to use the venv's Python, not your system Python. If you skip this, you'll see errors like "Import pandas could not be resolved."

**VS Code:**

- Press `Cmd+Shift+P` (Mac) or `Ctrl+Shift+P` (Windows/Linux)
- Type `Python: Select Interpreter`
- Pick the one from your venv:
  - **Mac/Linux:** `./venv/bin/python`
  - **Windows:** `./venv/Scripts/python.exe`

**PyCharm:**

- Go to PyCharm → Settings → Project → Python Interpreter
- Click the ⚙️ icon and choose "Add..."
- Select "Existing Environment" and pick:
  - **Mac/Linux:** `venv/bin/python`
  - **Windows:** `venv/Scripts/python.exe`

**Other editors:**
Look for a way to set your project's Python interpreter path to `./venv/bin/python` (Mac/Linux) or `./venv/Scripts/python.exe` (Windows). This is usually in settings under "Python" or "Interpreter."

## Running the Streamlit poker app

```bash
python -m streamlit run streamlit/app.py
```

That's enough for **Vs Computer** mode — play a full heads-up hand against a heuristic bot, with the Learning Coach toggle available in the sidebar.

**Multiplayer** mode needs the app's own backend running first, in a separate terminal:

```bash
cd streamlit
python -m uvicorn backend:app --reload --port 8000
```

Then open the Streamlit URL in two browser windows (e.g. one normal, one Incognito) to create a room in one and join from the other. If you deploy the frontend and backend separately, point the app at your backend with `POKER_API_URL`. More detail in [`streamlit/README.md`](streamlit/README.md).

## Running the GTO trainer backend

```bash
uvicorn poker_coach.api.main:app --reload
```

Serves scenarios and evaluates user actions against solver frequencies at `/api/scenarios/next` and `/api/evaluate`, logging telemetry to a local SQLite DB. Load scenario data first:

```bash
python -m poker_coach.ingest Data/sample_scenarios.json
```

Note: this backend isn't currently called by the Streamlit app — the two were built as separate efforts. Exercise it via the tests or `httpx`/`curl` for now.

## Notebooks

```bash
jupyter lab
```

Notebooks in `notebooks/` walk through the bustabit data exploration, loss-chasing and bet-size analysis, and the risk-tier model's training/evaluation (`05_training_and_testing.ipynb`), plus a few supplementary analyses (cross-validation, escalation magnitude, player segmentation).

## Tests

```bash
pytest
```

## Status

- ✅ Streamlit poker app (Vs Computer + Multiplayer) — playable
- ✅ Risk-tier XGBoost model — trained, evaluated in `notebooks/05_training_and_testing.ipynb`
- 🚧 FastAPI GTO trainer backend — built and tested, not yet wired to a frontend
- 🚧 Gemini/Vertex AI coaching — implemented in `coach.py`, not yet called from the API routes
