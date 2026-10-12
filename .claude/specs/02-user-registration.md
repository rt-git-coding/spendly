# Spec: User Registration

## Overview
Turn the static `/register` page into a working sign-up flow. A visitor submits name, email and password; the server validates the input, hashes the password with werkzeug, stores a new row in `users`, and redirects to the login page. This is Step 2 of the Spendly roadmap: it builds on the Step 1 data layer and produces the accounts that login (Step 3) and every later feature depend on. It does not log the user in; sessions arrive in Step 3.

## Depends on
- Step 1 — Database setup (`users` table, `get_db()`, `init_db()`)

## Routes
- `GET /register` — render the registration form — public (already exists)
- `POST /register` — validate the form, create the user, redirect to `/login` on success, or re-render the form with an error — public

## Database changes
No database changes. The existing `users` table already has `name`, `email` (UNIQUE), `password_hash` and `created_at`.

New helpers in `database/db.py` (no inline SQL in routes):
- `get_user_by_email(email)` — returns a `sqlite3.Row` or `None`
- `create_user(name, email, password)` — hashes the password with `generate_password_hash`, inserts the row with a parameterised query, returns the new user id. Raises `sqlite3.IntegrityError` on a duplicate email, which the route catches.

## Templates
- **Create:** none
- **Modify:**
  - `templates/register.html` — replace the hardcoded `action="/register"` with `url_for('register')`; re-populate the name and email fields after a failed submit (never the password); keep the existing `error` block

## Files to change
- `app.py` — allow `GET` and `POST` on `/register`; add the POST handler; import `request`, `redirect`, `url_for`
- `database/db.py` — add `get_user_by_email()` and `create_user()`
- `templates/register.html` — as above

## Files to create
- `tests/test_registration.py` — pytest tests for the registration flow

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only (`?` placeholders, never f-strings in SQL)
- Passwords hashed with werkzeug (`generate_password_hash`); never store or log plaintext
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- DB logic lives in `database/db.py` only; the route just reads the form, calls helpers, renders or redirects
- Use `url_for()` for every internal link and redirect
- Server-side validation (the HTML `required` attribute is not enough):
  - name: required, trimmed, non-empty
  - email: required, trimmed, lowercased, must contain `@` with text on both sides
  - password: required, at least 8 characters
  - email must not already be registered
- Validation failures re-render `register.html` with an `error` message and HTTP 200 (or 400); do not return raw strings
- Do not implement login, sessions or logout (Step 3); leave the other stub routes untouched
- Keep port 5001; do not change `requirements.txt`

## Definition of done
- [ ] `GET /register` renders the form, and the form posts to `/register` via `url_for`
- [ ] Submitting valid name, email and an 8+ character password creates a row in `users` and redirects (302) to `/login`
- [ ] The stored `password_hash` is a werkzeug hash and not the plaintext password
- [ ] Registering the same email again (including different letter case) shows an error and creates no second row
- [ ] A password shorter than 8 characters shows an error and creates no row
- [ ] Empty name or empty email, or an email without a valid `@` shape, shows an error and creates no row
- [ ] After a failed submit, name and email are kept in the form and the password field is empty
- [ ] The seeded `demo@spendly.com` account is unaffected
- [ ] `pytest` passes, including the new `tests/test_registration.py`
- [ ] No hardcoded URLs or hex colours were added, and no new packages were installed
