from backend.app import app, db, User
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password"  

with app.app_context():
    admin = User.query.filter_by(username=ADMIN_USERNAME).first()
    if admin:
        admin.is_admin = True
        admin.password = generate_password_hash(ADMIN_PASSWORD)
        db.session.commit()
        print(f"✅ Admin user ensured (username={ADMIN_USERNAME}). Password reset.")
    else:
        admin = User(
            username=ADMIN_USERNAME,
            password=generate_password_hash(ADMIN_PASSWORD),
            is_admin=True
        )
        db.session.add(admin)
        try:
            db.session.commit()
            print(f"✅ Admin user created (username={ADMIN_USERNAME}, password={ADMIN_PASSWORD})")
        except IntegrityError:
            db.session.rollback()
            print("⚠️ Could not create admin due to a uniqueness constraint. Try a different username.")
