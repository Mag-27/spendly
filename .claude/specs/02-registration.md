# Spec: Registration

## Overview

This step wires up the `POST` handler for `/register` so new users can create an account.

The registration template (`templates/register.html`) and its form already exist and POST to `/register` with `name`, `email`, and `password` fields. The template has an `{% if error %}` block ready to render validation/registration errors.

Only the backend registration logic is required unless the existing template does **not** support repopulating `name` and `email` after validation failure.

This step builds directly on the database layer from Step 1 and is a prerequisite for Step 3 (logout) and Step 4 (profile), since both require an authenticated session.

---

## Depends on

**Step 1 — Database setup**

* `database/db.py` is already implemented.
* The `users` table already exists with:

```text
id
name
email
password_hash
created_at
```

* The `email` column has a `UNIQUE` constraint.
* No database schema changes are required.

---

# Routes

### `GET /register`

* Public route.
* Render the existing `templates/register.html`.
* The form should initially be empty.
* No session is required.

### `POST /register`

* Public route.
* Read `name`, `email`, and `password` from `request.form`.
* Validate all fields server-side.
* Normalize `name` and `email`.
* Check whether the email is already registered.
* Hash the password using Werkzeug.
* Create the user through `database/db.py`.
* Store the new user's ID in the Flask session.
* Redirect to `/profile` after successful registration.

---

# Database Changes

No database schema changes are required.

The existing `users` table supports this feature:

```text
users
├── id
├── name
├── email
├── password_hash
└── created_at
```

Add the following two database helpers to `database/db.py` alongside the existing `get_db()`, `init_db()`, and `seed_db()` functions.

---

## `get_user_by_email(email)`

Purpose:

* Look up a user by email.
* Used for the registration uniqueness check.

Requirements:

* Use a parameterized SQL query.
* Never interpolate the email directly into SQL.
* Return the matching user/row if found.
* Return `None` if no user exists.
* The email passed to this function should already be normalized by the application layer.

Example behavior:

```text
get_user_by_email("user@example.com")
        ↓
existing user → return user
        ↓
no user → return None
```

---

## `create_user(name, email, password_hash)`

Purpose:

* Insert a new user into the `users` table.
* Return the newly created user's database ID.

Requirements:

* Use a parameterized `INSERT`.
* Never store the plaintext password.
* Only `password_hash` may be written to the password column.
* Commit the transaction successfully before returning.
* Return the new user's integer ID, preferably using SQLite's `lastrowid`.
* Properly handle/propagate database errors.
* Do not silently suppress unexpected database errors.

The function should conceptually perform:

```text
INSERT user
      ↓
commit transaction
      ↓
return new user ID
```

---

# Input Normalization and Validation

All validation must happen on the server.

Do **not** rely on:

* HTML `required`
* HTML `type="email"`
* HTML `minlength`
* Any other client-side validation

The server must assume that submitted form data can be completely invalid.

---

## Name

Read:

```python
name = request.form.get("name", "")
```

Then:

* Strip leading/trailing whitespace.
* Reject an empty name.
* Preserve internal whitespace.
* Do not impose restrictive character rules that would reject legitimate names containing spaces, hyphens, apostrophes, etc.
* Enforce a reasonable maximum length of **100 characters**.

Example:

```text
"  John Doe  " → "John Doe"
```

If the name is missing or empty after trimming:

```text
Name is required.
```

---

## Email

Read:

```python
email = request.form.get("email", "")
```

Normalize it before validation/database operations:

1. Strip leading/trailing whitespace.
2. Convert to lowercase.

Example:

```text
"  User@Example.COM  "
        ↓
"user@example.com"
```

The normalized email must be used for:

* Validation
* Duplicate lookup
* Database insertion

The application should therefore treat:

```text
user@example.com
User@example.com
USER@EXAMPLE.COM
```

as the same email address.

Perform server-side email format validation.

Do not attempt to implement full RFC-compliant email parsing. A reasonable/conservative validation mechanism is sufficient.

Possible errors:

```text
Email is required.
```

or:

```text
Please enter a valid email address.
```

---

# Password

Read the password exactly as submitted:

```python
password = request.form.get("password", "")
```

### Important

**Do not strip or normalize the password.**

Do not:

* `.strip()`
* `.lower()`
* Change whitespace
* Change capitalization
* Modify Unicode characters
* Log it
* Store it directly

The password must be passed to `generate_password_hash()` exactly as submitted.

---

## Minimum password length

The password must contain at least **8 characters**.

Use the actual submitted password when checking length.

For example:

