from pathlib import Path

# These are the file paths used
# __file__ — the location of config.py itself
# .resolve() — get the full absolute path
# .parents[2] — go up two folders (from config.py → poker_coach → src → project root)
# / "Data" — then go into the Data folder
DATA_DIR = Path(__file__).resolve().parents[2] / "Data"

BUSTABIT_DATA_FILE = DATA_DIR / "bustabit.csv"
PLAYER_STATS_FILE = DATA_DIR / "player_stats.csv"

MODELS_DIR = Path(__file__).resolve().parents[2] / "models"
RISK_SCREENER_MODEL_FILE = MODELS_DIR / "xgboost_risk_screener.pkl"

#Bustabit data scheme and columns
DATA_COLUMNS = ['Bet','CashedOut', 'Bonus', 'Profit', 'BustedAt']
ID_COLS = ['Id', 'GameID']

# Bet, Bonus, and Profit are recorded in "bits" (1 bit = 0.000001 BTC). CashedOut and
# BustedAt are payout multipliers, not currency, so they're never converted.
BITS_PER_BTC = 1_000_000
BTC_USD_RATE = 750  # approx. BTC/USD price over the dataset's Nov-Dec 2016 window

# Shared Visualization Palettes
GRAPE_SODA = "#8a4f7d"
MUTED_TEAL = "#88a096"
ROSY_GRANITE = "#887880"
KHAKI_BEIGE = "#BBAB8B"
SWEET_SALMON = "#ef8275"

