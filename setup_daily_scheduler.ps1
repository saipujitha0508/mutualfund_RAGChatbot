# Setup Windows Task Scheduler for Daily 9:15 AM IST Refresh
# This script creates a scheduled task to run the ingest pipeline daily

$TaskName = "Navi RAG Daily Data Refresh"
$ScriptPath = "C:\Users\hp\CascadeProjects\navi-mutual-fund-rag\runtime\scheduler\local_scheduler.py"
$PythonPath = "python"
$ProjectDir = "C:\Users\hp\CascadeProjects\navi-mutual-fund-rag"

# Convert 9:15 AM IST to local time (assuming system is in IST)
# If system is in different timezone, adjust accordingly
$TriggerTime = "09:15"

# Create the scheduled task action
$Action = New-ScheduledTaskAction `
    -Execute $PythonPath `
    -Argument "$ScriptPath" `
    -WorkingDirectory $ProjectDir

# Create the trigger - Daily at 9:15 AM
$Trigger = New-ScheduledTaskTrigger `
    -Daily `
    -At $TriggerTime

# Create the task principal (run as current user, only when logged in)
$Principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType Interactive `
    -RunLevel Highest

# Create the task settings
$Settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -DontStopOnIdleEnd `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries

# Register the scheduled task
Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Principal $Principal `
    -Settings $Settings `
    -Description "Runs the Navi RAG ingest pipeline daily at 9:15 AM IST to refresh data from sources" `
    -Force

Write-Host "Scheduled task '$TaskName' created successfully!"
Write-Host "It will run daily at $TriggerTime"
Write-Host ""
Write-Host "To verify the task, open Task Scheduler and look for '$TaskName'"
Write-Host "To run the task manually, use: Start-ScheduledTask -TaskName '$TaskName'"
Write-Host "To delete the task, use: Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:$false"