```text
len(password) < 8
```

If invalid:

```text
Password must be at least 8 characters.
```

No password should be inserted if this validation fails.

---

# Password Hashing

Use Werkzeug's:

```python
from werkzeug.security import generate_password_hash
```

Hash the password before inserting it into the database:

```text
plaintext password
       ↓
generate_password_hash()
       ↓
password_hash
       ↓
database
```

The plaintext password must **never** be:

* Stored in the database
* Logged
* Printed
* Passed into the template
* Stored in the session
* Included in an error message

The database must contain only the generated password hash.

Do not implement a custom password hashing algorithm.

Do not use:

* MD5
* SHA-1
* SHA-256 directly
* Plaintext passwords
* Custom encryption

---

# Email Uniqueness

The registration flow must perform an application-level lookup using:

```text
get_user_by_email(email)
```

If a user already exists, do not create another account.

Display an appropriate error such as:

```text
An account with that email is already registered.
```

However, the lookup is **not** considered the final authority.

The database's `UNIQUE` constraint remains the final protection against duplicate emails.

This is important because two requests could theoretically perform:

```text
Request A → email does not exist
Request B → email does not exist
Request A → INSERT
Request B → INSERT
```

Therefore, the INSERT must still correctly handle a uniqueness violation.

---

# IntegrityError / Race Condition Handling

If the database raises an SQLite integrity error because the email uniqueness constraint was violated during insertion:

* Catch the expected `sqlite3.IntegrityError`.
* Do not return HTTP 500.
* Do not create a session.
* Re-render `register.html`.
* Display the same duplicate-email error used by the normal uniqueness check.

Example:

```text
An account with that email is already registered.
```

Do not blindly convert unrelated database integrity errors into a duplicate-email error if the database contains other constraints that could produce an `IntegrityError`.

Unexpected database failures should continue to the application's normal error handling/logging mechanism rather than being silently hidden.

---

# Registration Flow

The `/register` POST handler should follow this sequence:

```text
POST /register
      │
      ▼
Read name/email/password
      │
      ▼
Normalize name and email
      │
      ▼
Validate name
      │
      ├── invalid → render register.html with error
      │
      ▼
Validate email
      │
      ├── invalid → render register.html with error
      │
      ▼
Validate password
      │
      ├── invalid → render register.html with error
      │
      ▼
get_user_by_email(email)
      │
      ├── exists → render register.html with error
      │
      ▼
generate_password_hash(password)
      │
      ▼
create_user(name, email, password_hash)
      │
      ├── IntegrityError → render register.html with duplicate error
      │
      ▼
new_user_id
      │
      ▼
session["user_id"] = new_user_id
      │
      ▼
redirect("/profile")
```

---

# Session

Flask's built-in session must be used.

After successful registration:

```python
session["user_id"] = new_user_id
```

The session must contain the newly created user's database ID.

### Important

The session must only be created/modified **after** the database insertion succeeds.

Do not set:

```python
session["user_id"]
```

before the user has actually been inserted successfully.

If registration fails because of:

* Missing name
* Invalid email
* Short password
* Existing email
* Database insertion failure

then no new authenticated registration session should be created.

---

# Secret Key

Flask sessions require `app.secret_key`.

If the application does not already configure one, configure it before handling requests.

Use the environment variable:

```text
SECRET_KEY
```

with a development-only fallback.

Conceptually:

```text
SECRET_KEY environment variable
          ↓
     app.secret_key
```

The fallback is only for local development/testing and must not be treated as a production secret.

Do not hardcode a real production secret into the source code.

The secret key configuration must happen during application initialization, before session handling.

---

# Session Security

Preserve any existing session security configuration.

If appropriate for the existing application/environment:

```text
SESSION_COOKIE_HTTPONLY = True
```

For HTTPS production deployments:

```text
SESSION_COOKIE_SECURE = True
```

Do not break or disable existing session security settings.

No additional session-management dependency is required.

---

# Form Behavior

The existing `templates/register.html` should continue to be used.

The form already contains:

```text
name
email
password
```

and posts to:

```text
/register
```

---

## Validation Failure

When registration fails, render:

```text
templates/register.html
```

with:

```text
error
name
email
```

The previously submitted `name` and normalized `email` should be available to the template so they can be repopulated.

The password must **never** be repopulated.

For example, the resulting behavior should be:

```text
Name:     John Doe
Email:    john@example.com
Password: [empty]
Error:    Password must be at least 8 characters.
```

---

## Existing Template Requirement

The specification currently assumes that `register.html` supports:

