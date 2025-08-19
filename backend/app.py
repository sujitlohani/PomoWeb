from datetime import datetime
import os
from flask_migrate import Migrate
from flask import Flask, render_template, request, redirect, url_for, jsonify
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
migrate = Migrate(app, db)
with app.app_context():
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
    is_admin = db.Column(db.Boolean, default=False)

    # Proper two-way relationship
    tasks = db.relationship("Task", back_populates="user", lazy=True)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    estimated = db.Column(db.Integer, default=1)          # estimated pomodoros
    completed = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    completed_at = db.Column(db.DateTime, nullable=True)
    # NEW: mark tasks created by an admin
    assigned_by_admin = db.Column(db.Boolean, default=False, nullable=False)

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

    tasks_list = (
        Task.query
        .filter_by(user_id=current_user.id)
        .order_by(Task.timestamp.desc())
        .all()
    )
    return render_template("tasks.html", tasks=tasks_list)

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

        # Redirect admins to /admin, others to /home
        if user.is_admin:
            return redirect(url_for("admin"))
        return redirect(url_for("home"))

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# ----- Admin -----
@app.route("/admin", methods=["GET", "POST"])
@login_required
def admin():
    if not current_user.is_admin:
        return redirect(url_for("home"))

    if request.method == "POST":
        user_id = request.form.get("user_id", type=int)
        description = (request.form.get("task_description") or "").strip()
        # estimated might not be present in the admin form; default to 1
        estimated = request.form.get("estimated", type=int) or 1

        if user_id and description:
            task = Task(
                description=description,
                estimated=estimated,
                user_id=user_id,
                assigned_by_admin=True  # flag for UI
            )
            db.session.add(task)
            db.session.commit()
        return redirect(url_for("admin"))

    users = User.query.order_by(User.username.asc()).all()
    tasks = Task.query.order_by(Task.timestamp.desc()).all()
    return render_template("admin.html", users=users, tasks=tasks)

@app.route("/report")
@login_required
def report():
    return render_template("report.html")

# ----- Task actions used from Home/Tasks -----
@app.route("/add_task", methods=["POST"])
@login_required
def add_task():
    """
    Endpoint used by the Home modal to add a task.
    Accepts JSON: 'description' and optional 'estimated'.
    """
    # Accept JSON safely; if you ever post form to this route, this won't crash.
    desc = ""
    est = 1
    if request.is_json:
        payload = request.get_json(silent=True) or {}
        desc = (payload.get("description") or "").strip()
        est = payload.get("estimated", 1)
        try:
            est = int(est)
        except (TypeError, ValueError):
            est = 1
    else:
        desc = (request.form.get("description") or "").strip()
        est = request.form.get("estimated", type=int) or 1

    if not desc:
        return jsonify({"error": "Task description is required"}), 400

    task = Task(description=desc, estimated=est, user_id=current_user.id)
    db.session.add(task)
    db.session.commit()

    return jsonify({
        "id": task.id,
        "description": task.description,
        "estimated": task.estimated,
        "completed": task.completed,
        "assigned_by_admin": task.assigned_by_admin
    })


@app.route("/toggle_task/<int:task_id>", methods=["POST"])
@login_required
def toggle_task(task_id: int):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403

    task.completed = not task.completed
    # If you added completed_at earlier:
    try:
        task.completed_at = datetime.utcnow() if task.completed else None
    except Exception:
        pass

    db.session.commit()

    # If it's AJAX, return JSON; otherwise, redirect (for /tasks page forms)
    is_ajax = request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest"
    if is_ajax:
        return jsonify({"success": True, "completed": task.completed, "id": task.id})
    return redirect(request.headers.get("Referer") or url_for("tasks"))


@app.route("/delete_task/<int:task_id>", methods=["POST"])
@login_required
def delete_task(task_id: int):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403

    db.session.delete(task)
    db.session.commit()

    is_ajax = request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest"
    if is_ajax:
        return jsonify({"success": True, "id": task_id})
    return redirect(request.headers.get("Referer") or url_for("tasks"))

# Optional user profile route if you still need it
@app.route("/user/<usr>")
@login_required
def user_profile(usr: str):
    # Typically you'd rely on current_user, but keeping this for compatibility.
    return render_template("user.html", name=usr)

# -----------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
