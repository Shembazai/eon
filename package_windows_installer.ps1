<#
.SYNOPSIS
Build a Windows source package for EON_PFA.

.DESCRIPTION
This script creates a ZIP archive in the dist/ directory that is safe to copy to a Windows machine.
The archive excludes large model and training artifacts, and includes the Windows install helper.
#>
[CmdletBinding()]
param(
    [string]$OutputDir = "dist",
    [string]$ReleaseName = "eon_pfa_source_$((Get-Date).ToString('yyyyMMdd_HHmmss'))"
)

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

if (Test-Path $OutputDir) {
    Remove-Item -Recurse -Force -Path $OutputDir
}
New-Item -ItemType Directory -Path $OutputDir | Out-Null

$archive = Join-Path $OutputDir "$ReleaseName.zip"

$excludePatterns = @(
    "$OutputDir",
    "dist",
    "reports",
    "models",
    "mistral_training",
    "__pycache__",
    ".pytest_cache",
    "profile.json",
    "profile_last_backup.json",
    "mastercard_summary.json",
    "change_journal.csv",
    "finance.db"
)

$files = Get-ChildItem -Recurse -Force | Where-Object {
    $relative = $_.FullName.Substring($root.Length).TrimStart('\','/')
    if ([string]::IsNullOrEmpty($relative)) { return $false }
    foreach ($exclude in $excludePatterns) {
        if ($relative -eq $exclude -or $relative -like "$exclude*") {
            return $false
        }
    }
    return $true
} | ForEach-Object {
    $_.FullName.Substring($root.Length).TrimStart('\','/')
}

if (-not $files) {
    throw "No files found to package."
}

Write-Host "Creating Windows package: $archive"
Compress-Archive -Path $files -DestinationPath $archive -Force
Write-Host "Windows package created successfully."
Write-Host "Copy the archive to Windows, extract it, and run .\\windows_install.ps1 to install."
