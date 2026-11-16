# Phoenix Database Backup (PowerShell)
param(
    [string]$DbPath = "$PSScriptRoot\..\backend\phoenix.db",
    [string]$BackupDir = "$PSScriptRoot\..\..\phoenix_backups"
)

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " Phoenix Disaster Recovery - Database Backup" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

python "$PSScriptRoot\backup.py" --db-path $DbPath --backup-dir $BackupDir
