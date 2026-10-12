import os
import sqlite3

from flask import Flask, redirect, render_template, request, session, url_for

from database.db import (
    create_user,
    get_db,
    get_user_by_email,
    get_user_by_id,
    init_db,
    seed_db,
    verify_user,
)

app = Flask(__name__)
# The fallback key is for local development only; set SPENDLY_SECRET_KEY in production.
app.secret_key = os.environ.get("SPENDLY_SECRET_KEY", "dev-only-insecure-key-change-me")

with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

def _current_user():
    user_id = session.get("user_id")
    if user_id is None:
        return None
    return get_user_by_id(user_id)


@app.context_processor
def inject_current_user():
    return {"current_user": _current_user()}


@app.route("/")
def landing():
    return render_template("landing.html")


def _register_error(message, name, email):
    return render_template("register.html", error=message, name=name, email=email), 400


def _is_valid_email(email):
    local, sep, domain = email.partition("@")
    has_space = any(char.isspace() for char in email)
    return bool(sep and local and domain and "@" not in domain and not has_space)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    if not name:
        return _register_error("Name is required.", name, email)
    if not email:
        return _register_error("Email is required.", name, email)
    if not _is_valid_email(email):
        return _register_error("Enter a valid email address.", name, email)
    if len(password) < 8:
        return _register_error("Password must be at least 8 characters.", name, email)
    if get_user_by_email(email):
        return _register_error("An account with that email already exists.", name, email)

    try:
        create_user(name, email, password)
    except sqlite3.IntegrityError:
        return _register_error("An account with that email already exists.", name, email)
    return redirect(url_for("login"))


def _login_error(message, email, status):
    return render_template("login.html", error=message, email=email), status


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if _current_user():
            return redirect(url_for("landing"))
        return render_template("login.html")

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    if not email or not password:
        return _login_error("Email and password are required.", email, 400)

    user = verify_user(email, password)
    if user is None:
        return _login_error("Invalid email or password.", email, 401)

    session.clear()
    session["user_id"] = user["id"]
    return redirect(url_for("landing"))


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


@app.route("/profile")
def profile():
    return "Profile page — coming in Step 4"


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
