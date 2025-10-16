from datetime import datetime
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
import os
from flask_migrate import Migrate
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user, login_required,
    logout_user, current_user
)
from sqlalchemy import func
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from dotenv import load_dotenv
load_dotenv()



# App & Config
app = Flask(
    __name__,
    template_folder="../frontend/templates",
    static_folder="../frontend/static"
)
mail = Mail(app)



app.config.update(
    MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.gmail.com"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
    MAIL_USE_TLS=True,
    MAIL_USE_SSL=False,
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_DEFAULT_SENDER=os.getenv("MAIL_FROM", os.getenv("MAIL_USERNAME")),
)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "your_super_secret_key")

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL",
    "sqlite:///users.db" 
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)
with app.app_context():
    print("👉 Using DB at:", os.path.abspath(db.engine.url.database or ":memory:"))

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)




# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=True)
    password = db.Column(db.String(150), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    tasks = db.relationship("Task", back_populates="user", lazy=True)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    estimated = db.Column(db.Integer, default=1)          
    completed = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    completed_at = db.Column(db.DateTime, nullable=True)
    assigned_by_admin = db.Column(db.Boolean, default=False, nullable=False)

    user = db.relationship("User", back_populates="tasks")

with app.app_context():
    db.create_all()



def get_serializer():
    return URLSafeTimedSerializer(app.config["SECRET_KEY"])

@login_manager.user_loader
def load_user(user_id: str):
    return User.query.get(int(user_id))




# Routes
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
        username = (request.form.get("username") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = (request.form.get("password") or "").strip()

        if not username or not email or not password:
            return render_template("register.html", error="All fields are required")

        if User.query.filter_by(username=username).first():
            return render_template("register.html", error="Username already exists")
        if User.query.filter(func.lower(User.email) == email).first():
            return render_template("register.html", error="Email already in use")

        user = User(username=username, email=email, password=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("login"))
    return render_template("register.html")



@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        identifier = (request.form.get("identifier") or "").strip()
        password = (request.form.get("password") or "").strip()

        user = User.query.filter_by(username=identifier).first()
        if not user and hasattr(User, "email"):
            user = User.query.filter(db.func.lower(User.email) == identifier.lower()).first()

        if not user or not check_password_hash(user.password, password):
            return render_template("login.html", error="Invalid credentials")

        login_user(user)
        return redirect(url_for("admin" if user.is_admin else "home"))

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
        estimated = request.form.get("estimated", type=int) or 1

        if user_id and description:
            task = Task(
                description=description,
                estimated=estimated,
                user_id=user_id,
                assigned_by_admin=True
            )
            db.session.add(task)
            db.session.commit()
        return redirect(url_for("admin"))

    users = User.query.order_by(User.username.asc()).all()
    tasks = Task.query.order_by(Task.timestamp.desc()).all()

    tasks_by_user = {}
    for u in users:
        user_tasks = []
        for t in u.tasks: 
            user_tasks.append({
                "id": t.id,
                "description": t.description,
                "completed": bool(t.completed),
                "timestamp": t.timestamp.strftime('%Y-%m-%d %H:%M') if t.timestamp else None
            })
        tasks_by_user[u.id] = user_tasks

    return render_template(
        "admin.html",
        users=users,
        tasks=tasks,
        tasks_by_user=tasks_by_user
    )


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
    try:
        task.completed_at = datetime.utcnow() if task.completed else None
    except Exception:
        pass

    db.session.commit()
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



@app.route("/user/<usr>")
@login_required
def user_profile(usr: str):
    return render_template("user.html", name=usr)



@app.route("/forgot", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        identifier = (request.form.get("identifier") or "").strip()

        user = User.query.filter_by(username=identifier).first()
        if not user:
            user = User.query.filter(func.lower(User.email) == identifier.lower()).first()

        if user and user.email:
            s = get_serializer()
            token = s.dumps({"uid": user.id, "email": user.email})
            reset_link = url_for("reset_password", token=token, _external=True)

            msg = Message(
                subject="Reset your Pomoweb password",
                recipients=[user.email],  
                body=f"Click to reset your password: {reset_link}",
                html=f"<p>Click to reset your password: <a href='{reset_link}'>Reset password</a></p>",
            )
            mail.send(msg)

        return render_template("forgot_sent.html")

    return render_template("forgot.html")



@app.route("/reset/<token>", methods=["GET", "POST"])
def reset_password(token):
    s = get_serializer()
    try:
        data = s.loads(token, max_age=3600)  
    except SignatureExpired:
        return render_template("reset.html", expired=True)
    except BadSignature:
        return render_template("reset.html", invalid=True)

    user = User.query.get_or_404(data.get("uid"))

    if request.method == "POST":
        new_password = (request.form.get("password") or "").strip()
        confirm = (request.form.get("confirm") or "").strip()
        if not new_password or len(new_password) < 6:
            return render_template("reset.html", token=token, error="Password must be at least 6 characters.")
        if new_password != confirm:
            return render_template("reset.html", token=token, error="Passwords do not match.")

        user.password = generate_password_hash(new_password)
        db.session.commit()
        return redirect(url_for("login"))

    return render_template("reset.html", token=token)








# -----------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
