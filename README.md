Prop Firm Challenge Simulator
Overview
The Prop Firm Challenge Simulator is a specialized trading journal and simulation tool designed to help traders practice and validate their strategies against strict proprietary trading firm rules. It mimics the environment of a 2-step evaluation challenge, tracking equity, drawdown, and rule compliance in real-time.

Key Features
🎯 Challenge Simulation
Two-Phase Evaluation: Automatically tracks progress through Phase 1 (10% target) and Phase 2 (5% target).
Rule Enforcement: rigorously checks for violations of:
Max Daily Drawdown (5%)
Max Overall Drawdown (8%)
Max Loss Per Trade (2%)
Instant Feedback: Flags violations immediately and records failure events.
📊 Dashboard & Analytics
Interactive Equity Curve: Visualizes account growth over time.
Daily PnL Chart: Tracks daily performance to ensure consistency.
Real-time Status: Displays current balance, profit target progress, and pass/fail status.
📝 Trade Journaling
Detailed Logging: Record entry/exit prices, position size, strategy used, and reasoning.
Performance Tracking: Calculates PnL and duration for every trade.
Glassmorphism UI: A modern, clean interface for a premium user experience.
Technical Stack
Backend: Python, Flask, SQLAlchemy
Database: SQLite
Frontend: HTML5, CSS3 (Glassmorphism), Chart.js
