"""單元 5：Hook —— 回合結束（Stop）時，若 app/ 有變更但測試沒跑過，提醒補跑。

只做提醒（exit 0 並印訊息），示範 Stop 事件的用法；要強制可改成 exit 2。
"""
import subprocess
import sys

if hasattr(sys.stderr, "reconfigure"):  # Windows 主控台預設不是 UTF-8
    sys.stderr.reconfigure(encoding="utf-8")


def main() -> int:
    diff = subprocess.run(["git", "diff", "--name-only"], capture_output=True, text=True).stdout
    changed = [f for f in diff.splitlines() if f.startswith("app/")]
    if not changed:
        return 0
    cmd = [sys.executable, "-m", "pytest", "-q", "-x"]  # 用同一個 Python，跨平台
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        msg = "[hook] app/ 有變更但 pytest 未通過，請在交付前修正：\n"
        print(msg + r.stdout[-800:], file=sys.stderr)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
