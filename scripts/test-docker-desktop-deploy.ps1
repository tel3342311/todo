<# Run deployment control-flow tests without a Docker daemon or network access. #>
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$deploymentScript = Join-Path $PSScriptRoot 'deploy-docker-desktop.ps1'
$testState = @{ Scenario = ''; DockerCalls = @(); HealthCalls = 0 }

# These doubles replace the two external boundaries, not deployment decisions.
function docker {
    $command = $args -join ' '
    $testState.DockerCalls += $command
    $global:LASTEXITCODE = 0
    if ($command -like '* info --format *') {
        if ($testState.Scenario -eq 'engine-unavailable') { $global:LASTEXITCODE = 1; return }
        if ($testState.Scenario -eq 'windows-engine') { return 'windows' }
        return 'linux'
    }
    if ($command -like '* build --pull' -and $testState.Scenario -eq 'build-failure') {
        $global:LASTEXITCODE = 1
    }
    if ($command -like '* up *' -and $testState.Scenario -eq 'healthcheck-failure') {
        $global:LASTEXITCODE = 1
    }
}

function Invoke-RestMethod {
    param([string]$Uri, [int]$TimeoutSec)
    $testState.HealthCalls++
    if ($Uri -ne 'http://127.0.0.1:8080/health' -or $TimeoutSec -le 0) {
        throw 'Unexpected readiness request.'
    }
    if ($testState.Scenario -eq 'wrong-version') { return @{ status = 'ok'; version = 'old' } }
    return @{ status = 'ok'; version = 'test-sha' }
}

$savedVersion = $env:APP_VERSION
$savedPort = $env:TODO_PORT
try {
    foreach ($scenario in @('healthy', 'windows-engine', 'engine-unavailable', 'build-failure', 'healthcheck-failure', 'wrong-version')) {
        $testState.Scenario = $scenario
        $testState.DockerCalls = @()
        $testState.HealthCalls = 0
        $env:APP_VERSION = 'previous-version'
        $env:TODO_PORT = '9090'
        $failed = $false
        $failureMessage = ''
        try { & $deploymentScript -ImageTag 'test-sha' -Port 8080 | Out-Null }
        catch { $failed = $true; $failureMessage = $_.Exception.Message }

        if ($failed -ne ($scenario -ne 'healthy')) {
            throw "Unexpected result for ${scenario}: $failureMessage"
        }
        if ($env:APP_VERSION -ne 'previous-version' -or $env:TODO_PORT -ne '9090') {
            throw "Deployment leaked environment changes for $scenario."
        }
        $upCalls = @($testState.DockerCalls | Where-Object { $_ -like '* up *' })
        if ($scenario -in @('windows-engine', 'engine-unavailable', 'build-failure') -and $upCalls.Count -ne 0) {
            throw "Deployment replaced the container after a preflight/build failure: $scenario."
        }
        if ($scenario -eq 'healthy' -and ($upCalls.Count -ne 1 -or $testState.HealthCalls -ne 1)) {
            throw 'Healthy deployment did not start and verify the app.'
        }
        if ($scenario -eq 'healthcheck-failure' -and $testState.HealthCalls -ne 0) {
            throw 'Deployment continued after Compose reported an unhealthy container.'
        }
        if (@($testState.DockerCalls | Where-Object { $_ -match '(^| )(down|rm|prune)( |$)' }).Count -gt 0) {
            throw 'Deployment attempted a destructive cleanup.'
        }
        Write-Output "PASS: $scenario"
    }
} finally {
    $env:APP_VERSION = $savedVersion
    $env:TODO_PORT = $savedPort
}
