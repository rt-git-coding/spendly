import pytest

from database import db

DEMO = {"email": "demo@spendly.com", "password": "demo123"}
INVALID_MSG = b"Invalid email or password."


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    db.init_db()
    db.seed_db()
    import app as app_module

    app_module.app.config["TESTING"] = True
    return app_module.app.test_client()


def login(client, **overrides):
    return client.post("/login", data={**DEMO, **overrides})


def session_user_id(client):
    with client.session_transaction() as sess:
        return sess.get("user_id")


def test_get_login_renders_form(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert b'action="/login"' in response.data
    assert b"Sign out" not in response.data
    assert b"Sign in" in response.data


def test_demo_login_sets_session_and_redirects(client):
    response = login(client)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")
    demo = db.get_user_by_email(DEMO["email"])
    assert session_user_id(client) == demo["id"]


def test_email_is_trimmed_and_case_insensitive(client):
    response = login(client, email=" Demo@Spendly.com ")
    assert response.status_code == 302
    assert session_user_id(client) is not None


@pytest.mark.parametrize(
    "overrides",
    [{"password": "wrong-password"}, {"email": "nobody@example.com"}],
)
def test_bad_credentials_show_same_error(client, overrides):
    response = login(client, **overrides)
    assert response.status_code == 401
    assert INVALID_MSG in response.data
    assert session_user_id(client) is None


@pytest.mark.parametrize(
    "overrides",
    [{"email": ""}, {"password": ""}, {"email": "", "password": ""}],
)
def test_missing_fields_show_error(client, overrides):
    response = login(client, **overrides)
    assert response.status_code == 400
    assert b"auth-error" in response.data
    assert session_user_id(client) is None


def test_failed_login_keeps_email_not_password(client):
    response = login(client, password="wrong-password")
    assert b'value="demo@spendly.com"' in response.data
    assert b"wrong-password" not in response.data


def test_sql_injection_email_is_rejected(client):
    response = login(client, email="' OR 1=1 --")
    assert response.status_code == 401
    assert session_user_id(client) is None


def test_registered_user_can_log_in(client):
    creds = {"name": "Alice", "email": "alice@example.com", "password": "password123"}
    client.post("/register", data=creds)
    response = login(client, email=creds["email"], password=creds["password"])
    assert response.status_code == 302
    assert session_user_id(client) is not None


def test_login_page_redirects_when_logged_in(client):
    login(client)
    response = client.get("/login")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")


def test_stale_session_is_treated_as_logged_out(client):
    with client.session_transaction() as sess:
        sess["user_id"] = 99999
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Sign in" in response.data
    assert b"Sign out" not in response.data


def test_navbar_when_logged_in(client):
    login(client)
    response = client.get("/")
    assert b"Demo User" in response.data
    assert b'href="/logout"' in response.data
    assert b"Get started" not in response.data


def test_logout_clears_session(client):
    login(client)
    response = client.get("/logout")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")
    assert session_user_id(client) is None
    assert b"Sign out" not in client.get("/").data


def test_logout_when_logged_out_does_not_error(client):
    response = client.get("/logout")
    assert response.status_code == 302


def test_session_holds_only_user_id(client):
    login(client)
    with client.session_transaction() as sess:
        assert set(sess.keys()) == {"user_id"}


def test_secret_key_is_set(client):
    import app as app_module

    assert app_module.app.secret_key


def test_stub_routes_unchanged(client):
    assert b"coming in Step 4" in client.get("/profile").data
    assert b"coming in Step 7" in client.get("/expenses/add").data
