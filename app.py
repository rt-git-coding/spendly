import sqlite3

from flask import Flask, redirect, render_template, request, url_for

from database.db import create_user, get_db, get_user_by_email, init_db, seed_db

app = Flask(__name__)

with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

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


@app.route("/login")
def login():
    return render_template("login.html")


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
    return "Logout — coming in Step 3"


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
