# PomoWebHere’s a **simple, copy-paste-ready README.md** focused only on **pulling the repo and running it locally**. It assumes no prior setup and keeps the steps minimal and exact.

---

# PomoWeb

A minimal Pomodoro + Tasks web app built with **Flask**, **Flask-Login**, and **SQLAlchemy**.
Users can register/login and manage personal tasks. The timer runs in the browser; tasks are saved per user in a local SQLite database.

---

## Clone the repo

```bash
git clone https://github.com/sujitlohani/PomoWeb.git
cd PomoWeb
```

---

## Create and activate a virtual environment

```bash
# Create venv
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

If you see `(venv)` at the start of your terminal prompt, the environment is active.

---

## Install dependencies

```bash
pip install -r requirements.txt
```

---


Open the app at:
**[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## Use the app

1. **Register** a new account
2. **Login**
3. Go to **Home** (timer), **Tasks** (add tasks), **Reports** (placeholder), **Logout** when done.

Tasks are saved per logged-in user in `users.db`.

---

That’s it. If you need a Docker setup or deployment guide later, we can add it.
