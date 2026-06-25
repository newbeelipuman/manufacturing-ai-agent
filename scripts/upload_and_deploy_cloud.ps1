param(
    [string]$ServerIp = "43.136.25.67",
    [string]$User = "ubuntu",
    [string]$BaseUrl = "http://43.136.25.67",
    [switch]$ResetDemoVolume
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Dist = Join-Path $Root "dist-cloud"
$Zip = Join-Path $Dist "manufacturing-ai-agent-cloud.zip"
$Checksum = Join-Path $Dist "manufacturing-ai-agent-cloud.zip.sha256"
$Manifest = Join-Path $Dist "manufacturing-ai-agent-cloud.zip.manifest.json"
$Remote = "${User}@${ServerIp}"
$RemoteScript = "deploy-manufacturing-ai-agent.sh"
$LocalRemoteScript = Join-Path $env:TEMP $RemoteScript
$LocalReport = Join-Path $Root "docs\cloud-deployment-check-report.md"

function Invoke-NativeChecked {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Command,
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$Arguments
    )

    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Command failed with exit code $LASTEXITCODE"
    }
}

foreach ($Path in @($Zip, $Checksum, $Manifest)) {
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Missing deployment artifact: $Path"
    }
}

Push-Location $Root
try {
    python scripts\verify_cloud_package.py
}
finally {
    Pop-Location
}

Write-Host "Checking SSH login for $Remote ..."
try {
    Invoke-NativeChecked ssh $Remote "echo ssh-login-ok"
}
catch {
    Write-Host ""
    Write-Host "SSH login failed before upload."
    Write-Host "Use the same Linux username that worked in your manual login, for example:"
    Write-Host "  .\scripts\upload_and_deploy_cloud.ps1 -User root -ServerIp $ServerIp -BaseUrl $BaseUrl -ResetDemoVolume"
    Write-Host "Do not paste the server password into chat; type it only into the SSH prompt."
    throw
}

$RemoteScriptBody = @"
#!/usr/bin/env bash
set -euo pipefail

sudo apt-get update
sudo apt-get install -y unzip python3

cd "`$HOME"
sha256sum -c manufacturing-ai-agent-cloud.zip.sha256
if [[ -f manufacturing-ai-agent-cloud/.env.production && "$($ResetDemoVolume.IsPresent)" != "True" ]]; then
  cp manufacturing-ai-agent-cloud/.env.production .env.production.manufacturing-ai-agent.backup
fi
rm -rf manufacturing-ai-agent-cloud
mkdir -p manufacturing-ai-agent-cloud
unzip manufacturing-ai-agent-cloud.zip -d manufacturing-ai-agent-cloud
cd manufacturing-ai-agent-cloud
if [[ -f ../.env.production.manufacturing-ai-agent.backup && "$($ResetDemoVolume.IsPresent)" != "True" ]]; then
  mv ../.env.production.manufacturing-ai-agent.backup .env.production
fi
if [[ "$($ResetDemoVolume.IsPresent)" == "True" ]]; then
  export RESET_DEMO_VOLUME=1
fi
bash scripts/deploy_cloud_server.sh "$BaseUrl"
"@

[System.IO.File]::WriteAllText(
    $LocalRemoteScript,
    $RemoteScriptBody,
    [System.Text.UTF8Encoding]::new($false)
)

Write-Host "Uploading package artifacts to $Remote ..."
Invoke-NativeChecked scp $Zip $Checksum $Manifest "${Remote}:~/"

Write-Host "Uploading remote deployment script ..."
Invoke-NativeChecked scp $LocalRemoteScript "${Remote}:~/$RemoteScript"

Write-Host "Running remote deployment. Type the server password only into the SSH prompts."
try {
    Invoke-NativeChecked ssh $Remote "bash ~/$RemoteScript"
}
catch {
    Write-Host "Remote deployment failed. Fetching container diagnostics if available ..."
    ssh $Remote "cd ~/manufacturing-ai-agent-cloud 2>/dev/null && (sudo docker compose -f docker-compose.yml -f docker-compose.cloud.yml --env-file .env.production ps || true) && (sudo docker compose -f docker-compose.yml -f docker-compose.cloud.yml --env-file .env.production logs --tail=120 backend || true) && (sudo docker compose -f docker-compose.yml -f docker-compose.cloud.yml --env-file .env.production logs --tail=80 nginx || true) && (sudo docker compose -f docker-compose.yml -f docker-compose.cloud.yml --env-file .env.production logs --tail=80 postgres || true)" | Out-Host
    throw
}

Write-Host "Fetching cloud deployment report back to local docs ..."
Invoke-NativeChecked scp "${Remote}:~/manufacturing-ai-agent-cloud/docs/cloud-deployment-check-report.md" $LocalReport

Push-Location $Root
try {
    python scripts\verify_cloud_report.py --report docs\cloud-deployment-check-report.md
}
finally {
    Pop-Location
}

Write-Host "Cloud deployment report updated: $LocalReport"
