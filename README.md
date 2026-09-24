# todo-api — Codex × Harness 實戰課程專案

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
