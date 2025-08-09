from backend.app import app, db

with app.app_context():
    db.drop_all()
    db.create_all()
    print("Dropped & recreated all tables successfully.")
