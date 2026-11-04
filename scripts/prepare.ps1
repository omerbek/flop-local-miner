# Guidance only: no installers, downloads, elevation or system changes.
[CmdletBinding()]
param()

Write-Output 'Windows/WSL2 preparation | Windows/WSL2 hazirlik (read-only / salt okunur)'
Write-Output 'Windows 10 version 21H2 (build 19044) or newer, or Windows 11, is the supported starting point for WSL GPU diagnostics. Update older Windows first.'
Write-Output 'Windows 10 21H2+ veya Windows 11 ile baslayin. Eski Windows surumlerini once guncelleyin.'
Write-Output ''
& (Join-Path $PSScriptRoot 'diagnose.ps1')
Write-Output ''
Write-Output 'Official installation and configuration references / Resmi kurulum ve yapilandirma kaynaklari:'
Write-Output '1. Windows WSL prerequisites and installation (Ubuntu 24.04, WSL version 2): https://learn.microsoft.com/en-us/windows/wsl/install'
Write-Output '   If appropriate after reviewing prerequisites, Microsoft documents: wsl --install -d Ubuntu-24.04 (NOT run by this script).'
Write-Output '2. NVIDIA Windows driver: https://www.nvidia.com/Download/index.aspx'
Write-Output '   WSL GPU guide: https://docs.nvidia.com/cuda/wsl-user-guide/index.html'
Write-Output '   Install the Windows driver on the host; do NOT install a Linux NVIDIA display driver inside WSL.'
Write-Output '3. Docker Desktop for Windows: https://docs.docker.com/desktop/setup/install/windows-install/'
Write-Output '   WSL2 backend and per-distro Ubuntu integration: https://docs.docker.com/desktop/features/wsl/'
Write-Output '   Docker GPU requirements: https://docs.docker.com/desktop/features/gpu/'
Write-Output '4. In Ubuntu-24.04 verify docker info and docker compose version; run ./scripts/preflight.sh then ./scripts/gpu-container-test.sh --dry-run.'
Write-Output '   Only ./scripts/gpu-container-test.sh --run explicitly authorizes pulling/running the pinned diagnostic CUDA image.'
Write-Output 'No install/indirme, elevation/yetki yukseltme, secrets/gizli anahtarlar or miner launch is performed here.'
Write-Output 'FLOP runtime: NOT_IMPLEMENTED - official operator assets required.'
