# Troubleshooting / Sorun giderme

[English](README.en.md) · [Türkçe](README.tr.md) · [Evidence](RESEARCH.md)

| Symptom / Belirti | Next read-only check / Sonraki salt okunur kontrol | Fix to consider / Değerlendirilecek çözüm |
| --- | --- | --- |
| `nvidia-smi` missing on Windows / Windows'ta yok | `Get-Command nvidia-smi -ErrorAction SilentlyContinue`; Device Manager / Aygıt Yöneticisi | Inspect [official Windows NVIDIA driver](https://www.nvidia.com/Download/index.aspx). Do not install a Linux driver inside WSL. / WSL'e Linux ekran sürücüsü kurmayın. |
| WSL2 lists Ubuntu but fails to start; virtualization disabled / Sanallaştırma kapalı | `wsl --status`; `wsl --list --verbose` | Follow [Microsoft WSL prerequisites](https://learn.microsoft.com/en-us/windows/wsl/install); check firmware virtualization and Virtual Machine Platform by user choice. Do not delete existing distro. / Mevcut dağıtımı silmeyin. |
| `nvidia-smi` absent only inside WSL / Yalnız WSL içinde yok | `/usr/lib/wsl/lib/nvidia-smi`; `wsl --version` | Update Windows driver/WSL via official guidance. Some WSL NVML fields are unsupported; missing temperature is `unknown`, not failure. / Bazı sensörlerin eksikliği olağandır. |
| Docker CLI exists but daemon unavailable / CLI var daemon yok | `docker info`; Desktop Linux engine state | Start/inspect [Docker Desktop WSL2 backend](https://docs.docker.com/desktop/features/wsl/) and enable integration for selected distro; native Ubuntu uses its own Docker Engine. / Dağıtım entegrasyonunu kontrol edin. |
| `docker run --gpus all` cannot select device driver / GPU konteynere bağlanamıyor | `nvidia-smi`; `docker info`; pinned test `--dry-run` | For native Ubuntu check [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html); for WSL check [Docker GPU support](https://docs.docker.com/desktop/features/gpu.md). Verify driver versus image CUDA requirements; do not assume driver-API version equals toolkit. |
| Docker CUDA image cannot be pulled / İmaj indirilemiyor | `docker info`; registry access; compare [digest metadata](https://hub.docker.com/v2/repositories/nvidia/cuda/tags/12.6.3-base-ubuntu24.04) | Do not substitute `latest`, unreviewed digest or `curl | bash`; retry after network/registry diagnosis. / Rastgele imaj kullanmayın. |
| Model API offline, 403 or timeout / Katalog erişilemez | `python3 scripts/network_check.py --json` | Offline unknown is expected; catalog never proves FLOP onboarding. / Katalog destek kanıtı değildir. |
| `possible but unverified` with ample VRAM / Bellek yeterli görünüyor | Review [compatibility gates](GPU-COMPATIBILITY.md) | KV-cache/context/concurrency, checkpoint/revision, policy, TOPLOC and registration still unproved. / Diğer kontroller bekliyor. |
| `NOT_IMPLEMENTED: official operator assets required` | Read [official integration boundary](OFFICIAL-INTEGRATION.md) | This is intentional; request authorized pack from operator via current official channel, do not synthesize a worker or wallet. / Sahte miner başlatmayın. |

**Privacy / Gizlilik:** Do not paste raw logs, wallet material, personal hostnames or network addresses into public issues. `--json` masks default identifiers but review before sharing. Every host needs a separate eventual identity, state and endpoint.
