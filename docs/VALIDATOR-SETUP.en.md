# FLOP Devnet Validator — Verified WSL2 preparation (English)

[**Animated bilingual walkthrough**](../site/validator.html) · [Türkçe](VALIDATOR-SETUP.tr.md) · [GPU Miner field guide](VERIFIED-DEVNET-SETUP.en.md)

> **Field evidence, 9 Nov 2026:** Windows + WSL2 Ubuntu 24.04.5. The operator verified the versioned Validator package, all 26 checksums, live Devnet preflight, both Docker signatures, Node 24 / pnpm 12.14.0, an independent validator identity and encrypted backup. The operator reports submitting the **Self-hosted** interest form and posting in [network issue #10](https://github.com/flop-labs/network/issues/10). **No validator join, activation, blocks, stake funding or Testnet acceptance has been demonstrated.**

## 1. Separate roles on one WSL2 host

GPU Miner: `/opt/flop-miner`, RTX 5090 Laptop GPU, **130 GFLOP/s SOFT calibration** accepted on Devnet. Validator preparation: `/opt/flop-validator`, with separate account, files and host SSH key. Never reuse or overwrite the miner signer or account.

Observed host: Intel Core Ultra 9 290HX Plus (24 logical CPUs), 31 GiB WSL RAM, 1 TB WSL filesystem, additional Windows disk capacity. The 4 TB NVMe and 32 GB RAM numbers in validator guidance are planning targets. Concurrent full validator+miner resource use is **unverified**; Windows sleeping interrupts WSL.

```bash
cat /etc/os-release | grep PRETTY_NAME
free -h
lsblk -o NAME,SIZE,TYPE,MOUNTPOINTS
df -h /
docker compose version
```

## 2. Verify official Validator archive and chain identity

Cross-check release and hashes against the current [FLOP Validator manual](https://docs.flop.network/docs/run-validator). The field-verified version was `0.3.0-devnet.1`.

```bash
mkdir -p /opt/flop-validator && cd /opt/flop-validator
curl -fL -O https://explorer.devnet.flop.network/validator-downloads/validator-cs-be91fe83-0.3.0-devnet.1.tar.gz
echo 'bf98e281b7d3217fb52e9aeba75886d2165e66d32f0159dbc3f1f2e998e30ba7  validator-cs-be91fe83-0.3.0-devnet.1.tar.gz' | sha256sum -c -
```

**Do not extract unless the checksum says OK.**

```bash
tar -xzf validator-cs-be91fe83-0.3.0-devnet.1.tar.gz
cd validator-cs-be91fe83
sha256sum -c SHA256SUMS
node preflight.mjs
```

**Observed:** 26/26 file checksums OK; `validator preflight: verified`; genesis `0x99c172c095340ace980631f9123544c6bebd4839f3437e463533422d8be2d631`; finalized block 3,277,782 and 15 peers at observation time.

## 3. Verify the signed node/DA images with Cosign via Docker

Downloading the Cosign GitHub Release binary returned HTTP 504. Running Cosign from an official container avoided that path. Verify the Cosign image's provenance separately and preferably pin its digest.

```bash
docker run --rm ghcr.io/sigstore/cosign/cosign:v3.1.4 version
WF='https://github.com/flop-labs/flop-core/.github/workflows/build-services.yml@refs/heads/main'
for IMG in \
 'ghcr.io/flop-labs/flop-core/node-devnet@sha256:84498fd73db2464eb13088ab34d369ddf7cddd22a45c810d140c9ff8ec16c91d' \
 'ghcr.io/flop-labs/flop-core/da-validator@sha256:c6709bb5bba04978a7800daccd87bb2bf916edd34d7dbf09f84aba5be9aca949'
do
 docker run --rm ghcr.io/sigstore/cosign/cosign:v3.1.4 verify "$IMG" \
  --certificate-oidc-issuer 'https://token.actions.githubusercontent.com' \
  --certificate-identity "$WF" >/dev/null && echo "OK: ${IMG%%@*}" || { echo "FAILED: $IMG"; exit 1; }
done
```

**Observed:** 2/2 signed container images successfully verified. Verification is **not** permission to join a production/Devnet validator set.

## 4. Isolate Node.js 24 and pnpm

System Node was 18.19.1, pnpm and Corepack were absent. Install a verified official Node 24 archive into `/opt/flop-validator/tools/node24`, without replacing `/usr/bin/node`. Cross-check the `packageManager` version inside the verified package.

```bash
export PATH="/opt/flop-validator/tools/node24/bin:$PATH"
cd /opt/flop-validator/validator-cs-be91fe83
node --version
node -p "require('./package.json').packageManager"
corepack --version
pnpm --version
export COREPACK_ENABLE_DOWNLOAD_PROMPT=0
pnpm install --frozen-lockfile --ignore-scripts
```

**Observed:** pnpm 12.14.0, install `Done`.

## 5. Prepare identity — once

`pnpm onboard prepare` creates secret-bearing `account.json` and `.env`. Preserve an existing identity; do not rerun or overwrite a created one.

```bash
cd /opt/flop-validator/validator-cs-be91fe83
export PATH="/opt/flop-validator/tools/node24/bin:$PATH"
umask 077
if [ -e account.json ] || [ -e .env ]; then
 echo 'Existing Validator identity; prepare not repeated'
else
 pnpm onboard prepare
fi
stat -c '%a %n' account.json .env
```

**Observed:** 600 permissions; public validator address `5CScVJxv99DxKhWdUTdSW8JiYdxqiA3G5UCTRjg4HYc7pk1A`. Public addresses are examples, **not** a keystore to reuse.

## 6. WSL hostname and SSH host public key

The WSL hostname was changed from `omer` to `omerbektas` before submission. WSL auto-generates `/etc/hosts`; preserve existing settings when configuring `[network] hostname=...` in `/etc/wsl.conf`. Avoid `wsl --shutdown` while the GPU Miner is serving.

An ED25519 SSH **host key** was generated, and its public fingerprint checked. No publicly exposed SSH service/port 22 is required merely to prepare enrollment. Never share the host **private** key.

```bash
hostname
ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub
stat -c '%a %n' account.json .env
```

Observed host SSH fingerprint: `SHA256:DjcFtpXJYSIse6wP9QVowbnoXKJvYiZ66T0fOXTQkn0`.

## 7. Encrypted backup

The operator created two archives containing `account.json`, `.env` and the SSH host private/public keys, then encrypted them with `age -p` to a Windows D: path. The archives have **not** undergone a separate restore test.

```bash
mkdir -p /root/flop-validator-backup && chmod 700 /root/flop-validator-backup
cd /opt/flop-validator/validator-cs-be91fe83
tar -czf /root/flop-validator-backup/validator-identity.tar.gz account.json .env
tar -czf /root/flop-validator-backup/ssh-identity.tar.gz -C /etc/ssh ssh_host_ed25519_key ssh_host_ed25519_key.pub
chmod 600 /root/flop-validator-backup/*.tar.gz
mkdir -p /mnt/d/FLOP-Validator-Backup
age -p -o /mnt/d/FLOP-Validator-Backup/validator-identity.tar.gz.age /root/flop-validator-backup/validator-identity.tar.gz
age -p -o /mnt/d/FLOP-Validator-Backup/ssh-identity.tar.gz.age /root/flop-validator-backup/ssh-identity.tar.gz
```

Store the password safely offline. WSL mounts of Windows files may display permissive permissions; **never copy unencrypted archives there**. A compressed tar.gz cannot be appended to using `tar -r`. Test decryption/restoration before treating backup as complete.

## 8. Apply, but do not join early

The operator reports completing the [Validator Interest Form](https://flop.finance/apply/validator) with **Self-hosted validator server** and leaving a comment in [FLOP network Issue #10](https://github.com/flop-labs/network/issues/10). **Application ≠ approval**. The FLOP Operations team must provide verified contact and enrollment details, Tailscale access, DA peers, any required funding and activation.

Do **not** run `pnpm onboard join` until explicitly instructed and required access material is authenticated. No Devnet reward or automatic Testnet priority is guaranteed.

## 9. Limitations

- This repository documents the verified preparation, **not** a deployed or activated Validator; it redistributes no official Validator bundles.
- All field evidence is user-supplied, not independently tested by CI; the animated page is **not live telemetry**.
- Concurrent fully operating Validator+GPU Miner performance is unmeasured.
- Current rules and release material may change; see [official FLOP docs](https://docs.flop.network/docs/run-validator), [FLOP issue #10](https://github.com/flop-labs/network/issues/10).
