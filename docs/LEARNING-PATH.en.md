# FLOP Devnet — Learning pathway (Miner + Validator)

[🇹🇷 Türkçe](LEARNING-PATH.tr.md) · [Interactive guide](../site/validator.html) · [Miner commands](VERIFIED-DEVNET-SETUP.en.md) · [Validator commands](VALIDATOR-SETUP.en.md)

> **Purpose:** Teach independent operators how to reason about each step, verify evidence and diagnose failure safely. This is education, not advertising, investment advice, official distribution or a reward promise.

## Learning progression

| Level | Learn | Completion criterion |
| --- | --- | --- |
| 0 | Devnet/Testnet, Miner vs Validator, on-chain status | Explain your intended role |
| 1 | WSL2, NVIDIA, Docker, resource monitoring | Independent host/container checks |
| 2 | SHA256, Cosign and genesis | Verify provenance and chain identity |
| 3 | Miner signer, model root, worker, calibration | Read registration and calibration on-chain |
| 4 | Validator preparation and identity | Preflight, backup and enrollment stages |
| 5 | Operations | Detect stale logs, RPC disruptions and storage problems |

## 1. Two distinct roles

A **Miner** performs registered-model GPU inference and supplies verifiable computational work. A **Validator** participates in blockchain / Data Availability infrastructure. Each role has independent identity, services, resource requirements and enrollment gates. Miner calibration does **not** authorize Validator activation. Devnet preparation does not imply Testnet preference or income.

## 2. Check the actual WSL2 host

```bash
cat /etc/os-release | grep PRETTY_NAME
uname -r
nvidia-smi
docker info --format '{{.OSType}}'
docker compose version
free -h
df -h /
```

**Why:** Docker CLI existence is not daemon access. Some WSL `nvidia-smi` fields may be unavailable. Windows sleep can suspend WSL workloads. Validate resources before starting services, rather than blindly rebuilding identities.

## 3. SHA256 vs Cosign vs genesis

**SHA256** checks downloaded bytes against an expected digest. The **expected digest must be sourced independently and authoritatively**. **Cosign** checks signed-image provenance, certificate identity and transparency evidence. Neither proves a machine is enrolled or authorized. **Genesis hash** identifies the chain: matching the wrong genesis can leave a node outside the intended Devnet.

```bash
sha256sum -c SHA256SUMS
node preflight.mjs
```

Preflight `verified` means preparatory validation, not a live Validator.

## 4. Miner checkpoints

1. **Keys:** Protect the private signer; share only public SS58 if appropriate. Read `registered:true` separately.
2. **Model:** Compare downloaded BF16 model root with registered root. Never bypass `MODEL_VERIFICATION_FAILED`.
3. **Backend:** Inspect model hash, precision and decode policy, not merely HTTP status.
4. **Worker:** Check signer, `model-gate OK`, session listener and endpoint advertisement.
5. **Calibration:** `answered task` logs and finalized `verifiedJobs` are different measures. An example host reached **130 GFLOP/s**, which is not a universal benchmark.
6. **Paid work:** GPU use, Ghost test tasks and calibration are **not** proof of a finalized paid receipt.

[Complete Miner command guide](VERIFIED-DEVNET-SETUP.en.md)

## 5. Validator checkpoints

1. Select a versioned package from **official FLOP docs**.
2. Verify the archive digest before extraction and the internal file manifest afterward.
3. Confirm the **live** Devnet genesis via preflight.
4. Verify exact digest-pinned node and DA image signatures with Cosign.
5. Use the package-specified Node and pnpm. Isolate runtimes rather than replacing the system Node used by other applications.
6. Run `pnpm onboard prepare` **only if no identity exists**. Preserve `account.json` and `.env`.
7. Distinguish SSH **public** from **private** host keys; keep encrypted backups on separate storage and test restoration.
8. Enrollment/application is not the same as `join`, funding or activation.

[Complete Validator command guide](VALIDATOR-SETUP.en.md)

## 6. Symptom → diagnosis → safe action

| Symptom | Likely layer | First safe check |
| --- | --- | --- |
| Sponsor HTTP 429 | Admission/capacity | Review specific error code and `retryAfterSeconds`; do not rotate identities to bypass limits |
| `MODEL_VERIFICATION_FAILED` | Model/precision/download | Inspect registered root, BF16 bytes, concurrency and CLI result |
| WebSocket 1006 | RPC network | Compare independent `network status` and timestamped worker logs |
| 60s RPC timeout | RPC delay/connectivity | Separate chain status from stale application logs before restarting |
| GitHub Release HTTP 504 | Download gateway | Use verified official distribution alternatives |
| Empty attested GPU inventory | Declaration vs attestation | Confirm on-chain declaration without assuming attestation |
| No SSH host public key | Host identity | Generate missing host ED25519 key; do not expose port 22 just to prepare |
| `onboard prepare` succeeded | Preparation only | Wait for authorized join/verify procedure before asserting active Validator |

## 7. Safety rules

Never publish private signers, mnemonics, `miner.json`, `account.json`, `.env`, SSH private keys, session keys, secrets or backup passwords. Even public logs may expose identities. Archive existence is **not** restoration verification. Never run `docker compose down -v` against a working miner.

## 8. How to use this project

Start with concepts, validate your own host, follow each **proof gate**, and troubleshoot at the layer that actually failed. Always re-check [official FLOP Miner](https://docs.flop.network/docs/run-miner) and [Validator docs](https://docs.flop.network/docs/run-validator) for current versions and access conditions.

Animations are illustrative; dated real host outcomes are clearly labeled **field examples**, not live telemetry or guarantees.
