#!/usr/bin/env bash
# FLOP local miner: read-only operational snapshot.
# Requires a previously reviewed official runtime in /opt/flop-miner.
set -uo pipefail
BASE="${FLOP_HOME:-/opt/flop-miner}"
ADDRESS="${1:-}"
cd "$BASE" || { echo "Missing runtime directory: $BASE" >&2; exit 2; }
if [[ ! -f miner.env || ! -f docker-compose.yml ]]; then
  echo "Missing miner.env or docker-compose.yml. This is not an installer." >&2
  exit 2
fi
FLOP_CLI=$(sed -n 's/^FLOP_CLI=//p' miner.env | tail -1 | tr -d '\r')
if [[ -z "$FLOP_CLI" ]]; then echo "FLOP_CLI missing" >&2; exit 2; fi
if [[ -z "$ADDRESS" ]]; then
  if [[ -f miner.address ]]; then ADDRESS=$(head -1 miner.address | tr -d '\r'); fi
fi
if [[ ! "$ADDRESS" =~ ^[1-9A-HJ-NP-Za-km-z]{45,55}$ ]]; then
  echo "Usage: bash scripts/miner-health.sh YOUR_MINER_SS58_ADDRESS" >&2
  echo "No signer/seed is read." >&2
  exit 2
fi
printf '\n=== SERVICES / SERVISLER ===\n'
docker compose --env-file miner.env -f docker-compose.yml ps || true
printf '\n=== TUNNEL / TUNEL ===\n'
systemctl is-active flop-tunnel 2>/dev/null || echo 'Tunnel systemd status unavailable'
printf '\n=== GHOST TASK ANSWERS / GOREV YANITLARI (LOG COUNT) ===\n'
logs=$(docker compose --env-file miner.env -f docker-compose.yml logs --no-color worker 2>/dev/null || true)
printf '%s\n' "$logs" | grep -c '\[ghost\] answered task' || true
printf '\n=== RECENT WORKER EVENTS / SON OLAYLAR ===\n'
printf '%s\n' "$logs" | grep -Ei 'calibration|cap accepted|session.*(settled|completed)|payment|error|warn' | tail -12 || true
printf '\n=== ON-CHAIN MINER STATUS / ZINCIR DURUMU ===\n'
docker run --rm --network host "$FLOP_CLI" --network devnet \
 --rpc wss://rpc.devnet.flop.network miner status "$ADDRESS" --json
printf '\nRead-only snapshot complete. A Ghost answer does not prove paid work.\n'
