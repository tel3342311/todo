---
name: release
description: 要為 todo-api 發布新版本時使用：改版號、更新 k8s image tag、產生 CHANGELOG、開 release PR。修 bug 或加功能時不要用。
---

# 發布 SOP（單元 6：Skill 是工序，AGENTS.md 是規矩）

使用方式：`$release 0.2.0`

## 步驟
1. 確認工作區乾淨：`git status` 沒有未提交變更；目前在 `main` 且已 `git pull`。
2. 讀 `app/main.py` 的 `APP_VERSION` 預設值與 `k8s/deployment.yaml` 的 image tag，確認兩者一致（舊版號）。
3. 建分支 `release/<新版號>`。
4. 更新三處版號：
   - `app/main.py` 的 `APP_VERSION` 預設值
   - `k8s/deployment.yaml` 的 `image:` tag 與 `APP_VERSION` env
   - `README.md` 若有版本標示
5. 用 `git log <舊 tag>..HEAD --oneline` 整理 `CHANGELOG.md`，分「新增／修正／變更」三段，每條一行。
6. 執行 `ruff check .` 與 `pytest -q`，都要過。
7. commit 訊息 `chore(release): v<新版號>`；`git push -u origin release/<新版號>`（會觸發 Rules 的 prompt，等人確認）。
8. `gh pr create --title "Release v<新版號>" --body-file CHANGELOG 摘要`（同樣會被 prompt）。

## 不要做的事
- 不要自己 merge、不要打 git tag——tag 由 CI 在 PR merge 後建立。
- 不要碰 `.github/`、`.codex/`、`argocd/`。
- 不要直接 `kubectl`；部署由 Argo CD 依 Git 同步（單元 7）。

## 交付
回報：新版號、變更的檔案清單、CHANGELOG 摘要、PR 連結。
