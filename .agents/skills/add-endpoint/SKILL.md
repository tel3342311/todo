---
name: add-endpoint
description: 在 todo-api 新增或修改一個 FastAPI 端點時使用。包含 schema、實作、測試、文件四步驟與驗收標準。純粹修 bug、重構、或改部署設定時不要用這個 skill。
---

# 新增端點 SOP

這是 todo-api 專案「新增一個 API 端點」的固定工序。AGENTS.md 是規矩，這份是步驟。
使用方式：在 Codex 輸入 `$add-endpoint 新增 GET /todos/search?q=關鍵字`。

## 步驟

1. **先讀再寫**：讀 `app/main.py` 看既有端點的寫法（依賴注入 `get_db`、`_get_or_404`、response_model），新端點要長得一樣。
2. **Schema**：若需要新的請求或回應結構，加在 `app/models.py` 的 Pydantic 區段，欄位要有型別與 `Field` 限制。
3. **實作**：加在 `app/main.py`，放在相關端點旁邊；一行 docstring；錯誤一律用 `HTTPException`，不要回傳裸 dict 當錯誤。
4. **測試**：在 `tests/test_todos.py` 用既有的 `client` fixture，至少寫：
   - 一個正常路徑
   - 一個邊界（空結果、不存在的 id、非法參數 → 422）
5. **文件**：若 `docs/API.md` 存在，補上端點說明與 curl 範例；不存在則略過。
6. **驗證**：執行 `ruff check .` 與 `pytest -q`，兩者都要過。

## 交付格式

完成後回報：
- 新增/修改了哪些檔案
- 測試數量從幾個變成幾個
- `pytest -q` 的最後一行輸出

## 不要做的事

- 不要動 `k8s/`、`.github/`、`.codex/`、`Dockerfile`
- 不要新增第三方套件
- 不要「順手」修 `GET /stats` 的已知 bug 或重構 `legacy_report.py`（那是課堂練習）
