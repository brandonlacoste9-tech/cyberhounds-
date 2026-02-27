# 🐺 CYBERHOUND WINDOWS TASK SCHEDULER SETUP
# Sets up scheduled hunting via Windows Task Scheduler

param(
    [ValidateSet("30min", "1hour", "4hour", "daily", "custom")]
    [string]$Schedule = "30min",
    
    [string]$CustomSchedule,
    
    [switch]$Force
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir
$CronHunter = Join-Path $ProjectDir "hound_core\cron_hunt.py"
$PythonPath = "python"

Write-Host "🐺 Cyberhound Windows Task Scheduler Setup" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if cron hunter exists
if (-not (Test-Path $CronHunter)) {
    Write-Host "❌ cron_hunt.py not found at $CronHunter" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Found cron_hunt.py" -ForegroundColor Green

# Find Python
$PythonExe = Get-Command python -ErrorAction SilentlyContinue
if (-not $PythonExe) {
    $PythonExe = Get-Command python3 -ErrorAction SilentlyContinue
}
if (-not $PythonExe) {
    Write-Host "❌ Python not found in PATH" -ForegroundColor Red
    exit 1
}
$PythonPath = $PythonExe.Source
Write-Host "✅ Found Python: $PythonPath" -ForegroundColor Green

# Validate configuration
Write-Host ""
Write-Host "🔍 Validating configuration..." -ForegroundColor Yellow

Push-Location $ProjectDir
& $PythonPath $CronHunter --dry-run 2>&1 | Out-Null
$Valid = $?
Pop-Location

if (-not $Valid) {
    Write-Host "❌ Configuration validation failed" -ForegroundColor Red
    Write-Host "   Please configure targets in hound_core\data\targets.txt"
    exit 1
}

Write-Host "✅ Configuration valid" -ForegroundColor Green

# Determine schedule
Write-Host ""
Write-Host "📅 Selected Schedule: $Schedule" -ForegroundColor Yellow

switch ($Schedule) {
    "30min" {
        $IntervalMinutes = 30
        $Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 30) -RepetitionDuration ([TimeSpan]::MaxValue)
    }
    "1hour" {
        $IntervalMinutes = 60
        $Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 1) -RepetitionDuration ([TimeSpan]::MaxValue)
    }
    "4hour" {
        $IntervalMinutes = 240
        $Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 4) -RepetitionDuration ([TimeSpan]::MaxValue)
    }
    "daily" {
        $IntervalMinutes = 1440
        $Trigger = New-ScheduledTaskTrigger -Daily -At "9:00 AM"
    }
    "custom" {
        if (-not $CustomSchedule) {
            Write-Host "❌ Custom schedule required" -ForegroundColor Red
            exit 1
        }
        # Parse custom schedule
        Write-Host "Using custom schedule: $CustomSchedule"
        $Trigger = New-ScheduledTaskTrigger -Daily -At $CustomSchedule
    }
}

# Create task action
$Action = New-ScheduledTaskAction -Execute $PythonPath -Argument $CronHunter -WorkingDirectory $ProjectDir

# Create task settings
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable

# Register task
$TaskName = "CyberhoundCronHunter"

Write-Host ""
Write-Host "📝 Task to create:" -ForegroundColor Yellow
Write-Host "  Name: $TaskName"
Write-Host "  Schedule: Every $IntervalMinutes minutes"
Write-Host "  Command: $PythonPath $CronHunter"
Write-Host "  Working Dir: $ProjectDir"
Write-Host ""

$Confirm = Read-Host "Create this scheduled task? (y/N)"

if ($Confirm -eq "y" -or $Confirm -eq "Y") {
    try {
        # Remove existing task if exists
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
        
        # Register new task
        Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Force | Out-Null
        
        Write-Host "✅ Scheduled task created successfully!" -ForegroundColor Green
        Write-Host ""
        Write-Host "To check status:" -ForegroundColor Cyan
        Write-Host "  python hound_core\cron_hunt.py --status"
        Write-Host ""
        Write-Host "To view logs:" -ForegroundColor Cyan
        Write-Host "  Get-Content hound_core\data\logs\cron.log -Tail 50 -Wait"
        Write-Host ""
        Write-Host "To remove task:" -ForegroundColor Cyan
        Write-Host "  Unregister-ScheduledTask -TaskName $TaskName -Confirm:`$false"
        
    } catch {
        Write-Host "❌ Failed to create task: $_" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "❌ Cancelled"
    exit 0
}

Write-Host ""
Write-Host "✅ Windows Task Scheduler setup complete!" -ForegroundColor Green
