def get_auth(client):
    client.post("/auth/register", json={
        "email": "proj@muelaads.com", "password": "password123", "name": "P", "role": "admin"
    })
    token = client.post("/auth/login", json={"email": "proj@muelaads.com", "password": "password123"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def create_client(http_client, headers):
    return http_client.post("/clients", json={"name": "Test Client", "industry": "Tech"}, headers=headers).json()

def test_create_project(client):
    headers = get_auth(client)
    c = create_client(client, headers)
    r = client.post("/projects", json={
        "client_id": c["id"],
        "title": "January Social Media",
        "service_type": "social_media"
    }, headers=headers)
    assert r.status_code == 200
    assert r.json()["title"] == "January Social Media"
    assert r.json()["status"] == "pending"

def test_list_projects(client):
    headers = get_auth(client)
    c = create_client(client, headers)
    client.post("/projects", json={"client_id": c["id"], "title": "P1", "service_type": "ads"}, headers=headers)
    client.post("/projects", json={"client_id": c["id"], "title": "P2", "service_type": "seo"}, headers=headers)
    r = client.get("/projects", headers=headers)
    assert r.status_code == 200
    assert len(r.json()) == 2

def test_list_projects_by_client(client):
    headers = get_auth(client)
    c1 = create_client(client, headers)
    c2 = client.post("/clients", json={"name": "Other", "industry": "Retail"}, headers=headers).json()
    client.post("/projects", json={"client_id": c1["id"], "title": "C1 P", "service_type": "ads"}, headers=headers)
    client.post("/projects", json={"client_id": c2["id"], "title": "C2 P", "service_type": "seo"}, headers=headers)
    r = client.get(f"/projects?client_id={c1['id']}", headers=headers)
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["title"] == "C1 P"

def test_update_project_status(client):
    headers = get_auth(client)
    c = create_client(client, headers)
    p = client.post("/projects", json={"client_id": c["id"], "title": "P", "service_type": "ads"}, headers=headers).json()
    r = client.put(f"/projects/{p['id']}", json={"status": "in_progress"}, headers=headers)
    assert r.status_code == 200
    assert r.json()["status"] == "in_progress"

def test_get_project_not_found(client):
    headers = get_auth(client)
    r = client.get("/projects/99999", headers=headers)
    assert r.status_code == 404

def test_projects_require_auth(client):
    r = client.get("/projects")
    assert r.status_code in (401, 403)

def test_create_project_invalid_client(client):
    headers = get_auth(client)
    r = client.post("/projects", json={
        "client_id": 99999,
        "title": "Bad Project",
        "service_type": "social_media"
    }, headers=headers)
    assert r.status_code == 404
