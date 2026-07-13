# Specification: PioSOLVER Data Pipeline & FastAPI GTO Spot Trainer

## Problem Statement
Traditional poker tools focus strictly on either GTO mathematical charts or manual game logs, leaving a massive gap for players who want to understand *why* a solver chooses a particular frequency. Additionally, identifying early behavioral tilt and **loss-chasing** traits in real-time is crucial for player longevity, but is neglected by standalone solvers.

## Solution
Build a dual-component backend that:
1.  Provides an automated local pipeline using Python's `subprocess` to parse heavy `.cfr` files via PioSOLVER's Universal Poker Interface (UPI), outputting compressed, highly queryable JSON state files.
2.  Provides a FastAPI web application that serves these GTO spots to an interactive training frontend, evaluates user decisions against true solver frequencies, uses an LLM coach to explain the strategic logic, and logs detailed behavior telemetry (**Bet**, **PrevOutcome**, **ResponseTime**) for downstream addiction screening analysis.

## User Stories
1.  **GTO Spot Loading:** As a training player, I want to fetch a randomized board spot (including board cards, hole cards, active positions, and pot sizes) so that I can practice different training spots.
2.  **GTO Evaluation:** As a training player, I want to make an action (Check, Bet, Fold) and instantly see the GTO solver's optimal frequencies for that entire node.
3.  **Natural Language Coaching:** As a training player, I want an AI Coach to explain in natural language the strategic reasoning (e.g. range advantage, blockers) behind the solver's preferred actions, especially if my action deviated from GTO.
4.  **Behavioral Telemetry Logging:** As an addiction researcher, I want the system to silently record each player's action, **Bet** size, **PrevOutcome**, and **ResponseTime** into a structured format so that I can run loss-chasing analysis.

## Implementation & Testing Decisions
*   **Database Schema:** SQLite/PostgreSQL with native JSON column mapping to store and query node-specific solver dictionaries.
*   **LLM Provider:** Connection via an official, asynchronous Python client (OpenAI or Gemini) using structured prompt inputs.
*   **Output Minimization:** Serialized strategy files must remain under 50KB per node.

## Test Seams
*   **FastAPI TestClient:** All functional API tests will run against endpoints via `TestClient` to preserve maximum refactoring freedom.
*   **Subprocess Standard I/O Mocks:** The PioSOLVER pipeline will be tested by mock-streaming stdout UPI matrices into the parser module, isolating tests from the solver binary.

## Out of Scope
*   **Full Game State Machine:** Multi-street complex betting hands (only single pre-solved node spots are served).
*   **Frontend UI implementation:** Handled by a separate React app repository/module.

## Triage
Label: `ready-for-agent`