```html
value="{{ name or '' }}"
```

and:

```html
value="{{ email or '' }}"
```

or an equivalent mechanism.

**Verify this before implementation.**

If the current template already supports repopulating these values:

* No template modification is necessary.

If it does not:

* Make the minimal required modification to `templates/register.html`.
* Do not redesign the page.
* Do not modify the styling unnecessarily.
* Do not add password repopulation.

Therefore, the "Files to change" list below allows a template change **only if technically necessary for the required repopulation behavior**.

---

# Error Messages

Use clear user-facing validation messages.

Recommended messages:

```text
Name is required.
Email is required.
Please enter a valid email address.
Password must be at least 8 characters.
An account with that email is already registered.
```

The exact wording may be adjusted to match the existing application's style, but duplicate-email errors should be consistent between:

* The initial `get_user_by_email()` check
* A database uniqueness race/`IntegrityError`

Do not expose raw SQL or database exception messages to the user.

---

# CSRF

If the existing application already has CSRF protection:

* Do not disable it.
* Do not bypass it for `/register`.
* Preserve the existing CSRF mechanism.

No new CSRF dependency is required for this step.

If the application currently has no CSRF system, do not introduce a new dependency solely for this registration step unless required by the project's existing architecture.

---

# Database Access Rules

All SQLite access related to users must remain inside:

```text
database/db.py
```

`app.py` must **not** directly execute SQL queries.

Correct:

```text
app.py
   │
   ├── get_user_by_email()
   │
   └── create_user()
          │
          ▼
    database/db.py
          │
          ▼
       SQLite
```

Incorrect:

```text
app.py
   │
   └── sqlite3.execute(...)
```

Do not introduce:

* SQLAlchemy
* ORM models
* Additional database abstraction layers

---

# SQL Requirements

All SQL queries must use parameterized values.

Correct:

```python
db.execute(
    "SELECT ... WHERE email = ?",
    (email,)
)
```

Incorrect:

```python
db.execute(
    f"SELECT ... WHERE email = '{email}'"
)
```

Never concatenate user input into SQL statements.

---

# Files to Change

## `database/db.py`

Add:

```text
get_user_by_email(email)
create_user(name, email, password_hash)
```

Keep all SQLite access in this module.

No schema changes.

---

## `app.py`

Modify:

```text
/register
```

from GET-only behavior to:

```text
GET + POST
```

Conceptually:

```python
@app.route("/register", methods=["GET", "POST"])
```

On `GET`:

* Render the existing registration form.

On `POST`:

* Read form values.
* Normalize inputs.
* Validate inputs.
* Check email uniqueness.
* Hash password.
* Create user.
* Create session.
* Redirect to `/profile`.

---

## `templates/register.html`

No changes are required **if** it already supports repopulating `name` and `email`.

If it does not, make only the minimal change necessary to support:

* `name` repopulation
* `email` repopulation
* Empty password after failed submission

Do not redesign the template.

---

# Files to Create

None.

---

# New Dependencies

None.

Use the existing dependencies:

```python
Flask
Werkzeug
sqlite3
```

Specifically:

```python
from werkzeug.security import generate_password_hash
```

No SQLAlchemy or ORM.

No new password hashing package.

No new database package.

---

# Security Requirements

The implementation must satisfy all of the following:

* Never store plaintext passwords.
* Never log plaintext passwords.
* Never return plaintext passwords to the template.
* Never put passwords into the Flask session.
* Never interpolate user input into SQL.
* Use parameterized SQL queries.
* Validate all inputs server-side.
* Normalize email consistently.
* Preserve the database `UNIQUE` constraint as the final duplicate-email protection.
* Handle duplicate-email `IntegrityError` without a 500.
* Do not expose raw database errors to users.
* Do not disable existing CSRF protection.
* Configure Flask's secret key before using sessions.

---

# CSS / Template Rules

No new styling is required for this step.

If any template modification becomes necessary:

* All templates must continue to extend `base.html`.
* Use the existing CSS architecture.
* Use CSS variables.
* Never introduce hardcoded hex colors.
* Do not redesign the registration page.

---

# Definition of Done

## Successful registration

* [ ] `GET /register` still renders the registration form.
* [ ] `POST /register` accepts `name`, `email`, and `password`.
* [ ] A valid new registration creates exactly one row in `users`.
* [ ] The stored password is a Werkzeug password hash, not plaintext.
* [ ] The normalized email is stored.
* [ ] `create_user()` commits the insertion successfully.
* [ ] `create_user()` returns the new user's ID.
* [ ] `session["user_id"]` contains the newly created user's ID.
* [ ] The successful request redirects to `/profile`.
* [ ] The browser receives the Flask session cookie.

