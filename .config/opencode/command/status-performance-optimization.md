---
description: Check and optimize Windows performance, GPU, CPU, network, and desktop settings for gaming and productivity. Backs up previous values and can restore them.
agent: build
---

# Performance Monitor & Optimizer

```bash
#Requires -RunAsAdministrator

$backupPath = "$env:USERPROFILE\Desktop\perf-optimizer-backup.json"

function Test-Status {
    Write-Host '==================================================' -ForegroundColor Cyan
    Write-Host '          WINDOWS PERFORMANCE STATUS CHECK         ' -ForegroundColor Yellow
    Write-Host '==================================================' -ForegroundColor Cyan

    # Power Plan
    $activeScheme = (powercfg /getactivescheme)
    Write-Host '[*] Power Plan:' -NoNewline
    if ($activeScheme -match '8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c') {
        Write-Host ' Ultimate Performance (Optimal)' -ForegroundColor Green
    } else {
        Write-Host ' Balanced / Other (Can be optimized)' -ForegroundColor Yellow
    }

    # Hardware-Accelerated GPU Scheduling
    $hags = (Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\GraphicsDrivers' -Name 'HwSchMode' -ErrorAction SilentlyContinue).HwSchMode
    Write-Host '[*] Hardware-Accelerated GPU Scheduling (HAGS):' -NoNewline
    if ($hags -eq 2) { Write-Host ' Enabled (Optimal)' -ForegroundColor Green }
    else { Write-Host ' Disabled / Not Set (Can be optimized)' -ForegroundColor Yellow }

    # Game Mode
    $gameMode = (Get-ItemProperty 'HKCU:\Software\Microsoft\GameBar' -Name 'AutoGameModeEnabled' -ErrorAction SilentlyContinue).AutoGameModeEnabled
    Write-Host '[*] Windows Game Mode:' -NoNewline
    if ($gameMode -eq 1) { Write-Host ' Enabled (Optimal)' -ForegroundColor Green }
    else { Write-Host ' Disabled / Not Set (Can be optimized)' -ForegroundColor Yellow }

    # Network Throttling Index (0xFFFFFFFF / 4294967295 = unlimited)
    $netThrottle = (Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile' -Name 'NetworkThrottlingIndex' -ErrorAction SilentlyContinue).NetworkThrottlingIndex
    Write-Host '[*] Network Throttling Index:' -NoNewline
    if ($netThrottle -eq 4294967295) { Write-Host ' Disabled / Unlimited (Optimal)' -ForegroundColor Green }
    else { Write-Host ' Enabled / Default (Can be optimized)' -ForegroundColor Yellow }

    # System Responsiveness (0 = prioritize foreground/game tasks)
    $sysResp = (Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile' -Name 'SystemResponsiveness' -ErrorAction SilentlyContinue).SystemResponsiveness
    Write-Host '[*] System Responsiveness:' -NoNewline
    if ($sysResp -eq 0) { Write-Host ' 0 - Games prioritized (Optimal)' -ForegroundColor Green }
    else { Write-Host " $sysResp (Can be optimized)" -ForegroundColor Yellow }

    # Xbox Game Bar / Game DVR background recording
    $gameDvr = (Get-ItemProperty 'HKCU:\System\GameConfigStore' -Name 'GameDVR_Enabled' -ErrorAction SilentlyContinue).GameDVR_Enabled
    Write-Host '[*] Xbox Game DVR (background recording):' -NoNewline
    if ($gameDvr -eq 0) { Write-Host ' Disabled (Optimal)' -ForegroundColor Green }
    else { Write-Host ' Enabled / Not Set (Can be optimized)' -ForegroundColor Yellow }

    # Fullscreen Optimizations (global default for apps that don't override it)
    $fso = (Get-ItemProperty 'HKCU:\System\GameConfigStore' -Name 'GameDVR_FSEBehaviorMode' -ErrorAction SilentlyContinue).GameDVR_FSEBehaviorMode
    Write-Host '[*] Fullscreen Optimizations default:' -NoNewline
    if ($fso -eq 2) { Write-Host ' Disabled (Optimal for older/exclusive-fullscreen games)' -ForegroundColor Green }
    else { Write-Host ' Enabled / Not Set (fine for most modern games)' -ForegroundColor Yellow }

    Write-Host '=================================================='  -ForegroundColor Cyan
}

function Backup-Values {
    $current = @{
        PowerPlan             = (powercfg /getactivescheme | Select-String -Pattern '([0-9a-f-]{36})').Matches[0].Value
        HwSchMode             = (Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\GraphicsDrivers' -Name 'HwSchMode' -ErrorAction SilentlyContinue).HwSchMode
        AutoGameModeEnabled   = (Get-ItemProperty 'HKCU:\Software\Microsoft\GameBar' -Name 'AutoGameModeEnabled' -ErrorAction SilentlyContinue).AutoGameModeEnabled
        NetworkThrottlingIndex= (Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile' -Name 'NetworkThrottlingIndex' -ErrorAction SilentlyContinue).NetworkThrottlingIndex
        SystemResponsiveness  = (Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile' -Name 'SystemResponsiveness' -ErrorAction SilentlyContinue).SystemResponsiveness
        GameDVR_Enabled       = (Get-ItemProperty 'HKCU:\System\GameConfigStore' -Name 'GameDVR_Enabled' -ErrorAction SilentlyContinue).GameDVR_Enabled
        GameDVR_FSEBehaviorMode = (Get-ItemProperty 'HKCU:\System\GameConfigStore' -Name 'GameDVR_FSEBehaviorMode' -ErrorAction SilentlyContinue).GameDVR_FSEBehaviorMode
    }
    $current | ConvertTo-Json | Out-File -FilePath $backupPath -Encoding utf8
    Write-Host "[*] Backup saved to $backupPath" -ForegroundColor DarkGray
}

function Apply-Optimizations {
    Write-Host 'Creating a System Restore point (safety net)...' -ForegroundColor Cyan
    try {
        Checkpoint-Computer -Description 'Pre perf-optimizer changes' -RestorePointType 'MODIFY_SETTINGS' -ErrorAction Stop
    } catch {
        Write-Host '  Could not create a restore point (may be disabled on this PC). Continuing.' -ForegroundColor Yellow
    }

    Backup-Values

    Write-Host 'Applying optimizations...' -ForegroundColor Cyan

    # Ultimate Performance power plan
    powercfg -duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c 2>&1 | Out-Null
    powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c 2>&1 | Out-Null

    # HAGS
    Set-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Control\GraphicsDrivers' -Name 'HwSchMode' -Value 2 -ErrorAction SilentlyContinue

    # Game Mode
    Set-ItemProperty -Path 'HKCU:\Software\Microsoft\GameBar' -Name 'AutoGameModeEnabled' -Value 1 -ErrorAction SilentlyContinue

    # Network throttling off
    Set-ItemProperty -Path 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile' -Name 'NetworkThrottlingIndex' -Value 4294967295 -ErrorAction SilentlyContinue

    # System responsiveness -> prioritize foreground/games
    Set-ItemProperty -Path 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile' -Name 'SystemResponsiveness' -Value 0 -ErrorAction SilentlyContinue

    # Disable Xbox Game DVR background recording
    Set-ItemProperty -Path 'HKCU:\System\GameConfigStore' -Name 'GameDVR_Enabled' -Value 0 -ErrorAction SilentlyContinue

    # Disable global fullscreen optimizations (helps some older/exclusive-fullscreen titles; safe to leave default otherwise)
    Set-ItemProperty -Path 'HKCU:\System\GameConfigStore' -Name 'GameDVR_FSEBehaviorMode' -Value 2 -ErrorAction SilentlyContinue

    Write-Host 'Optimizations applied. Restart your PC for all changes to take effect.' -ForegroundColor Green
}

function Restore-Defaults {
    if (-not (Test-Path $backupPath)) {
        Write-Host "No backup found at $backupPath — nothing to restore." -ForegroundColor Yellow
        return
    }
    $backup = Get-Content $backupPath | ConvertFrom-Json
    if ($backup.PowerPlan) { powercfg /setactive $backup.PowerPlan 2>&1 | Out-Null }
    if ($null -ne $backup.HwSchMode) { Set-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Control\GraphicsDrivers' -Name 'HwSchMode' -Value $backup.HwSchMode -ErrorAction SilentlyContinue }
    if ($null -ne $backup.AutoGameModeEnabled) { Set-ItemProperty -Path 'HKCU:\Software\Microsoft\GameBar' -Name 'AutoGameModeEnabled' -Value $backup.AutoGameModeEnabled -ErrorAction SilentlyContinue }
    if ($null -ne $backup.NetworkThrottlingIndex) { Set-ItemProperty -Path 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile' -Name 'NetworkThrottlingIndex' -Value $backup.NetworkThrottlingIndex -ErrorAction SilentlyContinue }
    if ($null -ne $backup.SystemResponsiveness) { Set-ItemProperty -Path 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile' -Name 'SystemResponsiveness' -Value $backup.SystemResponsiveness -ErrorAction SilentlyContinue }
    if ($null -ne $backup.GameDVR_Enabled) { Set-ItemProperty -Path 'HKCU:\System\GameConfigStore' -Name 'GameDVR_Enabled' -Value $backup.GameDVR_Enabled -ErrorAction SilentlyContinue }
    if ($null -ne $backup.GameDVR_FSEBehaviorMode) { Set-ItemProperty -Path 'HKCU:\System\GameConfigStore' -Name 'GameDVR_FSEBehaviorMode' -Value $backup.GameDVR_FSEBehaviorMode -ErrorAction SilentlyContinue }
    Write-Host 'Previous values restored. Restart your PC for changes to take effect.' -ForegroundColor Green
}

# --- Entry point ---
Test-Status

Write-Host ''
Write-Host '1) Apply optimizations   2) Restore previous values   3) Exit' -ForegroundColor Cyan
$choice = Read-Host 'Choose an option (1/2/3)'
switch ($choice) {
    '1' { Apply-Optimizations }
    '2' { Restore-Defaults }
    default { Write-Host 'No changes made.' -ForegroundColor Yellow }
}
```