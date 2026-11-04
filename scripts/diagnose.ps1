# Read-only Windows environment diagnostics. No identifiers, secrets or raw tool errors are emitted.
[CmdletBinding()]
param([switch]$Json)

$ErrorActionPreference = 'Continue'
function Check($state, $detail, $next) {
    return [ordered]@{ status = $state; detail = $detail; next_step = $next }
}
function Has-Command($name) { return [bool](Get-Command $name -ErrorAction SilentlyContinue) }
function Invoke-Quiet($program, [string[]]$arguments) {
    try {
        $lines = @(& $program @arguments 2>$null)
        return @{ ok = ($LASTEXITCODE -eq 0); lines = $lines; code = $LASTEXITCODE }
    } catch {
        return @{ ok = $false; lines = @(); code = $null }
    }
}
$report = [ordered]@{
    schema_version = 1
    scope = 'Windows environment only; FLOP support and operator enrollment NOT verified'
    windows = $null
    gpus = @()
    wsl = $null
    docker = $null
    official_runtime = @{ status = 'NOT_IMPLEMENTED'; reason = 'official operator assets required' }
}
try {
    $os = Get-CimInstance Win32_OperatingSystem -ErrorAction Stop
    $version = [Environment]::OSVersion.Version
    $report.windows = [ordered]@{
        status = 'pass'
        caption = [string]$os.Caption
        version = [string]$os.Version
        build = [string]$os.BuildNumber
        wsl2_minimum = if ($version.Major -eq 10 -and $version.Build -ge 22000) { 'Windows 11: check WSL2 and current updates' } elseif ($version.Major -eq 10 -and $version.Build -ge 19044) { 'Windows 10 21H2+: check WSL2 and current updates' } else { 'unknown or older than Windows 10 21H2; update Windows before WSL2 GPU setup' }
    }
} catch {
    $report.windows = Check 'unknown' 'Windows version/build query unavailable' 'Check Windows Settings > System > About.'
}
if (Has-Command 'nvidia-smi') {
    $gpuQuery = Invoke-Quiet 'nvidia-smi' @('--query-gpu=name,memory.total,driver_version', '--format=csv,noheader,nounits')
    if ($gpuQuery.ok) {
        foreach ($line in $gpuQuery.lines) {
            if ([string]::IsNullOrWhiteSpace($line)) { continue }
            # Parse CSV rather than splitting names containing commas; no UUID is requested.
            try {
                $parsed = @($line | ConvertFrom-Csv -Header 'name','memory_mib','driver_version')
                $gpu = $parsed[0]
                $memory = 0
                $hasMemory = [int]::TryParse(([string]$gpu.memory_mib).Trim(), [ref]$memory)
                $report.gpus += [ordered]@{
                    index = $report.gpus.Count
                    name = ([string]$gpu.name).Trim()
                    uuid = '[redacted]'
                    memory_total_mib = if ($hasMemory) { $memory } else { $null }
                    driver_version = ([string]$gpu.driver_version).Trim()
                    status = 'visible in Windows; FLOP compatibility not verified'
                }
            } catch { continue }
        }
    }
    $report.gpu_check = if ($report.gpus.Count -gt 0) { Check 'pass' "$($report.gpus.Count) NVIDIA GPU(s) detected in Windows" 'Check GPU access in WSL2 and the container separately.' } else { Check 'unknown' 'NVIDIA driver query did not return usable GPU rows' 'Check Windows NVIDIA driver and run nvidia-smi manually.' }
} else {
    $report.gpu_check = Check 'unknown' 'nvidia-smi unavailable; NVIDIA GPU/driver not established' 'Install or check the Windows NVIDIA driver; other GPU brands are not verified.'
}
if (Has-Command 'wsl.exe') {
    $wslResult = Invoke-Quiet 'wsl.exe' @('--list', '--verbose')
    if ($wslResult.ok) {
        $distributions = @()
        foreach ($line in $wslResult.lines) {
            $text = ([string]$line).Replace([string][char]0, '').Trim()
            if ($text -match '^\*?\s*(?<name>.+?)\s+(?<state>Running|Stopped|Installing|Uninstalling|Converting)\s+(?<version>[12])\s*$') {
                $distributions += [ordered]@{ name = if ($Matches.name.Trim() -eq 'Ubuntu-24.04') { 'Ubuntu-24.04' } else { '[redacted distro name]' }; state = $Matches.state; wsl_version = [int]$Matches.version }
            }
        }
        $ubuntu2 = @($distributions | Where-Object { $_.name -eq 'Ubuntu-24.04' -and $_.wsl_version -eq 2 }).Count -gt 0
        $ubuntuRunning = @($distributions | Where-Object { $_.name -eq 'Ubuntu-24.04' -and $_.wsl_version -eq 2 -and $_.state -eq 'Running' }).Count -gt 0
        $report.wsl = [ordered]@{
            status = if ($ubuntuRunning) { 'pass' } elseif ($ubuntu2) { 'unknown' } else { 'needs intervention' }
            detail = if ($ubuntuRunning) { 'Ubuntu-24.04 WSL2 distro is running; GPU access inside WSL still unverified' } elseif ($ubuntu2) { 'Ubuntu-24.04 WSL2 distro registered but stopped; boot and virtualization not verified' } else { 'Ubuntu-24.04 WSL2 distro not established' }
            distributions = $distributions
            next_step = 'Check wsl --status; if virtualization is unavailable enable it per Microsoft guidance. Check Ubuntu-24.04 is WSL version 2.'
        }
    } else {
        $report.wsl = Check 'needs intervention' 'WSL distro query failed; virtualization/WSL state unknown' 'Run wsl --status manually; check virtualization, WSL2 prerequisites and reboot requirements.'
    }
} else {
    $report.wsl = Check 'needs intervention' 'wsl.exe unavailable' 'Consult Microsoft WSL installation guidance; do not install a Linux NVIDIA driver inside WSL.'
}
$desktopInstalled = [bool](Test-Path "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe")
if (-not (Has-Command 'docker')) {
    $report.docker = [ordered]@{
        desktop = Check $(if ($desktopInstalled) { 'pass' } else { 'unknown' }) $(if ($desktopInstalled) { 'Docker Desktop executable found' } else { 'Docker Desktop not detected at default location' }) 'Check the official Docker Desktop installer.'
        engine = Check 'needs intervention' 'docker CLI unavailable; Linux engine not verified' 'Install/start Docker Desktop and select WSL2 Linux engine.'
        compose = Check 'needs intervention' 'docker CLI unavailable; Compose not verified' 'Use Docker Desktop with the Compose plugin.'
        wsl_integration = Check 'unknown' 'Per-distribution WSL integration cannot be inferred from Windows CLI' 'Enable WSL Integration for Ubuntu-24.04 in Docker Desktop settings; verify docker info inside Ubuntu.'
    }
} else {
    $engine = Invoke-Quiet 'docker' @('info', '--format', '{{.OSType}}')
    $linuxEngine = $engine.ok -and (@($engine.lines | Where-Object { ([string]$_).Trim() -eq 'linux' }).Count -gt 0)
    $compose = Invoke-Quiet 'docker' @('compose', 'version', '--short')
    $report.docker = [ordered]@{
        desktop = Check $(if ($desktopInstalled) { 'pass' } else { 'unknown' }) $(if ($desktopInstalled) { 'Docker Desktop executable found at default location' } else { 'Docker CLI found; Docker Desktop installation not established' }) 'Confirm Docker Desktop is running.'
        engine = if ($linuxEngine) { Check 'pass' 'Docker daemon reports Linux engine' 'Verify GPU passthrough using the pinned CUDA diagnostic container.' } elseif ($engine.ok) { Check 'needs intervention' 'Docker engine is not Linux' 'Switch Docker Desktop to Linux containers/WSL2 backend.' } else { Check 'needs intervention' 'Docker daemon unreachable or engine type unavailable' 'Start Docker Desktop; check Docker Desktop Linux engine.' }
        compose = if ($compose.ok) { Check 'pass' 'Docker Compose plugin available' 'Confirm integration inside the WSL distribution.' } else { Check 'needs intervention' 'Docker Compose plugin unavailable' 'Install/check Docker Desktop Compose plugin.' }
        wsl_integration = Check 'unknown' 'Windows-side Docker access does not establish Ubuntu WSL integration' 'Enable WSL Integration for Ubuntu-24.04 and run docker info inside Ubuntu.'
    }
}
if ($Json) {
    $report | ConvertTo-Json -Depth 8 -Compress
} else {
    Write-Output 'Windows / Windows:'
    Write-Output ($report.windows | ConvertTo-Json -Compress)
    Write-Output "GPU / GPU: $($report.gpu_check.status) - $($report.gpu_check.detail)"
    foreach ($gpu in $report.gpus) { Write-Output "  [$($gpu.index)] $($gpu.name); VRAM: $($gpu.memory_total_mib) MiB; driver: $($gpu.driver_version); UUID: [redacted]" }
    Write-Output "WSL2 / WSL2: $($report.wsl.status) - $($report.wsl.detail)"
    foreach ($distro in $report.wsl.distributions) { Write-Output "  $($distro.name): $($distro.state), WSL $($distro.wsl_version)" }
    Write-Output "Docker Desktop: $($report.docker.desktop.status) - $($report.docker.desktop.detail)"
    Write-Output "Docker Linux engine: $($report.docker.engine.status) - $($report.docker.engine.detail)"
    Write-Output "Compose: $($report.docker.compose.status) - $($report.docker.compose.detail)"
    Write-Output "WSL integration: unknown - enable/check per-distro in Desktop, then run docker info in Ubuntu."
    Write-Output 'FLOP miner / FLOP miner: NOT_IMPLEMENTED - official operator assets required.'
    Write-Output 'This report does not establish FLOP model support, calibration, enrollment or accepted work.'
}