## Name validation

* [ ] Missing name is rejected.
* [ ] Whitespace-only name is rejected.
* [ ] Leading/trailing whitespace is removed.
* [ ] Names up to the configured maximum length are accepted.
* [ ] Legitimate names containing spaces, hyphens, and apostrophes are not unnecessarily rejected.

## Email validation

* [ ] Missing email is rejected.
* [ ] Leading/trailing email whitespace is removed.
* [ ] Email is normalized to lowercase.
* [ ] Invalid email formats are rejected server-side.
* [ ] Email uniqueness is checked before insertion.
* [ ] Email uniqueness is effectively case-insensitive.
* [ ] Duplicate email registration does not create a second row.
* [ ] Duplicate-email database race conditions are handled without a 500.

## Password validation

* [ ] Missing password is rejected.
* [ ] Passwords shorter than 8 characters are rejected.
* [ ] Passwords of exactly 8 characters are accepted.
* [ ] Password is not stripped before validation/hashing.
* [ ] Password is not lowercased or otherwise normalized.
* [ ] Password is never logged.
* [ ] Password is never stored in plaintext.
* [ ] Password is never repopulated into the form after an error.

## Validation failures

* [ ] Validation failures re-render `register.html`.
* [ ] Validation failures do not create a database row.
* [ ] Validation failures do not create an authenticated registration session.
* [ ] `name` is repopulated after validation failure.
* [ ] `email` is repopulated after validation failure.
* [ ] `password` remains empty after validation failure.
* [ ] The `error` variable is passed to the template.

## Database behavior

* [ ] All SQL remains inside `database/db.py`.
* [ ] All queries use parameterized SQL.
* [ ] No SQLAlchemy or ORM is introduced.
* [ ] Successful inserts are committed.
* [ ] Expected duplicate-email `IntegrityError` is handled gracefully.
* [ ] Unexpected database errors are not silently swallowed.
* [ ] Raw database exceptions are not displayed to users.

## Session behavior

* [ ] `app.secret_key` is configured.
* [ ] `SECRET_KEY` environment variable is supported.
* [ ] A development fallback exists if the project requires one.
* [ ] The session is only created after successful database insertion.
* [ ] Failed registration does not authenticate the user.
* [ ] The newly created user's ID is stored in `session["user_id"]`.

## Application behavior

* [ ] `python app.py` starts without errors.
* [ ] `GET /register` works.
* [ ] `POST /register` works.
* [ ] Successful registration redirects to `/profile`.
* [ ] Existing Step 1 database functionality continues to work.
* [ ] Existing template inheritance from `base.html` remains intact.
* [ ] Existing CSS behavior is not unnecessarily changed.
* [ ] Existing CSRF protection, if present, remains enabled.

---

# Expected End-to-End Behavior

### Valid registration

```text
User submits:
    Name: John Doe
    Email: JOHN@Example.com
    Password: mypassword123

             ↓

Normalize:
    Name: John Doe
    Email: john@example.com
    Password: unchanged

             ↓

Validate
             ↓
Check email uniqueness
             ↓
Generate password hash
             ↓
INSERT into users
             ↓
COMMIT
             ↓
Get new user ID
             ↓
session["user_id"] = new_user_id
             ↓
302 Redirect → /profile
```

### Duplicate email

```text
POST /register
       ↓
Normalize email
       ↓
get_user_by_email()
       ↓
User exists
       ↓
Render register.html
       ↓
Show duplicate-email error
       ↓
No INSERT
       ↓
No new session
```

### Short password

```text
POST /register
       ↓
Password length < 8
       ↓
Render register.html
       ↓
Show password error
       ↓
Preserve name/email
       ↓
Password remains empty
       ↓
No database insert
       ↓
No new session
```

### Database race condition

```text
Request A ──────┐
                ├── Both see email as available
Request B ──────┘
                ↓
             INSERT
                ↓
One succeeds
                ↓
Other receives UNIQUE constraint IntegrityError
                ↓
Render duplicate-email error
                ↓
No 500
                ↓
No invalid session
```

---

# Scope Restrictions

This step is **only** for registration.

Do not implement unrelated features such as:

* Logout
* Profile editing
* Login
* Password reset
* Email verification
* OAuth
* User deletion
* Admin functionality
* New database tables
* SQLAlchemy migration
* UI redesign

Those belong to later steps unless already required by the existing application.

The final implementation should remain minimal and follow the existing project architecture.
