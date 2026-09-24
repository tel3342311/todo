"""起始測試：只涵蓋 health 與新增/列出。
單元 3 練習：請用 Codex 補齊 PATCH / DELETE / 404 / /stats 的測試。
"""


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_create_and_list(client):
    r = client.post("/todos", json={"title": "買牛奶"})
    assert r.status_code == 201
    body = r.json()
    assert body["title"] == "買牛奶"
    assert body["done"] is False

    r = client.get("/todos")
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_create_rejects_empty_title(client):
    r = client.post("/todos", json={"title": ""})
    assert r.status_code == 422


def test_index_page(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "待辦清單" in r.text
