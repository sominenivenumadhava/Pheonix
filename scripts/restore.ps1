# Phoenix Database Restore (PowerShell)
param(
    [string]$BackupFile = "",
    [string]$TargetDb = "$PSScriptRoot\..\backend\phoenix.db",
    [string]$BackupDir = "$PSScriptRoot\..\..\phoenix_backups"
)

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " Phoenix Disaster Recovery - Database Restore" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

if ($BackupFile -ne "") {
    python "$PSScriptRoot\restore.py" --backup-file $BackupFile --target-db $TargetDb
} else {
    python "$PSScriptRoot\restore.py" --backup-dir $BackupDir --target-db $TargetDb
}
