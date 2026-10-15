$ErrorActionPreference = 'Stop'
$taskAppPath = Join-Path $PSScriptRoot 'app.py'
$taskListeners = Get-NetTCPConnection -LocalPort 8391 -State Listen -ErrorAction SilentlyContinue
foreach ($taskListener in $taskListeners) {
    $taskServerProcess = Get-CimInstance Win32_Process -Filter "ProcessId=$($taskListener.OwningProcess)"
    if ($taskServerProcess.CommandLine -and $taskServerProcess.CommandLine.Contains($taskAppPath)) {
        Stop-Process -Id $taskListener.OwningProcess
        Write-Output 'Humanize Lab stopped.'
    }
}
