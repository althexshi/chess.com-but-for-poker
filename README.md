# Poker AI Coach with Addiction Screening

## How to Install and Setup

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

This installs the project's dependencies (pandas, seaborn, matplotlib, scipy), the `jupyter`/`jupyterlab` dev tooling, and makes `poker_coach` (the code in `src/poker_coach`) importable from the notebooks.

### 4. Tell your editor where Python is (Configure IDE)

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