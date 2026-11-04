#!/usr/bin/env bash
# Docker-only CUDA visibility diagnostic; no miner, network or credentials.
set -u
readonly image='nvidia/cuda:12.6.3-base-ubuntu24.04@sha256:c87e78933f4c16e3272123bf2f75537306596d0fbaa395a29696a22786e5ee0e'
usage() {
    printf '%s\n' 'Usage: gpu-container-test.sh [--dry-run | --run]' \
        'Default --dry-run prints the pinned container command without pulling/running.' \
        '--run explicitly permits Docker to pull/cache the pinned image and start one ephemeral container; no host installer is run.'
}
case ${1:---dry-run} in
    --dry-run) [[ $# -eq 0 || $# -eq 1 ]] || { usage >&2; exit 2; }; run=0 ;;
    --run) [[ $# -eq 1 ]] || { usage >&2; exit 2; }; run=1 ;;
    --help|-h) usage; exit 0 ;;
    *) usage >&2; exit 2 ;;
esac
printf 'Image / Imaj: %s\n' "$image"
printf '%s\n' 'Checks NVIDIA visibility in a sandbox only; FLOP support, registration and network-accepted work remain unverified.'
printf '%s\n' 'Command / Komut: docker run --rm --gpus all --network none --read-only --cap-drop ALL --security-opt no-new-privileges --pids-limit 128 IMAGE nvidia-smi'
if [[ $run -eq 0 ]]; then
    printf '%s\n' 'DRY RUN: no image pulled, no container started. To authorize a pull and ephemeral run: ./scripts/gpu-container-test.sh --run'
    exit 0
fi
if ! command -v docker >/dev/null 2>&1; then
    printf '%s\n' 'Docker CLI unavailable. Install/configure Docker Desktop WSL integration or native Ubuntu Docker.' >&2
    exit 1
fi
engine=$(docker info --format '{{.OSType}}' 2>/dev/null) || engine=''
if [[ $engine != linux ]]; then
    printf '%s\n' 'Linux Docker engine unavailable. Start Docker daemon and select Linux containers; inside WSL enable per-distro integration.' >&2
    exit 1
fi
printf '%s\n' 'Running pinned CUDA visibility check; Docker may pull/cache the image. No miner is started.'
if docker run --rm --gpus all --network none --read-only --cap-drop ALL --security-opt no-new-privileges --pids-limit 128 "$image" nvidia-smi 2>/dev/null; then
    printf '%s\n' 'GPU visible in diagnostic container; FLOP environment/model support remains NOT VERIFIED.'
else
    printf '%s\n' 'GPU container check failed. Check host NVIDIA driver, Docker GPU support and (native Ubuntu) NVIDIA Container Toolkit or (WSL) Docker Desktop WSL integration.' >&2
    exit 1
fi
