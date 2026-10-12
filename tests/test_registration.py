import pytest
from werkzeug.security import check_password_hash

from database import db

VALID = {"name": "Alice", "email": "alice@example.com", "password": "password123"}


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    db.init_db()
    db.seed_db()
    import app as app_module

    app_module.app.config["TESTING"] = True
    return app_module.app.test_client()


def register(client, **overrides):
    return client.post("/register", data={**VALID, **overrides})


def user_count():
    conn = db.get_db()
    try:
        return conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    finally:
        conn.close()


def test_get_register_renders_form(client):
    response = client.get("/register")
    assert response.status_code == 200
    assert b'action="/register"' in response.data
    assert b'name="email"' in response.data


def test_register_success_redirects_to_login(client):
    before = user_count()
    response = register(client)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")
    assert user_count() == before + 1


def test_password_is_hashed(client):
    register(client)
    user = db.get_user_by_email("alice@example.com")
    assert user["password_hash"] != VALID["password"]
    assert check_password_hash(user["password_hash"], VALID["password"])


def test_email_normalised_and_name_trimmed(client):
    register(client, name="  Alice  ", email="  Alice@Example.COM ")
    user = db.get_user_by_email("alice@example.com")
    assert user is not None
    assert user["name"] == "Alice"


@pytest.mark.parametrize("email", ["alice@example.com", "ALICE@EXAMPLE.COM"])
def test_duplicate_email_rejected(client, email):
    register(client)
    before = user_count()
    response = register(client, email=email)
    assert response.status_code == 400
    assert b"already exists" in response.data
    assert user_count() == before


def test_duplicate_race_returns_400(client, monkeypatch):
    import app as app_module

    register(client)
    before = user_count()
    monkeypatch.setattr(app_module, "get_user_by_email", lambda email: None)
    response = register(client)
    assert response.status_code == 400
    assert b"already exists" in response.data
    assert user_count() == before


def test_demo_user_unaffected(client):
    demo_hash = db.get_user_by_email("demo@spendly.com")["password_hash"]
    register(client)
    assert db.get_user_by_email("demo@spendly.com")["password_hash"] == demo_hash
    before = user_count()
    response = register(client, email="demo@spendly.com")
    assert response.status_code == 400
    assert user_count() == before


def test_password_length_boundary(client):
    before = user_count()
    response = register(client, password="1234567")
    assert response.status_code == 400
    assert b"at least 8" in response.data
    assert user_count() == before
    assert register(client, password="12345678").status_code == 302


@pytest.mark.parametrize(
    "overrides",
    [
        {"name": ""},
        {"name": "   "},
        {"email": ""},
        {"email": "   "},
        {"email": "plain"},
        {"email": "@x.com"},
        {"email": "a@"},
        {"email": "@"},
        {"email": "a@@b.com"},
        {"email": "a b@x.com"},
    ],
)
def test_invalid_input_rejected(client, overrides):
    before = user_count()
    response = register(client, **overrides)
    assert response.status_code == 400
    assert user_count() == before


def test_missing_field_returns_400(client):
    response = client.post("/register", data={"name": "Alice", "email": "a@x.com"})
    assert response.status_code == 400


def test_failed_submit_keeps_name_and_email_not_password(client):
    response = register(client, password="Zq9!uni")
    body = response.data.decode()
    assert 'value="Alice"' in body
    assert 'value="alice@example.com"' in body
    assert "Zq9!uni" not in body


def test_name_is_html_escaped(client):
    response = register(client, name="<script>x</script>", password="short")
    assert b"<script>x</script>" not in response.data
    assert b"&lt;script&gt;" in response.data
