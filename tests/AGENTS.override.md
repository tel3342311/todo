# tests/ 專屬規則（AGENTS.override.md 階層示範）

> 這個檔案示範官方 AGENTS.md 的階層：Codex 在 `tests/` 底下工作時，
> 會把根目錄的 AGENTS.md 和這份**串接**起來，這份排在後面，所以**優先**。
> 課堂驗證：`cd tests && codex --ask-for-approval never "Summarize the current instructions."`
> 應該會看到下面的規則出現在總結裡。

- 測試一律用 `tests/conftest.py` 的 `client` fixture，不要自己建 `TestClient`。
- 一個測試函式只驗證一件事；函式名用 `test_<端點>_<情境>`，例如 `test_patch_todo_not_found`。
- 不要用 `time.sleep` 或真實網路。
- 覆寫根目錄規則 1：在這個目錄下改完測試只需跑 `pytest -q tests/`，不必跑 `ruff`（示範「內層覆寫外層」）。
