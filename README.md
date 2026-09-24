# todo-api — Codex × Harness 實戰課程專案 20260924

一個刻意做小的 FastAPI 待辦清單 API，用來走完整條路：
**Codex 寫程式 → Git → GitHub Actions CI/CD → Argo CD GitOps → 自建 Worker Agent。**

## 快速開始
```bash
# macOS / Linux / WSL2
python3 -m venv .venv && source .venv/bin/activate
# Windows PowerShell（原生）
python -m venv .venv ; .venv\Scripts\Activate.ps1

pip install -r requirements-dev.txt
python run.py test   # = make test
python run.py dev    # = make dev；開 http://localhost:8000（前端頁）或 /docs（Swagger）
```
`run.py` 是 Makefile 的跨平台版（Windows 沒有 make）；`python run.py help` 列出全部指令。

## 推送後自動部署到 Docker Desktop

將 `.github/workflows/deploy-docker-desktop.yml` 合併到 `main`，並在 Docker Desktop 的電腦上註冊
帶有 `todo-docker-desktop` label 的 Windows self-hosted runner。之後每次 **push 到 `main`** 都會先執行測試，
再自動建置並部署容器至 **http://localhost:8080**。只有本機 commit、尚未 push 時不會觸發 GitHub Actions。

Docker Desktop 須使用 **Linux containers** 模式，電腦與 runner 必須保持上線。
SQLite 透過 `todo-desktop-data` volume 保留；容器資料與本機開發用的 `todo.db` 分開。
設定步驟、手動部署及故障排除見 [Docker Desktop 部署指南](docs/DOCKER_DESKTOP.md)。

## 待辦應用程式

開啟 http://localhost:8000 使用單人待辦清單，支援桌面與手機版面：

- 新增、編輯標題、勾選完成／恢復未完成，以及確認後刪除。
- 新增或編輯時可設定目標完成日期；留空可不設定或清除，日期會顯示於待辦項目。
- 全部／未完成／已完成篩選、標題搜尋，以及新增時間／標題排序。
- 顯示全部待辦的數量與完成比例；搜尋及篩選不影響總進度。
- 儲存失敗會保留輸入並顯示錯誤；按「重新整理」取得伺服器最新資料。
- 標題去除頭尾空白後須為 1–200 字，不接受只有空白的標題。

資料預設存於工作目錄的 `todo.db`，重新啟動後仍保留；可用 `DATABASE_URL` 指定位置。
這是單人應用，沒有帳號或登入隔離。前端使用原生 HTML、CSS、JavaScript，不需要前端建置工具。
啟動時會自動為既有 SQLite 的 `todos` 表新增可為空的 `finish_date DATE` 欄位；
原有 ID、標題、完成狀態與建立時間不變，既有待辦的日期為 `null`，可重複啟動而不重設日期。
升級前建議備份 `todo.db`。其他資料庫的既有表須先由管理者新增相同的 nullable DATE 欄位。

### API 與測試

`GET /todos` 列出所有待辦（ID 升冪）；`GET /todos?done=true` 或 `?done=false` 依完成狀態篩選，
非法狀態值回傳 `422`。新增使用 `POST /todos`，單筆讀取、修改、刪除使用
`GET`、`PATCH`、`DELETE /todos/{todo_id}`。完整 schema 與互動操作位於 `/docs`。
`finish_date` 是使用者選擇的目標日期（`YYYY-MM-DD`），不是實際完成時間；勾選完成不會改變它。
新增時可省略或傳 `null`；修改時省略表示保留，傳 `null` 表示清除。過去日期也允許使用。
請求範例與回應格式見 [API 說明](docs/API.md)。

```bash
python run.py test                    # pytest API、驗證及靜態資源測試
python run.py lint                    # ruff 程式碼檢查
node --test tests/frontend.test.mjs   # Node.js 20+；搜尋、排序、統計與錯誤處理
```

前端資源由 `/static/` 提供。介面的進度直接由完整待辦列表計算，不呼叫 `/stats`；
`/stats` 空資料時的已知錯誤與 `legacy_report.py` 仍保留作為課堂練習。

## Windows 學員請先看
- **建議用 WSL2**（Ubuntu）＋ Docker Desktop 的 WSL integration：Codex 官方支援 WSL2，且本專案的 `Makefile`、`scripts/*.sh`、Rules 範例（`rm -rf`）都是 Linux 指令，在 WSL2 裡跟 macOS 完全一致。
- 若堅持 Windows 原生：
  - 用 `python run.py …` 取代 `make …`；`.venv\Scripts\Activate.ps1` 被擋時先 `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`。
  - PowerShell 的 `curl` 其實是 `Invoke-WebRequest`，請打 **`curl.exe`**（例：`curl.exe -i localhost:8000/stats`）。
  - `.codex/hooks.json` 用 `python3` 啟動 hook；原生 Windows 通常只有 `python`，請把兩處 `python3` 改成 `python`。
  - `scripts/codex_gate.sh` 只在 CI（ubuntu）跑，本機不需要。

## 課堂路線圖
| 單元 | 你會對這個 repo 做的事 |
|---|---|
| 1 | `git init`、推到 GitHub；開 http://localhost:8000 看前端頁 |
| 2 | `codex` 讀懂專案、`/init` 產生 AGENTS.md |
| 3 | 用 Codex 修 `/stats` 的 bug、補測試、重構 `legacy_report.py` |
| 4 | 用 Codex Cloud 丟任務 → 產 PR → 你審核 |
| 5 | 把 Codex 接進 CI：`codex-review.yml`（PR 留言）、`codex-gate.yml`（JSON gate）；護欄 `.codex/rules/`、`.codex/hooks.json` |
| 6 | CD 與 Pipeline as Code：`build-and-release.yml` 建 image → GHCR → `codex exec` 開 manifest PR；`$release` Skill；三個審查 subagent |
| 7 | GitOps：`argocd/application.yaml` 讓 Argo CD 依 Git 同步 kind；agent 設定也全在 Git |
| 8 | 自建 Worker Agent：`agents/ci_autofix.py`（SDK）、`agents/app_server_demo.py`（app-server）；Auto-review；`plugins/` |

## GitOps（kind + Argo CD，單元 7）
```bash
python run.py set-owner <你的 GitHub 帳號>   # 把 k8s/ 與 argocd/ 的 CHANGE_ME 換掉（會轉小寫），然後 commit + push
python run.py kind-up                        # 建 kind 叢集（localhost:30080）
python run.py argocd-install                 # 裝 Argo CD 並等它就緒
kubectl apply -f argocd/application.yaml
kubectl get applications -n argocd -w        # OutOfSync → Synced
python run.py argocd-password                # 要看 Argo CD UI 時
```
image 從 GHCR 拉：第一次 CI 推送後，到 GitHub Packages 把 `todo-api` 改成 **Public**，kind 才拉得到。

## 課後清理
```bash
python run.py kind-down
```
