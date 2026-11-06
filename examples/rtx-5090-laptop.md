# Example: Windows RTX 5090 Laptop GPU / Örnek: Windows RTX 5090 Laptop GPU

**Updated with real user-provided evidence (6 Nov 2026) / Gerçek saha kanıtıyla güncellendi:** Earlier diagnostics used a *different* RTX 3060 Laptop. A later Windows/WSL2 host with **RTX 5090 Laptop GPU, 24,463 MiB** completed FLOP sponsored miner registration, BF16 model fetch/health, worker endpoint and **64 verified jobs / 623 blocks / 130 GFLOP/s SOFT calibration** on-chain. See [TR field guide](../docs/VERIFIED-DEVNET-SETUP.tr.md) / [EN field guide](../docs/VERIFIED-DEVNET-SETUP.en.md). These data come from user-provided terminal outputs, not a test run by repository CI. No paid session receipt was shown.

1. **Windows host / Windows host:** from repository root in PowerShell, review the scripts then run:

   ```powershell
   nvidia-smi
   wsl --status
   wsl --list --verbose
   docker --version
   powershell -NoProfile -File .\scripts\diagnose.ps1
   powershell -NoProfile -File .\scripts\prepare.ps1
   py -3 scripts\gpu_detect.py --json
   ```

   **Pass / Başarı:** card appears with its **measured** name, driver, free/total VRAM; Ubuntu WSL2 is version 2; optional Docker CLI present. **Fail / Hata:** no card → [NVIDIA driver](https://www.nvidia.com/Download/index.aspx); WSL2 cannot start → [Microsoft WSL prerequisites](https://learn.microsoft.com/en-us/windows/wsl/install). Do not write a fabricated 5090 value into any report. / Rapora uydurma 5090 verisi yazmayın.

2. **Only if Ubuntu 24.04 missing / Yalnız Ubuntu 24.04 eksikse:** after reviewing impact and granting consent, run `wsl --install -d Ubuntu-24.04`; validate `wsl --list --verbose`. **Pass / Başarı:** `VERSION 2`. **Fail / Hata:** virtualization unavailable → follow Microsoft prerequisites; do not delete an existing distro. No installer runs automatically. / Otomatik kurulum yoktur.

3. **Docker Desktop WSL integration / Docker entegrasyonu:** choose the Linux/WSL2 engine and enable the selected Ubuntu distro at **Settings → Resources → WSL Integration**. Inside Ubuntu at the repository folder:

   ```sh
   nvidia-smi || /usr/lib/wsl/lib/nvidia-smi
   bash scripts/preflight.sh
   python3 scripts/gpu_detect.py --json
   docker info
   docker compose version
   ```

   **Pass / Başarı:** host and WSL see real GPU; Docker server is reachable. **Fail / Hata:** daemon unavailable → [Docker WSL integration](https://docs.docker.com/desktop/features/wsl/). Install Windows NVIDIA driver only, never a Linux display driver in WSL. / WSL içine Linux ekran sürücüsü kurmayın.

4. **Optional digest-pinned physical test / İsteğe bağlı fiziksel test:** inspect [image provenance](../docs/RESEARCH.md), then:

   ```sh
   bash scripts/gpu-container-test.sh --dry-run
   bash scripts/gpu-container-test.sh --run
   ```

   **Pass / Başarı:** container `nvidia-smi` prints *measured* device rows. **Fail / Hata:** Docker GPU reservation error → verify Desktop WSL2 backend, driver and integration. This proves only container access. / Yalnız konteyner erişimi kanıtlanır.

5. **Official runtime required / Resmî miner ortamı gerekli:** consult [compatibility](../docs/GPU-COMPATIBILITY.md) and [official integration prerequisites](../docs/OFFICIAL-INTEGRATION.md). Model fit depends on actual available VRAM, checkpoint, runtime/KV-cache/context, registered decode policy, TOPLOC and accepted calibration; FLOP admission/work require operator approval and separate proof. / Gerçek miner kabulü için operatör izni ve ayrı kanıt gerekir.


## Verified field snapshot / Doğrulanmış saha sonucu

| Evidence | Value |
|---|---|
| Miner | [5H46Mswb…NaDezd](https://explorer.devnet.flop.network/account/5H46MswbTSXsej7cQgBmmwHfNNrLDs2c8no4MezvK4NaDezd) |
| GPU | NVIDIA GeForce RTX 5090 Laptop GPU, 24,463 MiB |
| Registered/staked | `registered:true`, `delegated:1000000`, active |
| BF16 model | Qwen/Qwen2.5-0.5B-Instruct, verified root 1a52c1…ba63306 |
| Calibration | SOFT, 130 GFLOP/s, 64 verified jobs, 623 blocks, accepted at 3021110 |
| GPU declared | [Transaction](https://explorer.devnet.flop.network/transactions/0x970f88289f3beaac756f8ec416cf9f120bebaebbc143c66f24f497eaecf0b753) |
| Attested inventory | Empty in subsequent `miner status`; a declaration is not hardware attestation |
| Paid work | No verified paid-session receipts |
