"""單元 8：用 Codex SDK 自建一個 Worker Agent —— CI Autofix。

流程：
  1. 跑 pytest，失敗就把輸出交給 Codex
  2. Codex 在 workspace-write sandbox 內修正，並自己重跑測試
  3. 把修改開成分支與 PR（人審核仍在；agent 不直接 push main）

用法：
  pip install openai-codex
  python agents/ci_autofix.py            # 本機試跑
  python agents/ci_autofix.py --dry-run  # 只看 Codex 的診斷，不改檔

依官方 SDK 文件：Codex() → thread_start(model, sandbox) → thread.run(prompt) → result.final_response
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time

if hasattr(sys.stdout, "reconfigure"):  # Windows 主控台預設不是 UTF-8
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from openai_codex import Codex, Sandbox

PROMPT = """
① 目前 `pytest -q` 失敗，輸出如下：
```
{output}
```
② 專案規範見 AGENTS.md；測試在 tests/，程式在 app/。
③ 不要修改 tests/ 底下的斷言來「讓測試過」；不要動 k8s/、.codex/、.github/。
④ 修正後重新執行 `pytest -q`，全部通過才算完成。最後用三行以內說明你改了什麼、為什麼。
"""


def run_tests() -> tuple[int, str]:
    proc = subprocess.run([sys.executable, "-m", "pytest", "-q"], capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="只診斷，不修改檔案")
    ap.add_argument("--model", default=None, help="覆寫模型；預設用 config.toml")
    args = ap.parse_args()

    code, output = run_tests()
    if code == 0:
        print("測試已通過，不需要 autofix。")
        return 0

    sandbox = Sandbox.read_only if args.dry_run else Sandbox.workspace_write
    prompt = PROMPT.format(output=output[-4000:])
    if args.dry_run:
        prompt += "\n（乾跑模式：只診斷根因與修法，不要修改任何檔案。）"

    with Codex() as codex:
        kwargs = {"sandbox": sandbox}
        if args.model:
            kwargs["model"] = args.model
        thread = codex.thread_start(**kwargs)
        result = thread.run(prompt)

    print("===== Codex 回報 =====")
    print(result.final_response)

    if args.dry_run:
        return 0

    code, _ = run_tests()
    if code != 0:
        print("Codex 修正後測試仍失敗，交回人工處理。", file=sys.stderr)
        return 1

    # 開分支 + PR（需要 gh CLI 已登入）；失敗只警告，不中斷
    branch = f"codex/autofix-{time.strftime('%Y%m%d-%H%M%S')}"  # 每次新分支，不需要 --force
    cmds = [
        ["git", "checkout", "-B", branch],
        ["git", "add", "-A"],
        ["git", "commit", "-m", "fix: codex autofix for failing tests"],
        ["git", "push", "-u", "origin", branch],
        ["gh", "pr", "create", "--fill", "--title", "Codex autofix: failing tests",
         "--body", result.final_response],
    ]
    for c in cmds:
        r = subprocess.run(c, capture_output=True, text=True)
        if r.returncode != 0:
            print(f"警告：{' '.join(c)} 失敗：{r.stderr.strip()}", file=sys.stderr)
            break
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
