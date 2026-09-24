# AGENTS.md — 給 Codex 的專案說明書

> 這個檔案是 Codex（以及 Cursor、Copilot 等）進入專案時會先讀的「新人手冊」。
> 課程單元 2 會示範用 `/init` 產生初稿，再由學員手動補強成這個版本。

## 專案是什麼
FastAPI + SQLAlchemy + SQLite 的待辦清單 REST API。目的是作為 CI/CD 教學專案，**保持小而完整**。

## 目錄
- `app/main.py` — 所有 API 端點
- `app/models.py` — ORM 模型與 Pydantic schema
- `app/db.py` — 資料庫連線（`DATABASE_URL` 環境變數）
- `app/legacy_report.py` — 刻意寫壞的舊程式，重構練習用
- `tests/` — pytest；`conftest.py` 提供記憶體 SQLite 的 `client` fixture
- `k8s/` — Kustomize manifests（Deployment / Service / Namespace）
- `.github/` — Codex PR review workflow、review prompt、output schema
- `scripts/codex_gate.sh` — codex exec 當 quality gate（任何 CI 可用）
- `agents/` — 用 Codex SDK / app-server 自建 worker agent 的範例
- `argocd/` — Argo CD Application（GitOps，單元 7）
- `.codex/rules/`、`.codex/hooks.json`、`hooks/` — 執行政策與 hooks（護欄，單元 5）
- `.codex/agents/` — PR 審查用的三個 subagent（單元 6）
- `.codex/config.toml.example` — Auto-review 與 subagent 上限範例（單元 8）
- `plugins/todo-api-toolkit/` — 把 Skills 打包成 Plugin 的範例（單元 8）
- `.agents/skills/` — Codex Skills；新增端點用 `$add-endpoint`，發布用 `$release`
- `tests/AGENTS.override.md` — tests/ 目錄專屬規則（示範階層覆寫）

## 開發指令
```bash
pip install -r requirements-dev.txt
python run.py dev    # 本機啟動 http://localhost:8000（macOS/Linux 也可用 make dev）
python run.py test   # pytest
python run.py lint   # ruff
python run.py build  # docker build
```

## 規範（Codex 修改程式時必須遵守）
1. **先跑測試再交付**：任何程式修改後都要執行 `pytest -q`，全綠才算完成。
2. **新增端點必須同時新增測試**，放在 `tests/test_todos.py`，使用既有的 `client` fixture。
3. 型別註記完整；公開函式要有一行 docstring（繁體中文或英文皆可）。
4. 不要引入新的第三方套件，除非明確被要求；若要加，同步更新 `requirements*.txt`。
5. 不要修改 `k8s/`、`argocd/`、`.github/`、`.codex/` 底下的檔案，除非任務明確與部署、CI 或 agent 設定有關。
6. 資料庫 schema 變更要說明對既有資料的影響。
7. Commit 訊息用 Conventional Commits（`feat:`、`fix:`、`test:`、`refactor:`、`docs:`）。

## Code Review Rules
（`/review` 會讀這一段。官方建議把 review 規則放在最近的 AGENTS.md。）
- 任何新增或修改的端點若沒有對應測試，標為 **blocking**。
- 直接用字串拼接組 SQL，標為 **blocking**，建議改用 SQLAlchemy 查詢。
- 捕捉 `Exception` 後靜默吞掉，標為 **warning**，建議至少記錄 log。
- 回傳的 JSON 欄位名稱變更，標為 **warning**，提醒要同步更新 `docs/API.md`。
- 修改 `k8s/`、`argocd/`、`.github/` 或 `.codex/` 時，提醒此變更會影響部署或 agent 行為，需要 DevOps 審核。

## 已知問題（練習用，不要「順手」修掉）
- `GET /stats` 在沒有任何 todo 時會炸（ZeroDivisionError）。
- `app/legacy_report.py` 需要重構。
