from datetime import datetime
from models import Trade

def compute_pnl(trade: Trade):
    """Compute PnL for a trade."""
    return (trade.exit_price - trade.entry_price) * trade.size * 100  # simplified


def apply_rules(trade: Trade, account):
    """
    Apply EquityEdge Legacy 2-step Challenge rules.
    Updates account.status accordingly.
    """
    violations = []
    pnl = compute_pnl(trade)
    trade.pnl = pnl
    trade.duration = (trade.exit_time - trade.entry_time).total_seconds() if trade.exit_time and trade.entry_time else 0

    # Update account balance dynamically
    balance = account.start_balance + sum(t.pnl for t in account.trades if t.pnl is not None)

    # ========== RULE PARAMETERS (Legacy 2-step) ==========
    phase = account.phase  # 1 or 2
    max_daily_drawdown_pct = 0.05
    max_overall_drawdown_pct = 0.08
    max_loss_per_trade_pct = 0.02
    profit_target_pct = 0.10 if phase == 1 else 0.05

    start_balance = account.start_balance
    profit_target = start_balance * profit_target_pct
    max_daily_drawdown = start_balance * max_daily_drawdown_pct
    max_overall_drawdown = start_balance * max_overall_drawdown_pct
    max_loss_per_trade = start_balance * max_loss_per_trade_pct

    # ========== RULE CHECKS ==========

    # 1️⃣ Max loss per trade
    if pnl < -max_loss_per_trade:
        violations.append(f"❌ Exceeded 2% max loss per trade (${abs(pnl):.2f} > ${max_loss_per_trade:.2f})")

    # 2️⃣ Max daily drawdown
    today_trades = [t for t in account.trades if t.entry_time.date() == trade.entry_time.date()]
    daily_pnl = sum(t.pnl for t in today_trades if t.pnl)
    if daily_pnl < -max_daily_drawdown:
        violations.append(f"❌ Max daily drawdown 5% breached (${daily_pnl:.2f})")

    # 3️⃣ Overall drawdown
    peak_balance = max(account.start_balance, *(account.start_balance + sum(t.pnl for t in account.trades[:i]) for i in range(len(account.trades))))
    if (peak_balance - balance) > max_overall_drawdown:
        violations.append(f"❌ Max overall drawdown 8% breached (${peak_balance - balance:.2f})")

    # 4️⃣ Profit target (Phase 1 → Phase 2 or Pass)
    total_profit = balance - start_balance
    if total_profit >= profit_target:
        if phase == 1:
            account.phase = 2
            account.status = "step1_passed"
        else:
            account.status = "passed"

    # 5️⃣ Failure condition
    if any("breached" in v for v in violations):
        account.status = "failed"
        account.failed_at = datetime.utcnow()

    # Attach violations
    trade.violation = " | ".join(violations) if violations else None

    return trade, account
