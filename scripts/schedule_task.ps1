# TrendLens: Register Windows Scheduled Task
# Runs twice daily at 09:00 AM and 06:00 PM (18:00)

$taskName = "TrendLens_News_Pipeline"
$scriptPath = "C:\Users\Abhiroop\Downloads\TrendLens_Full_Skeleton\TrendLens\scripts\run_scheduled_pipeline.bat"

Write-Host "Registering scheduled task '$taskName'..." -ForegroundColor Cyan

# Create triggers for 9:00 AM and 6:00 PM
$trigger1 = New-ScheduledTaskTrigger -Daily -At 9:00AM
$trigger2 = New-ScheduledTaskTrigger -Daily -At 6:00PM
$action = New-ScheduledTaskAction -Execute $scriptPath
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName $taskName -Trigger @($trigger1, $trigger2) -Action $action -Settings $settings -Description "TrendLens automated world news ingestion and trend computation" -Force

Write-Host "Task '$taskName' successfully registered in Windows Task Scheduler!" -ForegroundColor Green
Write-Host "It will run automatically every day at 09:00 AM and 06:00 PM."
