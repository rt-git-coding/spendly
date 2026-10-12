# Spec: Login and Logout

## Overview
Turn the static `/login` page into a working sign-in flow and replace the `/logout` stub. A visitor submits email and password; the server looks up the user, verifies the password against the stored werkzeug hash, stores the user id in the Flask session, and redirects to the landing page. Logout clears the session and redirects to the landing page. This is Step 3 of the Spendly roadmap: it builds on the accounts created in Step 2 and provides the session identity that every logged-in feature (profile, expenses) depends on. The navbar also becomes session-aware.

## Depends on
- Step 1 — Database setup (`users` table, `get_db()`)
- Step 2 — User registration (`create_user()`, `get_user_by_email()`, password hashing)

## Routes
- `GET /login` — render the sign-in form; if already logged in, redirect to `/` — public (already exists)
- `POST /login` — validate the form, verify credentials, set `session["user_id"]`, redirect to `/`; on failure re-render the form with an error — public
- `GET /logout` — clear the session and redirect to `/` — public (safe to call when not logged in); replaces the current stub

## Database changes
No database changes. The existing `users` table already has `email` (UNIQUE) and `password_hash`.

No new DB helpers are required: `get_user_by_email(email)` from Step 2 already returns the row including `password_hash`. If the navbar needs the user's name, add `get_user_by_id(user_id)` to `database/db.py` (parameterised query, returns `sqlite3.Row` or `None`).

## Templates
- **Create:** none
- **Modify:**
  - `templates/login.html` — replace the hardcoded `action="/login"` with `url_for('login')`; re-populate the email field after a failed submit (never the password); keep the existing `error` block
  - `templates/base.html` — navbar shows "Sign in" / "Get started" when logged out, and the user's name plus a "Sign out" link (`url_for('logout')`) when logged in

## Files to change
- `app.py` — set `app.secret_key` (read from env var `SPENDLY_SECRET_KEY`, with a clearly-labelled development fallback); allow `GET` and `POST` on `/login`; implement `/logout`; import `session`; add a context processor (or `before_request` loader) exposing the current user to templates
- `database/db.py` — add `get_user_by_id()` only if needed for the navbar
- `templates/login.html` — as above
- `templates/base.html` — as above

## Files to create
- `tests/test_login_logout.py` — pytest tests for the login and logout flow

## New dependencies
No new dependencies. Flask's built-in signed-cookie `session` is used.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only (`?` placeholders, never f-strings in SQL)
- Passwords verified with werkzeug (`check_password_hash`); never log or echo plaintext passwords
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- DB logic lives in `database/db.py` only; routes read the form, call helpers, render or redirect
- Use `url_for()` for every internal link and redirect
- Store only `user_id` in the session — not the name, email or hash
- Normalise the email (trim, lowercase) before lookup, matching registration
- Use one generic error message for both unknown email and wrong password ("Invalid email or password.") so account existence is not revealed
- Missing email or password re-renders `login.html` with an `error` and HTTP 400/401; do not return raw strings
- Do not hardcode a secret key that would ship to production silently: prefer the env var, and document the dev fallback in a comment
- Do not implement `/profile` or any other stub route; post-login redirect goes to `/` (landing) because `/profile` is still a stub until Step 4
- Keep port 5001; do not change `requirements.txt`

## Definition of done
- [ ] `GET /login` renders the form, and the form posts to `/login` via `url_for`
- [ ] Logging in as `demo@spendly.com` / `demo123` redirects (302) to `/` and sets a session cookie
- [ ] Email matching is case-insensitive and ignores surrounding whitespace (e.g. ` Demo@Spendly.com `)
- [ ] A wrong password shows "Invalid email or password." and sets no session
- [ ] An unknown email shows the same "Invalid email or password." message
- [ ] An empty email or password shows an error and sets no session
- [ ] After a failed submit, the email is kept in the form and the password field is empty
- [ ] A user registered via `/register` can immediately log in with the same credentials
- [ ] Visiting `/login` while logged in redirects to `/`
- [ ] When logged in, the navbar shows the user's name and a "Sign out" link; when logged out it shows "Sign in" and "Get started"
- [ ] `GET /logout` clears the session, redirects (302) to `/`, and the navbar returns to the logged-out state
- [ ] `GET /logout` while logged out does not error
- [ ] The session cookie contains no password or hash, and `app.secret_key` is not empty
- [ ] `/profile` and the other stub routes are unchanged
- [ ] `pytest` passes, including the new `tests/test_login_logout.py` and the existing registration tests
- [ ] No hardcoded URLs or hex colours were added, and no new packages were installed
