# Poker Arena — Game + Learning Coach

This project contains two modes in one Streamlit application:

- Vs Computer: play complete simplified heads-up Hold'em hands against a heuristic bot.
- Multiplayer: create or join a room and play another person with WebSocket-driven live updates.

The optional Learning Coach privately reviews each decision after it is made. It shows a decision score, suggested action, simplified action mix, estimated hand strength, pot odds, and an explanation. The percentages are educational heuristics and are not exact GTO solver outputs.

## Install

```powershell
python -m pip install -r requirements.txt
```

## Run

Terminal 1:

```powershell
python -m uvicorn backend:app --reload --port 8000
```

Terminal 2:

```powershell
python -m streamlit run app.py
```

For multiplayer testing, open the Streamlit URL in a normal browser window and an Incognito/InPrivate window. Create a room in one and join from the other.

Set `POKER_API_URL` to your deployed FastAPI URL when deploying the frontend separately.
