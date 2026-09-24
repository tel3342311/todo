"""單元 8（示範）：直接對 Codex app-server 講 JSON-RPC。

這是「最深的整合層」：你的產品自己開一個 codex app-server 子行程，
用 stdio 傳 JSONL，收事件串流，並在 Codex 要執行指令時由你決定 accept / decline。

用法：python agents/app_server_demo.py "列出這個專案所有 API 端點"
依官方 app-server 文件：initialize → initialized → thread/start → turn/start，
伺服器會送 item/* 事件；需要核准時送 item/commandExecution/requestApproval，
客戶端回 {"id": <同一個 id>, "result": "accept" | "decline"}。
方法名與欄位以你安裝的 Codex 版本文件為準（learn.chatgpt.com/docs/app-server）。
"""
from __future__ import annotations

import json
import queue
import shutil
import subprocess
import sys
import threading
from itertools import count

if hasattr(sys.stdout, "reconfigure"):  # Windows 主控台預設編碼不是 UTF-8
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

_id = count(1)


def main() -> None:
    prompt = sys.argv[1] if len(sys.argv) > 1 else "用三句話說明這個專案在做什麼。"
    codex = shutil.which("codex")  # Windows 上是 codex.cmd，用 which 找才不會 FileNotFoundError
    if not codex:
        sys.exit("找不到 codex 指令，請先 npm install -g @openai/codex")
    proc = subprocess.Popen(
        [codex, "app-server"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, encoding="utf-8", bufsize=1,
    )
    responses: queue.Queue[dict] = queue.Queue()

    def send(msg: dict) -> None:
        proc.stdin.write(json.dumps(msg) + "\n")
        proc.stdin.flush()

    def request(method: str, params: dict) -> dict:
        """送一個帶 id 的請求，並等伺服器回覆。"""
        rid = next(_id)
        send({"id": rid, "method": method, "params": params})
        while True:
            msg = responses.get()
            if msg.get("id") == rid:
                if "error" in msg:
                    sys.exit(f"{method} 失敗：{msg['error']}")
                return msg["result"]

    def reader() -> None:
        for line in proc.stdout:
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue
            method = msg.get("method", "")
            # 1) 人審核：Codex 想跑指令 → 這裡就是你的產品放「Approve」按鈕的地方
            if method == "item/commandExecution/requestApproval":
                cmd = msg.get("params", {}).get("command", "")
                print(f"\n[審核] Codex 想執行：{cmd}")
                ok = input("允許嗎？(y/N) ").strip().lower() == "y"
                send({"id": msg["id"], "result": "accept" if ok else "decline"})
            elif method == "item/fileChange/requestApproval":
                print("\n[審核] Codex 想修改檔案")
                ok = input("允許嗎？(y/N) ").strip().lower() == "y"
                send({"id": msg["id"], "result": "accept" if ok else "decline"})
            # 2) 事件串流：把 agent 的訊息即時印出來（你的產品可以拿去畫進度）
            elif method == "item/agentMessage/delta":
                print(msg.get("params", {}).get("textDelta", ""), end="", flush=True)
            elif method == "turn/completed":
                print("\n[turn 完成]")
                proc.terminate()
            elif "id" in msg and "method" not in msg:  # 對我們請求的回覆
                responses.put(msg)

    threading.Thread(target=reader, daemon=True).start()

    request("initialize", {"clientInfo": {"name": "todo-api-demo", "version": "0.1.0"}})
    send({"method": "initialized", "params": {}})
    thread = request("thread/start", {})
    thread_id = thread["thread"]["id"]
    print(f"[thread] {thread_id}")
    send({"id": next(_id), "method": "turn/start",
          "params": {"threadId": thread_id, "input": [{"type": "text", "text": prompt}]}})
    proc.wait()


if __name__ == "__main__":
    main()
