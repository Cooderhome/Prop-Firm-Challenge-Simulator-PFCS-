import click
from flask import Flask, render_template, request, redirect, session, url_for
from flask.cli import with_appcontext
from models import Failure, db, Account, Trade
from rules import apply_rules
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trades.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = b'\xcf\x93,\xbb\xf1\xb27\xaf\x1b\xd0i\xa8\x1bQYI\xa6\x93\x8fO_\x9a\xd0\xac'
db.init_app(app)


# ------------------ CLI COMMAND ------------------ #
@click.command("init-db")
@with_appcontext
def init_db_command():
    """Initialize the database and seed a trading account."""
    db.create_all()

    if not Account.query.first():
        acc = Account(
            start_balance=2500,
            profit_target=250,
            max_loss_per_trade_pct=0.01,
            max_drawdown=250,
            status="Active"
        )
        db.session.add(acc)
        db.session.commit()
        click.echo("✅ Database initialized and account seeded.")
    else:
        click.echo("ℹ️ Database already initialized.")

# Register command to Flask CLI
app.cli.add_command(init_db_command)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Simple demo auth
        if username == 'admin' and password == '1234':
            session['user'] = username
            return redirect(url_for('dashboard'))
        else:
            error = "Invalid credentials"
    return render_template('login.html', error=error)
users = {}  # simple in-memory user store

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if username in users:
            error = "Username already exists!"
        else:
            users[username] = {'email': email, 'password': password}
            session['user'] = username
            return redirect(url_for('dashboard'))

    return render_template('register.html', error=error)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

# ------------------ DASHBOARD ------------------ #
@app.route('/dashboard')
def dashboard():
    account = Account.query.first()

    # Auto-seed account if none exists
    if not account:
        account = Account(
            start_balance=2500,
            profit_target=250,
            max_loss_per_trade_pct=0.01,
            max_drawdown=250,
            status="Active"
        )
        db.session.add(account)
        db.session.commit()

    trades = account.trades
    balance = account.start_balance + sum(t.pnl or 0 for t in trades)
    profit = balance - account.start_balance

    # --- Equity curve ---
    equity_curve = []
    running_balance = account.start_balance
    for t in sorted(trades, key=lambda x: x.exit_time or x.entry_time):
        if t.pnl:
            running_balance += t.pnl
        equity_curve.append({
            "time": (t.exit_time or t.entry_time).strftime("%Y-%m-%d %H:%M"),
            "balance": running_balance
        })

    # --- Rules check ---
    rules = {}
    rules["Profit Target"] = profit >= account.profit_target

    lowest_balance = min([p["balance"] for p in equity_curve] or [balance])
    rules["Max Drawdown"] = (account.start_balance - lowest_balance) <= account.max_drawdown

    daily_limit = -0.05 * account.start_balance
    rules["Daily Loss Limit"] = all((t.pnl or 0) >= daily_limit for t in trades)
    rules["Min Duration"] = all((t.duration or 0) >= 120 for t in trades if t.duration)

    # --- Check for rule violations ---
    failed_rules = [r for r, passed in rules.items() if not passed]
    if failed_rules:
        for fr in failed_rules:
            failure = Failure(
                rule=fr,
                pnl_at_failure=profit,
                balance_at_failure=balance
            )
            db.session.add(failure)
        db.session.commit()

        # Reset account automatically
        Trade.query.delete()
        account.start_balance = 2500
        account.status = "Active"
        db.session.commit()

    failures = Failure.query.order_by(Failure.timestamp.desc()).all()

    return render_template(
        "dashboard.html",
        account=account,
        trades=trades,
        balance=balance,
        profit=profit,
        equity_curve=equity_curve,
        rules=rules,
        failures=failures
    )


# ------------------ ADD TRADE ------------------ #
@app.route('/add', methods=['GET', 'POST'])
def add_trade():
    account = Account.query.first()
    if not account:
        return "⚠️ No account found. Please initialize the database first."

    if request.method == 'POST':
        symbol = request.form['symbol']
        entry = float(request.form['entry_price'])
        exitp = float(request.form['exit_price'])
        size = float(request.form['size'])
        strategy = request.form['strategy']
        reason = request.form['reason']
        entry_time = datetime.strptime(request.form['entry_time'], "%Y-%m-%d %H:%M:%S")
        exit_time = datetime.strptime(request.form['exit_time'], "%Y-%m-%d %H:%M:%S")

        trade = Trade(
            account=account,
            symbol=symbol,
            entry_price=entry,
            exit_price=exitp,
            size=size,
            strategy=strategy,
            reason=reason,
            entry_time=entry_time,
            exit_time=exit_time
        )

        trade, account = apply_rules(trade, account)
        db.session.add(trade)
        db.session.commit()
        return redirect(url_for('dashboard'))

    return render_template("add_trade.html")


# ------------------ RESET ACCOUNT ------------------ #
@app.route('/reset_account', methods=['POST'])
def reset_account():
    account = Account.query.first()
    if account:
        Trade.query.delete()
        db.session.commit()

        account.start_balance = 2500
        account.status = "Active"
        db.session.commit()
    return redirect(url_for('dashboard'))


# ------------------ APP INIT ------------------ #
if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        if not Account.query.first():
            acc = Account(
                start_balance=2500,
                profit_target=250,
                max_loss_per_trade_pct=0.01,
                max_drawdown=250,
                status="Active"
            )
            db.session.add(acc)
            db.session.commit()

    app.run(debug=True)
