#!/usr/bin/env bash
# Read-only checks; neither probes private endpoints nor changes the host.
set -u

check() { printf '%s: %s — %s\n' "$1" "$2" "$3"; }
if [[ -r /etc/os-release ]]; then
    # /etc/os-release is the OS-defined key/value file (no arbitrary user file is sourced).
    . /etc/os-release
    distro=${ID:-unknown}
    release=${VERSION_ID:-unknown}
else
    distro=unknown
    release=unknown
fi
kernel=$(cat /proc/sys/kernel/osrelease 2>/dev/null || true)
if [[ ${kernel,,} == *microsoft* ]] || { [[ -r /proc/version ]] && [[ $(cat /proc/version) == *Microsoft* ]]; }; then
    environment='WSL (version not independently verified; check wsl --list --verbose on Windows)'
    if [[ ${kernel,,} == *wsl2* ]]; then
        environment='WSL2 (guest kernel reports WSL2; verify distro version on Windows)'
    fi
else
    environment='native Linux (not WSL detected)'
fi
check 'Platform / Platform' 'info' "$environment; distribution: $distro $release"
if [[ $distro == ubuntu && $release == 24.04 ]]; then
    check 'Ubuntu 24.04' 'pass' 'Target OS detected; GPU and Docker still need separate checks.'
else
    check 'Ubuntu 24.04' 'unknown' 'This distribution/version is not the documented target; compatibility is unverified.'
fi
if command -v nvidia-smi >/dev/null 2>&1; then
    if gpu_rows=$(nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader,nounits 2>/dev/null) && [[ -n $gpu_rows ]]; then
        gpu_count=0
        while IFS= read -r row; do
            [[ -n $row ]] && ((gpu_count+=1))
        done <<< "$gpu_rows"
        check 'NVIDIA GPU visibility / GPU gorunurlugu' 'pass' "$gpu_count GPU row(s); no FLOP compatibility implied. Run scripts/gpu_detect.py for per-GPU details."
    else
        check 'NVIDIA GPU visibility / GPU gorunurlugu' 'unknown' 'nvidia-smi could not query GPU; verify host driver and WSL GPU support.'
    fi
else
    check 'NVIDIA GPU visibility / GPU gorunurlugu' 'unknown' 'nvidia-smi absent; GPU and driver status unknown.'
fi
if command -v docker >/dev/null 2>&1; then
    engine=$(docker info --format '{{.OSType}}' 2>/dev/null) || engine=''
    if [[ $engine == linux ]]; then
        check 'Docker daemon / Docker servisi' 'pass' 'Linux engine reachable (GPU passthrough not yet checked).'
    elif [[ -n $engine ]]; then
        check 'Docker daemon / Docker servisi' 'fail' 'Engine does not report Linux; select the Docker Linux engine.'
    else
        check 'Docker daemon / Docker servisi' 'fail' 'Docker daemon unavailable. WSL: enable per-distro Docker Desktop integration; native Ubuntu: check Docker daemon and NVIDIA Container Toolkit.'
    fi
    if docker compose version >/dev/null 2>&1; then
        check 'Compose' 'pass' 'Docker Compose plugin available.'
    else
        check 'Compose' 'fail' 'docker compose plugin unavailable; check Docker Desktop or Compose installation.'
    fi
else
    check 'Docker daemon / Docker servisi' 'fail' 'docker command unavailable; use Desktop with WSL integration or native Linux Docker.'
    check 'Compose' 'unknown' 'Docker CLI unavailable.'
fi
if command -v df >/dev/null 2>&1; then
    disk_table=$(df -Pk . 2>/dev/null) || disk_table=''
    disk_last=${disk_table##*$'\n'}
    read -r _disk_total _disk_size disk_used disk_available _disk_percent _disk_mount <<< "$disk_last"
    if [[ ${disk_available:-} =~ ^[0-9]+$ ]]; then
        check 'Disk / Disk' 'info' "${disk_available} KiB available on current filesystem; image/model requirements not established."
    else
        check 'Disk / Disk' 'unknown' 'Available disk space could not be read.'
    fi
else
    check 'Disk / Disk' 'unknown' 'df unavailable.'
fi
if command -v date >/dev/null 2>&1; then
    if timestamp=$(date -u '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null); then
        check 'Clock / Saat' 'info' "UTC $timestamp; timestamp alone cannot prove clock accuracy."
    else
        check 'Clock / Saat' 'unknown' 'Clock cannot be queried.'
    fi
else
    check 'Clock / Saat' 'unknown' 'date unavailable.'
fi
if command -v timedatectl >/dev/null 2>&1; then
    sync=$(timedatectl show -p NTPSynchronized --value 2>/dev/null) || sync=''
    case $sync in
        yes) check 'Clock sync / Saat esitleme' 'pass' 'System reports NTP synchronization (not independent proof of exact time).' ;;
        no) check 'Clock sync / Saat esitleme' 'unknown' 'System reports no NTP synchronization; check host clock/time service.' ;;
        *) check 'Clock sync / Saat esitleme' 'unknown' 'Synchronization sensor unavailable (common in WSL).' ;;
    esac
else
    check 'Clock sync / Saat esitleme' 'unknown' 'Synchronization sensor unavailable.'
fi
check 'FLOP runtime' 'NOT_IMPLEMENTED' 'official operator assets required; container access does not prove FLOP registration or accepted work.'
