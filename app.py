import os
import sqlite3

from flask import Flask, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

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
_LOGIN_ERROR = "Incorrect email or password."

# Checked in place of a real hash when no user matches, so that a failed login
# costs the same amount of work whether or not the email exists. Without it,
# unknown-email responses return measurably faster than wrong-password ones,
# which lets an attacker enumerate registered accounts.
_DUMMY_PASSWORD_HASH = generate_password_hash("spendly-timing-equalizer")


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


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if session.get("user_id"):
            return redirect(url_for("profile"))
        return render_template("login.html")

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    user = get_user_by_email(email)

    # Always verify a hash, even when no user matched, to keep the response
    # time the same for unknown emails and wrong passwords.
    stored_hash = user["password_hash"] if user is not None else _DUMMY_PASSWORD_HASH
    password_ok = check_password_hash(stored_hash, password)

    if user is None or not password_ok:
        return render_template("login.html", error=_LOGIN_ERROR, email=email)

    # Drop any pre-existing session before authenticating, so a planted
    # session cookie cannot survive the login.
    session.clear()
    session["user_id"] = user["id"]
    return redirect(url_for("profile"))


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("landing"))


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

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
