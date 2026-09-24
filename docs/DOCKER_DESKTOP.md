# Deploy to Docker Desktop with GitHub Actions

Pushing a commit to `main` triggers `.github/workflows/deploy-docker-desktop.yml`.
A local `git commit` does not contact GitHub; push it, or merge a pull request into `main`.
The workflow must first be merged into `main` to enable automatic deployment.

## Deployment flow

1. A GitHub-hosted Ubuntu runner runs Ruff, pytest, frontend tests, and deployment-script tests.
2. After tests pass, a Windows self-hosted runner with label `todo-docker-desktop` checks out that commit.
3. The runner builds the image using Docker Desktop's `desktop-linux` context, then recreates the app container.
4. Compose waits for container health. The script checks `/health` reports the exact commit SHA as its version.

The app is available at **http://localhost:8080** on the Docker Desktop PC.
The port binds only to `127.0.0.1`, not the LAN. A different machine cannot open this URL.
Set repository Actions variable `TODO_DESKTOP_PORT` to change the host port.
Workflow runs are serialized so two deployments cannot replace the app at the same time.

The original `Build and release` workflow is independent and still publishes to GHCR / prepares Kubernetes changes.
Docker Desktop deployment does not need a registry login, OpenAI API key, or Argo CD.

## One-time runner setup

**Do not register a personal-PC runner on this public repository with its current default fork policy.**
Prefer moving deployment to a private repository, or using an organization runner group restricted to this
workflow at `refs/heads/main`. Those provide a stronger boundary than a label or an `if` condition.
If a dedicated public-repository runner is used instead, first set **Settings → Actions → General →
Approval for running fork pull request workflows from contributors → Require approval for all outside collaborators**.
Verify the setting is `all_external_contributors` through the GitHub API before registering the runner:

```powershell
gh api repos/tel3342311/todo/actions/permissions/fork-pr-contributor-approval
```

This approval gate requires a maintainer to review every external contributor's workflow run. It does not
bind a runner to one workflow: approving a malicious fork workflow can still expose the host.
Never approve a fork workflow targeting a self-hosted runner, and keep deployment on a dedicated machine.

1. Install Docker Desktop and Git on the Windows PC. Start Docker Desktop in **Linux containers** mode.
   The repository's `python:3.12-slim` image cannot run on the Windows container engine.
2. In GitHub, open **Settings → Actions → Runners → New self-hosted runner**, selecting Windows / x64.
3. Follow GitHub's generated download and configuration commands in a dedicated directory **outside this repository**, such as `D:\actions-runner-todo`.
   Give the runner label `todo-docker-desktop` in addition to its default `self-hosted`, `Windows`, and `X64` labels.
4. Run `run.cmd` as the Windows user who runs Docker Desktop. Confirm the runner appears **Idle** in GitHub.
   The account needs access to Docker Desktop's named pipe. A runner installed as a different service account may not have access.
5. Keep the PC awake, Docker Desktop running, and the runner online. If any is stopped, queued deployments cannot execute.

Use a dedicated trusted machine for a self-hosted runner. This repository is public: the deployment workflow only runs on `main`,
and never uses a pull-request trigger. Review changes to `main`, workflow files, Dockerfile, and deployment scripts before merging.
GitHub recommends private repositories for self-hosted runners because public fork workflows can put a host at risk.
The job's `main` guard protects this workflow only; runner labels are routing labels, not access control.
Repository administrators must enforce the setup restrictions above and review all workflows that can target the runner.

Official setup references: [GitHub self-hosted runners](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/add-runners)
and [Docker Desktop engine switching](https://docs.docker.com/reference/cli/docker/desktop/engine/use/).

## Run or diagnose locally

```powershell
# Confirm that the required engine is available.
docker --context desktop-linux info

# Deploy the current checkout and check readiness.
./scripts/deploy-docker-desktop.ps1 -ImageTag dev -Port 8080

# Run deployment control-flow tests without a Docker daemon.
./scripts/test-docker-desktop-deploy.ps1

# Inspect the running app.
docker --context desktop-linux compose -p todo-desktop ps
docker --context desktop-linux compose -p todo-desktop logs --tail 100
Invoke-RestMethod http://localhost:8080/health
```

On Windows, run these commands in PowerShell from the repository root. If local script policy blocks execution,
use `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/deploy-docker-desktop.ps1` for this invocation.
If deployment is queued, check the runner's status and labels. If it fails before building, check Docker Desktop's engine mode.
The workflow also supports **Run workflow**, with `main` selected; selecting another branch will not run the local deployment job.

## Persistent data and failure behavior

SQLite lives at `/data/todo.db` in named volume **`todo-desktop-data`**. It survives container replacement and runner checkout cleanup.
It is separate from the development server's `todo.db` in this repository; existing local development tasks are not imported automatically.
Do not delete this volume or run `docker compose down --volumes` unless you intend to delete all containerized tasks.

Each deployment uses a commit-specific image tag and `APP_VERSION`. A build failure leaves the old container running.
A replacement that fails its health check fails the workflow and prints recent logs; it does **not** automatically roll back the database or image.
Back up the SQLite database before schema-changing deployments. Older images remain available locally for a deliberate rollback when their schema is compatible.
Use `docker compose up --wait` readiness behavior as described in the [Compose reference](https://docs.docker.com/reference/cli/docker/compose/up/).
