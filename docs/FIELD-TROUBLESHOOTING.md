# 🧰 Field troubleshooting quick wins / Sahadan pratik çözümler

[🇹🇷 Kurulum](VERIFIED-DEVNET-SETUP.tr.md) · [🇬🇧 Setup](VERIFIED-DEVNET-SETUP.en.md)

| Symptom / Belirti | Evidence-based action / Sahada işe yarayan kontrol |
|---|---|
| `HTTP 429 auto_miner_cap_full` | Sponsor says uncalibrated queue full; respect `retryAfterSeconds`, preserve signer, do not rotate wallets to bypass limits. |
| `HTTP 429 daily_new_sponsorships` | Rolling 24-hour new-registration cap, not proof of local failure. Inspect `retryAfterSeconds`, avoid parallel/manual duplicate watchers. |
| `HTTP 502` faucet | Service error; don't reinstall Windows/NVIDIA or re-create wallet for this. |
| `API-WS ... 1006` | Unexpected WebSocket close. DNS and HTTP 101 only test handshake; use official CLI `network status` for actual RPC connectivity. `1000 Normal Closure` after a command is normally benign. |
| `Cannot find module '@polkadot/api'` | Package missing in local Node; prefer the reviewed official FLOP CLI Docker image rather than installing a separate SDK just for RPC tests. |
| `model show` unknown | CLI 0.1.220 uses `model get`, not `show`. Confirm with `model --help`. |
| `MODEL_VERIFICATION_FAILED` | Examine exact reason. FP16 `no measured root` is different from interrupted BF16 downloads. Do **not** bypass dm-verity verification. |
| `huggingface: terminated` | Check network, CLI logs, single fetch process and free disk/RAM. Large download via container can fail even when small `config.json` returns HTTP 200. |
| Multiple `model fetch` processes | Stop extra fetch containers safely, then use **one** BF16 fetch; do not remove existing model folders before inspection. |
| Empty model directory | Examine `docker ps`, `docker top`, host-mounted paths and CLI output. No file growth is not proof of download completion. |
| Healthy backend, no calibration | Confirm worker's signer, Ghost mailbox, model-gate, 8645 endpoint, HTTPS ad, verified job count and block span. |
| `answered task` >64, calibration null | Tasks *answered* are not necessarily *verified*. In field example 72 answers yielded 64 verified jobs and accepted calibration after 623 blocks. |
| `attested_gpu_inventory: []` after declare | User GPU declaration `flop.gpu-inventory.v1` is not automatically an attested hardware inventory. Verify transaction on explorer; avoid duplicate writes. |
| Cloudflare tunnel restarts | Quick Tunnel hostname may change; update local `SESSION_PUBLIC_HOST` (hostname only) and republish via worker restart after verifying service. |
| Laptop sleeps | Prevent Windows sleep and verify WSL/Docker start after host reboot. Never assume WSL systemd keeps running while Windows is asleep. |

## Safe one-command diagnostics / Güvenli tek komut tanılama

On a machine with a previously configured official miner runtime, from this repo:

```bash
bash scripts/miner-health.sh YOUR_MINER_SS58_ADDRESS
```

Reads container state, worker logs, tunnel status and on-chain miner status; **does not sign, stake, change passwords, expose secrets or execute sponsor requests**. It is not a guarantee that live paid jobs exist.
