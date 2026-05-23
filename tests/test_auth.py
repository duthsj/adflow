def test_register_user(client):
    response = client.post("/auth/register", json={
        "email": "test@muelaads.com",
        "password": "password123",
        "name": "Test User",
        "role": "editor"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["email"] == "test@muelaads.com"
    assert "access_token" in data

def test_login_success(client):
    client.post("/auth/register", json={
        "email": "login@muelaads.com",
        "password": "password123",
        "name": "Login User",
        "role": "editor"
    })
    response = client.post("/auth/login", json={
        "email": "login@muelaads.com",
        "password": "password123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_wrong_password(client):
    client.post("/auth/register", json={
        "email": "wrong@muelaads.com",
        "password": "correct123",
        "name": "Wrong User",
        "role": "editor"
    })
    response = client.post("/auth/login", json={
        "email": "wrong@muelaads.com",
        "password": "incorrect123"
    })
    assert response.status_code == 401

def test_get_me(client):
    r = client.post("/auth/register", json={
        "email": "me@muelaads.com",
        "password": "password123",
        "name": "Me User",
        "role": "admin"
    })
    token = r.json()["access_token"]
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "me@muelaads.com"

def test_me_no_token(client):
    r = client.get("/auth/me")
    assert r.status_code == 401
