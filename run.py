"""跨平台工作指令（Makefile 的 Windows / macOS 通用版）。

用法：python run.py <指令>
  dev              啟動開發伺服器  http://localhost:8000
  test             pytest -q
  lint             ruff check .
  build            docker build -t todo-api:dev .
  kind-up          建立 kind 叢集 harness-lab（NodePort 30080 → localhost:30080）
  kind-down        刪除 kind 叢集
  argocd-install   安裝 Argo CD 到 kind
  argocd-password  印出 Argo CD admin 初始密碼
  set-owner <you>  把 k8s/ 與 argocd/ 裡的 CHANGE_ME 換成你的 GitHub 帳號（小寫）

macOS / Linux 也可以直接用 make；Windows 沒有 make，就用這支。
"""
from __future__ import annotations

import base64
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
PY = sys.executable  # 用目前這個 Python（venv 內），避免 python / python3 名稱差異

if hasattr(sys.stdout, "reconfigure"):  # Windows 主控台預設不是 UTF-8
    sys.stdout.reconfigure(encoding="utf-8")


def sh(*cmd: str, check: bool = True, capture: bool = False) -> subprocess.CompletedProcess:
    print("$", " ".join(cmd))
    return subprocess.run(cmd, cwd=ROOT, check=check, capture_output=capture, text=True)


def dev() -> None:
    sh(PY, "-m", "uvicorn", "app.main:app", "--reload", "--port", "8000")


def test() -> None:
    sh(PY, "-m", "pytest", "-q")


def lint() -> None:
    sh(PY, "-m", "ruff", "check", ".")


def build() -> None:
    sh("docker", "build", "-t", "todo-api:dev", ".")


def kind_up() -> None:
    sh("kind", "create", "cluster", "--name", "harness-lab", "--config", "k8s/kind-config.yaml")


def kind_down() -> None:
    sh("kind", "delete", "cluster", "--name", "harness-lab")


def argocd_install() -> None:
    sh("kubectl", "create", "namespace", "argocd", check=False)
    sh("kubectl", "apply", "-n", "argocd", "-f",
       "https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml")
    sh("kubectl", "wait", "-n", "argocd", "--for=condition=available",
       "deploy/argocd-server", "--timeout=300s")
    print("Argo CD 已就緒。接著：python run.py set-owner <你的 GitHub 帳號> → "
          "kubectl apply -f argocd/application.yaml")


def argocd_password() -> None:
    r = sh("kubectl", "-n", "argocd", "get", "secret", "argocd-initial-admin-secret",
           "-o", "jsonpath={.data.password}", capture=True)
    print("admin 密碼：", base64.b64decode(r.stdout).decode())
    print("UI：kubectl port-forward svc/argocd-server -n argocd 8080:443 → https://localhost:8080")


def set_owner(owner: str) -> None:
    owner = owner.lower()  # GHCR 的 image 名稱只接受小寫
    for rel in ("k8s/deployment.yaml", "argocd/application.yaml"):
        p = ROOT / rel
        text = p.read_text(encoding="utf-8")
        if "CHANGE_ME" not in text:
            print(f"{rel}: 已經設定過，略過")
            continue
        p.write_text(text.replace("CHANGE_ME", owner), encoding="utf-8")
        print(f"{rel}: CHANGE_ME → {owner}")
    print("記得 git commit 並 push，Argo CD 與 kind 才拉得到正確的 repo / image。")


COMMANDS = {
    "dev": dev, "test": test, "lint": lint, "build": build,
    "kind-up": kind_up, "kind-down": kind_down,
    "argocd-install": argocd_install, "argocd-password": argocd_password,
}


def main(argv: list[str]) -> int:
    if not argv or argv[0] in {"-h", "--help", "help"}:
        print(__doc__)
        return 0
    name, *rest = argv
    if name == "set-owner":
        if not rest:
            print("用法：python run.py set-owner <你的 GitHub 帳號>")
            return 2
        set_owner(rest[0])
        return 0
    fn = COMMANDS.get(name)
    if fn is None:
        print(f"不認識的指令：{name}\n{__doc__}")
        return 2
    try:
        fn()
    except subprocess.CalledProcessError as e:
        return e.returncode
    except FileNotFoundError as e:
        print(f"找不到指令：{e.filename}（請先安裝，見手冊實作 0）")
        return 127
    return 0


if __name__ == "__main__":
    os.chdir(ROOT)
    raise SystemExit(main(sys.argv[1:]))
