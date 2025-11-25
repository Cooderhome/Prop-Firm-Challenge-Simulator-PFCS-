from app import app, db
from models import Account, Trade, Failure

try:
    with app.app_context():
        print("Creating all tables...")
        db.create_all()
        print("Tables created successfully.")
        
        print("Checking for account...")
        if not Account.query.first():
            print("Seeding account...")
            acc = Account(
                start_balance=2500,
                profit_target=250,
                max_loss_per_trade_pct=0.01,
                max_drawdown=250,
                status="Active"
            )
            db.session.add(acc)
            db.session.commit()
            print("Account seeded successfully.")
        else:
            print("Account already exists.")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
