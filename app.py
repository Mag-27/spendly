import os
import sqlite3

from flask import Flask, redirect, render_template, request, session, url_for
from werkzeug.security import generate_password_hash

from database.db import create_user, get_db, get_user_by_email, init_db, seed_db

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-not-for-production")
app.config["SESSION_COOKIE_HTTPONLY"] = True

with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Validation                                                          #
# ------------------------------------------------------------------ #

_MAX_NAME_LENGTH = 100
_MIN_PASSWORD_LENGTH = 8
_DUPLICATE_EMAIL_ERROR = "An account with that email is already registered."


def _validate_registration(name, email, password):
    """Return the first validation error, or None if all fields are valid."""
    if not name:
        return "Name is required."
    if len(name) > _MAX_NAME_LENGTH:
        return f"Name must be {_MAX_NAME_LENGTH} characters or fewer."

    if not email:
        return "Email is required."
    local, _, domain = email.partition("@")
    if email.count("@") != 1 or not local or not domain or any(c.isspace() for c in email):
        return "Please enter a valid email address."

    if not password:
        return "Password is required."
    if len(password) < _MIN_PASSWORD_LENGTH:
        return f"Password must be at least {_MIN_PASSWORD_LENGTH} characters."

    return None


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    error = _validate_registration(name, email, password)
    if error:
        return render_template("register.html", error=error, name=name, email=email)

    if get_user_by_email(email) is not None:
        return render_template(
            "register.html", error=_DUPLICATE_EMAIL_ERROR, name=name, email=email
        )

    try:
        user_id = create_user(name, email, generate_password_hash(password))
    except sqlite3.IntegrityError as exc:
        if "users.email" not in str(exc):
            raise
        return render_template(
            "register.html", error=_DUPLICATE_EMAIL_ERROR, name=name, email=email
        )

    session["user_id"] = user_id
    return redirect(url_for("profile"))


@app.route("/login")
def login():
    return render_template("login.html")


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
