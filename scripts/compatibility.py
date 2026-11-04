"""Conservative BF16 memory prefilter, never FLOP hardware/support certification.

Sources: https://docs.flop.network/docs/run-miner and
https://api.flop.network/v1/models (catalog omits checkpoint/policy/hardware gates).
"""

import json
import os
from http.client import HTTPException
from pathlib import Path
import tempfile
import time
from urllib import request


MODELS_URL = "https://api.flop.network/v1/models"
CACHE_TTL_SECONDS = 24 * 60 * 60
# Conservative nominal BF16 weights-only floors in MiB; not verified runtime VRAM minima.
# Documentation gives Qwen3.8-27B BF16 as approximately 55.6 GB of checkpoint bytes.
EXAMPLES = (
    ("Qwen/Qwen2.5-0.5B-Instruct", "qwen/qwen2.5-0.5b-instruct", 900),
    ("Qwen/Qwen3.8-27B", "qwen/qwen3.8-27b", 50 * 1024),
)
IDS = {example[1] for example in EXAMPLES}
CONDITIONS = ("BF16 weights-only prefilter; additional vLLM/KV-cache memory depends on context "
              "length and concurrency. FLOP requires the exact chain-registered checkpoint/revision "
              "and model root, allowlisted TOPLOC decode policy, actual GPU capture/throughput, "
              "operator pack, registration and calibration; no accepted work is proven.")


def _cache_path():
    base = os.environ.get("LOCALAPPDATA") if os.name == "nt" else None
    return (Path(base) if base else Path.home() / ".cache") / "flop-local-miner" / "models.json"


def _valid_ids(value):
    return isinstance(value, list) and all(isinstance(item, str) and item in IDS for item in value)


def _cached(path, now):
    try:
        cache = json.loads(path.read_text(encoding="utf-8"))
        timestamp = cache["fetched_at"]
        if (type(timestamp) in (int, float) and 0 <= now - timestamp < CACHE_TTL_SECONDS
                and _valid_ids(cache["model_ids"])):
            return set(cache["model_ids"])
    except (OSError, ValueError, KeyError, TypeError):
        pass
    return None


def _store(path, now, model_ids):
    """Only allowlisted identifiers and a time; never cache raw catalog/addresses."""
    temporary = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=".models-", delete=False) as stream:
            temporary = stream.name
            json.dump({"fetched_at": now, "model_ids": sorted(model_ids)}, stream)
        os.replace(temporary, path)
    except OSError:
        pass  # A read-only home directory does not prevent a successful HTTPS lookup.
    finally:
        if temporary:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
            except OSError:
                pass


def get_catalog(*, online=False, cache_path=None, now=None):
    """Return official catalog ID set, or None when offline/invalid/unavailable.

    No filesystem access or HTTP unless explicitly online. HTTPS, hardcoded endpoint,
    bounded size/timeout; cache is opt-in only, contains no server-supplied free text.
    """
    if not online:
        return None
    path = Path(cache_path) if cache_path is not None else _cache_path()
    current = time.time() if now is None else now
    hit = _cached(path, current)
    if hit is not None:
        return hit
    try:
        with request.urlopen(MODELS_URL, timeout=3) as response:
            content = response.read(1024 * 1024 + 1)
        if len(content) > 1024 * 1024:
            return None
        payload = json.loads(content)
        if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
            return None
        models = payload["data"]
        if any(not isinstance(model, dict) or not isinstance(model.get("id"), str)
               for model in models):
            return None
        # A model ID is an API listing, not proof of a hardware fit or registered model.
        ids = {model["id"] for model in models if model["id"] in IDS}
    except (OSError, HTTPException, ValueError, TypeError):
        return None
    _store(path, current, ids)
    return ids


def recommend(gpus, catalog=None):
    """Assess cards separately; 'supported' is reserved for proofs not available here."""
    recommendations = []
    for name, slug, lower_bound in EXAMPLES:
        known = [gpu.get("memory_free_mib") for gpu in gpus
                 if gpu.get("driver_version") and gpu.get("name")]
        known = [memory for memory in known if isinstance(memory, int) and memory >= 0]
        any_unknown = any(not isinstance(gpu.get("memory_free_mib"), int)
                          or not gpu.get("driver_version") or not gpu.get("name")
                          for gpu in gpus)
        if known and not any_unknown and max(known) < lower_bound:
            status = "insufficient memory"
            prefix = (f"Every detected GPU has less than {lower_bound} MiB free; even the "
                      "conservative nominal BF16 weights-only floor cannot fit on a single GPU. ")
        elif catalog is None:
            status = "unknown"
            prefix = "Official model catalog unavailable/offline; no live model availability checked. "
        elif slug not in catalog:
            status = "unknown"
            prefix = "Example not listed in the current official model catalog. "
        elif not known or any_unknown:
            status = "unknown"
            prefix = "GPU free memory or driver is unknown; no reliable memory prefilter. "
        elif max(known) < lower_bound:
            status = "insufficient memory"
            prefix = f"No individual GPU has {lower_bound} MiB free for nominal BF16 weights. "
        else:
            status = "possible but unverified"
            prefix = ("Official catalog lists this model and at least one GPU passes a conservative "
                      "nominal BF16 weights-only prefilter; this is not FLOP support. ")
        recommendations.append({"name": name, "status": status,
                                "reason": prefix + CONDITIONS + " Sources: "
                                "https://docs.flop.network/docs/run-miner ; " + MODELS_URL})
    return recommendations
