"""Todo API 的 CRUD、篩選及輸入驗證測試。"""

import pytest
from fastapi.testclient import TestClient


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


@pytest.mark.parametrize("done, expected", [("true", ["完成"]), ("false", ["待辦"])])
def test_list_todos_filters_completion(client: TestClient, done: str, expected: list[str]) -> None:
    """完成狀態篩選只回傳符合條件的待辦。"""
    client.post("/todos", json={"title": "待辦"})
    completed = client.post("/todos", json={"title": "完成"}).json()
    client.patch(f"/todos/{completed['id']}", json={"done": True})
    response = client.get("/todos", params={"done": done})
    assert response.status_code == 200
    assert [todo["title"] for todo in response.json()] == expected


def test_list_todos_invalid_filter(client: TestClient) -> None:
    """非法完成狀態不可被靜默忽略。"""
    assert client.get("/todos?done=invalid").status_code == 422


def test_list_todos_empty_filter_result(client: TestClient) -> None:
    """沒有符合狀態的待辦時回傳空列表。"""
    client.post("/todos", json={"title": "待辦"})
    assert client.get("/todos?done=true").json() == []


@pytest.mark.parametrize("title", [" ", "\t\n", "x" * 201])
def test_create_todo_invalid_title(client: TestClient, title: str) -> None:
    """空白及過長標題不可儲存。"""
    assert client.post("/todos", json={"title": title}).status_code == 422
    assert client.get("/todos").json() == []


def test_create_todo_trims_title(client: TestClient) -> None:
    """新增標題會去除頭尾空白並保留內容。"""
    response = client.post("/todos", json={"title": "  買牛奶  "})
    assert response.status_code == 201
    assert client.get(f"/todos/{response.json()['id']}").json()["title"] == "買牛奶"


def test_patch_todo_persists_title_and_completion(client: TestClient) -> None:
    """修改後重新讀取仍保留新標題及狀態。"""
    todo = client.post("/todos", json={"title": "原始"}).json()
    response = client.patch(f"/todos/{todo['id']}", json={"title": " 新標題 ", "done": True})
    assert response.status_code == 200
    stored = client.get(f"/todos/{todo['id']}").json()
    assert stored["title"] == "新標題"
    assert stored["done"] is True
    assert stored["created_at"] == todo["created_at"]


def test_patch_todo_reopens_without_changing_title(client: TestClient) -> None:
    """可將已完成的待辦恢復為未完成。"""
    todo = client.post("/todos", json={"title": "保留標題"}).json()
    client.patch(f"/todos/{todo['id']}", json={"done": True})
    response = client.patch(f"/todos/{todo['id']}", json={"done": False})
    assert response.json()["done"] is False
    assert response.json()["title"] == "保留標題"


@pytest.mark.parametrize("title", ["", "  ", "x" * 201])
def test_patch_todo_rejects_invalid_title(client: TestClient, title: str) -> None:
    """驗證失敗時原始待辦保持不變。"""
    todo = client.post("/todos", json={"title": "原始"}).json()
    response = client.patch(f"/todos/{todo['id']}", json={"title": title, "done": True})
    assert response.status_code == 422
    assert client.get(f"/todos/{todo['id']}").json() == todo


def test_delete_todo_persists_removal(client: TestClient) -> None:
    """刪除後無法讀取，列表也不再包含該待辦。"""
    todo = client.post("/todos", json={"title": "刪除我"}).json()
    response = client.delete(f"/todos/{todo['id']}")
    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"/todos/{todo['id']}").status_code == 404
    assert client.get("/todos").json() == []


@pytest.mark.parametrize("method", ["get", "patch", "delete"])
def test_todo_missing_id(client: TestClient, method: str) -> None:
    """不存在的待辦回傳一致的 404。"""
    kwargs = {"json": {"done": True}} if method == "patch" else {}
    response = client.request(method, "/todos/99999", **kwargs)
    assert response.status_code == 404
    assert response.json() == {"detail": "todo not found"}


@pytest.mark.parametrize(
    "asset, content_type", [("app.js", "javascript"), ("styles.css", "text/css")]
)
def test_static_assets_available(client: TestClient, asset: str, content_type: str) -> None:
    """前端資源可由應用程式直接提供。"""
    response = client.get(f"/static/{asset}")
    assert response.status_code == 200
    assert content_type in response.headers["content-type"]


def test_static_unknown_asset(client: TestClient) -> None:
    """不存在的靜態資源回傳 404。"""
    assert client.get("/static/missing.js").status_code == 404
