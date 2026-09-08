---
description: Check and optimize Windows performance, GPU, CPU, network, and desktop settings for gaming and productivity.
agent: build
---

# Performance Monitor & Optimizer

```bash
powershell -NoProfile -Command "
Write-Host '==================================================' -ForegroundColor Cyan
Write-Host '          WINDOWS PERFORMANCE STATUS CHECK         ' -ForegroundColor Yellow
Write-Host '==================================================' -ForegroundColor Cyan

# CPU Performance
$powerPlan = powercfg /getactivescheme
Write-Host '[*] Power Plan:' -NoNewline
if ($powerPlan -match '8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c') {
    Write-Host ' Ultimate Performance (Optimal)' -ForegroundColor Green
} else {
    Write-Host ' Balanced / Other (Can be optimized)' -ForegroundColor Yellow
}

# GPU / Hardware Accelerated GPU Scheduling (HAGS)
$hags = (Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\GraphicsDrivers' -Name 'HwSchMode' -ErrorAction SilentlyContinue).HwSchMode
Write-Host '[*] Hardware-Accelerated GPU Scheduling (HAGS):' -NoNewline
if ($hags -eq 2) {
    Write-Host ' Enabled (Optimal)' -ForegroundColor Green
} else {
    Write-Host ' Disabled / Not Set (Can be optimized)' -ForegroundColor Yellow
}

# Game Mode
$gameMode = (Get-ItemProperty 'HKCU:\Software\Microsoft\GameBar' -Name 'AutoGameModeEnabled' -ErrorAction SilentlyContinue).AutoGameModeEnabled
Write-Host '[*] Windows Game Mode:' -NoNewline
if ($gameMode -eq 1) {
    Write-Host ' Enabled (Optimal)' -ForegroundColor Green
} else {
    Write-Host ' Disabled / Not Set (Can be optimized)' -ForegroundColor Yellow
}

# Network Throttle (NetworkThrottlingIndex)
$netThrottle = (Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile' -Name 'NetworkThrottlingIndex' -ErrorAction SilentlyContinue).NetworkThrottlingIndex
Write-Host '[*] Network Throttling Index:' -NoNewline
if ($netThrottle -eq 3735928559 -or $netThrottle -eq 4294967295) {
    Write-Host ' Disabled / Unlimited (Optimal)' -ForegroundColor Green
} else {
    Write-Host ' Enabled / Default (Can be optimized)' -ForegroundColor Yellow
}

Write-Host '==================================================' -ForegroundColor Cyan
"

$choice = Read-Host "Do you want to apply optimizations now? (y/n)"
if ($choice -eq 'y') {
    Write-Host 'Applying optimizations...' -ForegroundColor Cyan
    powershell -NoProfile -Command "
    # Set Ultimate Performance Power Plan
    powercfg -duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c 2>&1 | Out-Null
    powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c 2>&1 | Out-Null

    # Enable HAGS
    Set-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Control\GraphicsDrivers' -Name 'HwSchMode' -Value 2 -ErrorAction SilentlyContinue

    # Enable Game Mode
    Set-ItemProperty -Path 'HKCU:\Software\Microsoft\GameBar' -Name 'AutoGameModeEnabled' -Value 1 -ErrorAction SilentlyContinue

    # Disable Network Throttling
    Set-ItemProperty -Path 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile' -Name 'NetworkThrottlingIndex' -Value 4294967295 -ErrorAction SilentlyContinue
    "
    Write-Host 'Optimizations applied successfully! Please restart your PC.' -ForegroundColor Green
} else {
    Write-Host 'Optimization skipped.' -ForegroundColor Yellow
}
```
