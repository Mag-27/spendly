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
# Profile page sample data                                            #
# ------------------------------------------------------------------ #

# Step 4 builds the profile UI against fixed sample data so the layout can be
# reviewed on its own. Step 5 replaces every one of these constants with real
# queries against the expenses table — nothing here touches the database.

_PROFILE_USER = {
    "initials": "DU",
    "name": "Demo User",
    "email": "demo@spendly.com",
    "member_since": "January 2026",
}

_PROFILE_STATS = [
    {"icon": "\u20b9", "label": "Total spent", "value": "\u20b912,450", "note": "This month"},
    {"icon": "\u25ce", "label": "Transactions", "value": "28", "note": "This month"},
    {"icon": "\u25f7", "label": "Top category", "value": "Bills", "note": "\u20b94,500 spent"},
]

_PROFILE_TRANSACTIONS = [
    {"date": "24 Aug", "description": "Electricity bill", "category": "Bills", "amount": "\u20b92,400"},
    {"date": "22 Aug", "description": "Groceries run", "category": "Food", "amount": "\u20b91,180"},
    {"date": "19 Aug", "description": "Metro card top-up", "category": "Transport", "amount": "\u20b9600"},
    {"date": "17 Aug", "description": "Pharmacy", "category": "Health", "amount": "\u20b9480"},
    {"date": "14 Aug", "description": "Movie night", "category": "Entertainment", "amount": "\u20b9750"},
    {"date": "11 Aug", "description": "New running shoes", "category": "Shopping", "amount": "\u20b93,200"},
]

# ``bar`` names a fixed-width utility class rather than an inline style, so the
# template stays free of style attributes.
_PROFILE_CATEGORIES = [
    {"name": "Bills", "amount": "\u20b94,500", "share": "36%", "bar": "cat-bar--w72"},
    {"name": "Shopping", "amount": "\u20b93,200", "share": "26%", "bar": "cat-bar--w52"},
    {"name": "Food", "amount": "\u20b92,050", "share": "16%", "bar": "cat-bar--w33"},
    {"name": "Transport", "amount": "\u20b91,750", "share": "14%", "bar": "cat-bar--w28"},
    {"name": "Health", "amount": "\u20b9950", "share": "8%", "bar": "cat-bar--w15"},
]


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


@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    return render_template(
        "profile.html",
        user=_PROFILE_USER,
        stats=_PROFILE_STATS,
        transactions=_PROFILE_TRANSACTIONS,
        categories=_PROFILE_CATEGORIES,
        current_user_name=_PROFILE_USER["name"],
    )


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

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
