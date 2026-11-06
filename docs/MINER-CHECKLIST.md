# Miner evidence checklist / Miner kanıt kontrol listesi

Check boxes record **observed** outcomes, never implied progress. Kutular yalnızca **gözlenen** sonuçla işaretlenir. A code fixture, screenshot illustration or README claim does not count as a physical test. Kod testi, çizim veya README fiziksel test sayılmaz.

## Level 1 · Host and GPU / Host ve GPU

- [ ] Identify host OS/build, WSL2 distro/version or native Ubuntu 24.04 / Host sürümü ve WSL2/Ubuntu doğrulandı.
- [ ] Detect each NVIDIA GPU separately with `nvidia-smi`, note masked UUID, driver, free/total VRAM, optional compute capability and unsupported fields / Her GPU ayrı ve eksik alanlar `unknown`.
- [ ] Distinguish driver-advertised CUDA API max from any installed toolkit / CUDA API ve toolkit ayrıldı.
- [ ] If GPU absent/non-NVIDIA or WSL stopped, report `needs intervention`/`not verified for FLOP`, not ready / Donanım yoksa hazır denmez.

## Level 2 · Container / Konteyner

- [ ] Inspect pinned [CUDA image digest](RESEARCH.md) and run `bash scripts/gpu-container-test.sh --run` **only with consent** / İmaj incelenip açık onayla çalıştırıldı.
- [ ] Record actual GPU rows inside ephemeral container, driver/runtime fit, Docker Compose, disk and clock; do not infer model eligibility / Konteyner GPU kanıtı kaydedildi, model uyumu varsayılmadı.

## Level 3 · Official miner / Resmî miner

- [ ] Obtain approved operator bundle, matching accessible worker/backend image digests and verified network identity / Yetkili paket, sabit imaj, ağ kimliği.
- [ ] Keep each host's own signer, session/Ghost keys, state, endpoint and secrets off Git / Her hostun kimlikleri, state'i ve gizlileri ayrı.
- [ ] Verify registered model hash, exact checkpoint revision/root, allowlisted decode policy and measured actual bytes / Gerçek model hash'i, checkpoint ve policy doğrulandı.
- [ ] Prove actual GPU inference, TOPLOC, context/concurrency/KV budget, registered account and accepted current calibration / Inference, TOPLOC, kayıt ve kalibrasyon kanıtlandı.

## Level 4 · Accepted work / Kabul edilen iş

- [ ] Through least-privilege authenticated HTTPS (no raw public 8000/8645), prove DA delivery, gateway admission and a positive finalized paid-session receipt in an authorized window / HTTPS, DA, ağ kabulü ve kesinleşmiş iş makbuzu kanıtlandı.
- [ ] Never equate devnet nominal catalog prices or a local GPU benchmark with earnings / Devnet fiyat satırları veya benchmark gelir değildir.

**Evidence update, 6 Nov 2026:** This repository's own scripts remain diagnostics, but a separate **RTX 5090 Laptop Windows/WSL2 field run** validated miner registration, BF16 verified-root fetch, `model_identity:measured`, public session endpoint (401 when unauthenticated), 72 answered Ghost tasks and on-chain 64 verified calibration jobs / 130 GFLOP/s. **Paid work is not verified.** For reproducible steps see [TR](VERIFIED-DEVNET-SETUP.tr.md) or [EN](VERIFIED-DEVNET-SETUP.en.md). The unchecked boxes above are a reusable checklist **for each new user's computer**, not denial of this one field result.
