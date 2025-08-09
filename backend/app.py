from datetime import datetime
import os

from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user, login_required,
    logout_user, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash

# -----------------------------------------------------------------------------
# App & Config
# -----------------------------------------------------------------------------
app = Flask(
    __name__,
    template_folder="../frontend/templates",
    static_folder="../frontend/static"  
)


app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "your_super_secret_key")

# You can point this to Postgres/MySQL later by setting DATABASE_URL env var.
# Example Postgres: postgresql+psycopg2://user:pass@localhost:5432/pomoweb
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL",
    "sqlite:///users.db"  # SQLAlchemy ORM with SQLite file by default
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
with app.app_context():
    import os
    print("👉 Using DB at:", os.path.abspath(db.engine.url.database or ":memory:"))


login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

# -----------------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

    # Proper two-way relationship
    tasks = db.relationship("Task", back_populates="user", lazy=True)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    estimated = db.Column(db.Integer, default=1)          # estimated pomodoros
    completed = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="tasks")


with app.app_context():
    db.create_all()

# -----------------------------------------------------------------------------
# Login manager
# -----------------------------------------------------------------------------
@login_manager.user_loader
def load_user(user_id: str):
    return User.query.get(int(user_id))

# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("base.html", landing_page=True)

@app.route("/home")
@login_required
def home():
    tasks = (
        Task.query
        .filter_by(user_id=current_user.id)
        .order_by(Task.timestamp.desc())
        .all()
    )
    return render_template("home.html", tasks=tasks)

@app.route("/tasks", methods=["GET", "POST"])
@login_required
def tasks():
    """
    Separate Tasks page (optional) that can also create a task.
    """
    if request.method == "POST":
        desc = request.form.get("description", "").strip()
        est = request.form.get("estimated", type=int) or 1
        if desc:
            db.session.add(Task(description=desc, estimated=est, user_id=current_user.id))
            db.session.commit()
        return redirect(url_for("tasks"))

    tasks = (
        Task.query
        .filter_by(user_id=current_user.id)
        .order_by(Task.timestamp.desc())
        .all()
    )
    return render_template("tasks.html", tasks=tasks)

# ----- Auth -----
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            return render_template("register.html", error="Username and password are required")

        existing = User.query.filter_by(username=username).first()
        if existing:
            return render_template("register.html", error="Username already exists")

        user = User(username=username, password=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        user = User.query.filter_by(username=username).first()
        if not user or not check_password_hash(user.password, password):
            return render_template("login.html", error="Invalid username or password")

        login_user(user)
        return redirect(url_for("home"))

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# ----- Admin/Report placeholders -----
@app.route("/admin")
@login_required
def admin():
    return render_template("admin.html", users=[])

@app.route("/report")
@login_required
def report():
    return render_template("report.html")

# ----- Task actions used from Home/Tasks -----
@app.route("/add_task", methods=["POST"])
@login_required
def add_task():
    """
    Minimal endpoint used by the Home modal to add a task.
    Accepts 'description' and optional 'estimated'.
    """
    desc = request.form.get("description", "").strip()
    est = request.form.get("estimated", type=int) or 1
    if desc:
        db.session.add(Task(description=desc, estimated=est, user_id=current_user.id))
        db.session.commit()
    return redirect(url_for("home"))

@app.route("/toggle_task/<int:task_id>", methods=["POST"])
@login_required
def toggle_task(task_id: int):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        return "Unauthorized", 403
    task.completed = not task.completed
    db.session.commit()
    return redirect(url_for("home"))

@app.route("/delete_task/<int:task_id>", methods=["POST"])
@login_required
def delete_task(task_id: int):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        return "Unauthorized", 403
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for("home"))


# Optional user profile route if you still need it
@app.route("/user/<usr>")
@login_required
def user_profile(usr: str):
    # Typically you'd rely on current_user, but keeping this for compatibility.
    return render_template("user.html", name=usr)

# -----------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
