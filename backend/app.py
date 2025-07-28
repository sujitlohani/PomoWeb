from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__, template_folder="../frontend/templates")

@app.route('/')
def index():
    return render_template("base.html", landing_page=True)

@app.route('/home')
def home():
    return render_template("home.html")

@app.route('/tasks', methods=['GET', 'POST'])
def tasks():
    if request.method == 'POST':
        task_name = request.form.get("task")
        # We'll add DB logic later
        return redirect(url_for('tasks'))
    return render_template("tasks.html", tasks=["Placeholder Task 1", "Task 2"])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Placeholder logic, DB will be added next step
        user = request.form.get("username")
        return redirect(url_for("user", usr=user))
    return render_template("login.html")

@app.route('/admin')
def admin():
    # Admin dashboard will be added later
    return render_template("admin.html", users=[])

@app.route('/user/<usr>')
def user(usr):
    # Placeholder user profile
    return render_template("user.html", name=usr)



if __name__ == "__main__":  # Corrected: use __name__ == "__main__"
    app.run(debug=True)
