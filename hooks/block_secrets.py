"""單元 5：Hook —— 擋住看起來像 API key / token 的內容。

掛在 UserPromptSubmit（使用者貼進來）與 PreToolUse: Bash（agent 要執行的指令）。
Codex 會把事件 JSON 從 stdin 餵進來；要「真的擋下」有兩種寫法：
  1. exit code 2，並把原因寫到 stderr
  2. 印出 JSON {"decision": "block", "reason": "..."}
這裡用第 1 種。
"""
import json
import re
import sys

if hasattr(sys.stderr, "reconfigure"):  # Windows 主控台預設不是 UTF-8
    sys.stderr.reconfigure(encoding="utf-8")

PATTERNS = [
    r"sk-[A-Za-z0-9]{20,}",            # OpenAI style key
    r"ghp_[A-Za-z0-9]{30,}",           # GitHub PAT
    r"AKIA[0-9A-Z]{16}",               # AWS access key
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
]

def main() -> int:
    try:
        event = json.load(sys.stdin)
    except Exception:
        return 0
    text = json.dumps(event, ensure_ascii=False)
    for pat in PATTERNS:
        if re.search(pat, text):
            msg = f"[hook] 偵測到疑似機密（{pat}），已擋下。請改用環境變數或 Secret。"
            print(msg, file=sys.stderr)
            return 2
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
