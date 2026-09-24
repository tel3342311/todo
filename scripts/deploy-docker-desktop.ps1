<#
.SYNOPSIS
Build and deploy this checkout to Docker Desktop's Linux engine without deleting task data.
#>
[CmdletBinding()]
param(
    [ValidatePattern('^[a-zA-Z0-9_][a-zA-Z0-9_.-]{0,127}$')]
    [string]$ImageTag = 'dev',

    [ValidateRange(1, 65535)]
    [int]$Port = 8080
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$repoRoot = Split-Path -Parent $PSScriptRoot
$composeFile = Join-Path $repoRoot 'compose.yaml'
$dockerOptions = @('--context', 'desktop-linux')
$composeOptions = $dockerOptions + @('compose', '--project-name', 'todo-desktop', '--file', $composeFile)

function Invoke-Docker {
    param([Parameter(Mandatory)][string[]]$DockerArguments)
    & docker @DockerArguments
    if ($LASTEXITCODE -ne 0) {
        throw "Docker command failed with exit code $LASTEXITCODE."
    }
}

$previousVersion = $env:APP_VERSION
$previousPort = $env:TODO_PORT
try {
    $env:APP_VERSION = $ImageTag
    $env:TODO_PORT = [string]$Port
    $engineType = & docker @dockerOptions info --format '{{.OSType}}'
    if ($LASTEXITCODE -ne 0 -or $engineType -ne 'linux') {
        throw 'Start Docker Desktop and switch to Linux containers before deploying.'
    }

    Invoke-Docker -DockerArguments ($composeOptions + @('config', '--quiet'))
    # Build first: a failed build must leave the currently running container intact.
    Invoke-Docker -DockerArguments ($composeOptions + @('build', '--pull'))
    Invoke-Docker -DockerArguments ($composeOptions + @('up', '--detach', '--no-build', '--wait', '--wait-timeout', '120'))

    $health = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/health" -TimeoutSec 10
    if ($health.status -ne 'ok' -or $health.version -ne $ImageTag) {
        throw 'The deployed application did not report the expected version and healthy status.'
    }
    Write-Output "Deployed $ImageTag to http://localhost:$Port (SQLite volume: todo-desktop-data)."
} catch {
    # Diagnostics only: do not remove the persistent volume or hide a failed deployment.
    & docker @composeOptions logs --tail 80
    throw
} finally {
    $env:APP_VERSION = $previousVersion
    $env:TODO_PORT = $previousPort
}
