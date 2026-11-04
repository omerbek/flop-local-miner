"""Read-only NVIDIA GPU inventory; never a FLOP miner or GPU qualification test."""

import argparse
import csv
import io
import json
import re
import subprocess
import sys

if __package__:
    from . import compatibility
else:  # `python scripts/gpu_detect.py` runs with scripts/ on sys.path.
    import compatibility


FIELDS = ("index", "name", "uuid", "memory.total", "memory.free", "driver_version",
          "temperature.gpu", "power.limit", "compute_cap")
QUERY_FORMAT = "--format=csv,noheader,nounits"
UNKNOWN = frozenset(("", "n/a", "[n/a]", "not supported", "not available", "unknown", "-"))
REPORT_FIELDS = ("index", "name", "uuid", "memory_total_mib", "memory_free_mib",
                 "driver_version", "cuda_driver_max", "temperature_c", "power_limit_w",
                 "compute_capability", "status", "reasons")


def _value(text):
    value = text.strip()
    return None if value.lower() in UNKNOWN else value


def _csv_rows(text, count):
    try:
        rows = list(csv.reader(io.StringIO(text, newline=""), strict=True))
    except csv.Error:
        return None
    if not rows or any(len(row) != count for row in rows):
        return None
    return [[_value(cell) for cell in row] for row in rows]


def _run(args):
    try:
        return subprocess.run(["nvidia-smi", *args], capture_output=True, text=True,
                              timeout=5, check=False)
    except (OSError, subprocess.TimeoutExpired, UnicodeError):
        return None


def _query(fields):
    result = _run(["--query-gpu=" + ",".join(fields), QUERY_FORMAT])
    if result is None or result.returncode != 0:
        return None
    return _csv_rows(result.stdout, len(fields))


def _number(text, cast):
    if text is None:
        return None
    try:
        number = cast(text)
        if number < 0 or number != number or number == float("inf"):
            return None
        return number
    except (ValueError, OverflowError):
        return None


def _safe_text(text, maximum=100):
    if (text is None or len(text) > maximum
            or not re.fullmatch(r"[\w .+()/:-]+", text, re.ASCII)
            or re.search(r"\b\d{1,3}(?:\.\d{1,3}){3}\b", text)):
        return None
    return text


def _cuda_driver_max():
    """nvidia-smi's CUDA Version is a driver API ceiling, NOT the installed toolkit."""
    result = _run([])
    if result is None or result.returncode != 0:
        return None
    match = re.search(r"\bCUDA Version:\s*(\d+\.\d+)\b", result.stdout)
    return match.group(1) if match else None


def _rows():
    """One combined query, then field-wise fallback for unsupported NVML fields."""
    combined = _query(FIELDS)
    if combined is not None:
        return [dict(zip(FIELDS, row)) for row in combined], None
    names = _query(("name",))
    if names is None:
        return [], "NVIDIA driver/GPU unavailable or nvidia-smi output could not be parsed"
    result = [{field: None for field in FIELDS} for _ in names]
    for record, row in zip(result, names):
        record["name"] = row[0]
    for field in FIELDS:
        if field == "name":
            continue
        values = _query((field,))
        if values is not None and len(values) == len(result):
            for record, row in zip(result, values):
                record[field] = row[0]
    return result, None


def _gpu(row, fallback_index, cuda_max):
    index = _number(row["index"], int)
    # A missing/malformed NVIDIA index is represented by its inventory position.
    index = fallback_index if index is None else index
    name = _safe_text(row["name"])
    driver = row["driver_version"]
    driver = driver if driver and re.fullmatch(r"\d+(?:\.\d+)+", driver) else None
    memory_total = _number(row["memory.total"], int)
    memory_free = _number(row["memory.free"], int)
    temperature = _number(row["temperature.gpu"], float)
    power = _number(row["power.limit"], float)
    # Some laptop drivers report the NVML unsigned-32 sentinel as ~4.29 million watts.
    if power is not None and power >= 4_000_000:
        power = None
    capability = row["compute_cap"]
    capability = capability if capability and re.fullmatch(r"\d+\.\d+", capability) else None
    reasons = []
    if not name or not driver:
        reasons.append("GPU name or NVIDIA driver version unavailable; inspect driver and nvidia-smi")
    if memory_total is None or memory_free is None:
        reasons.append("GPU memory metrics unavailable; model memory cannot be checked")
    if cuda_max is None:
        reasons.append("CUDA driver API maximum unavailable; installed CUDA toolkit not detected")
    if capability is None:
        reasons.append("Compute capability unavailable")
    return {"index": index, "name": name, "uuid": "[redacted]",
            "memory_total_mib": memory_total, "memory_free_mib": memory_free,
            "driver_version": driver, "cuda_driver_max": cuda_max,
            "temperature_c": temperature, "power_limit_w": power,
            "compute_capability": capability,
            "status": "ready for environment test" if name and driver else "not verified for FLOP",
            "reasons": reasons}


def detect(*, dry_run=False, online_models=False):
    """Return a redacted diagnostics report; dry-run never executes probes or HTTP."""
    rows, problem = ([], "Dry run: no hardware or network probes performed") if dry_run else _rows()
    cuda_max = _cuda_driver_max() if rows else None
    gpus = [_gpu(row, index, cuda_max) for index, row in enumerate(rows)]
    if dry_run:
        status = "not verified for FLOP"
    elif problem or not gpus:
        status = "needs intervention"
        problem = problem or "No NVIDIA GPU detected; CPU-only diagnostics cannot run FLOP inference"
    elif any(gpu["status"] != "ready for environment test" for gpu in gpus):
        status = "needs intervention"
        problem = "GPU name or NVIDIA driver version unavailable; inspect nvidia-smi and driver"
    else:
        status = "ready for environment test"
    catalog = compatibility.get_catalog(online=online_models and not dry_run)
    return {"schema_version": 1,
            "host": {"platform": sys.platform, "hostname": "[redacted]", "ip": "[redacted]"},
            "gpu_count": len(gpus), "gpus": gpus, "status": status,
            "official_runtime": {"status": "NOT_IMPLEMENTED", "reason": "official operator assets required"},
            "model_recommendations": compatibility.recommend(gpus, catalog),
            "reasons": [problem] if problem else ["GPU visibility does not prove Docker access, FLOP inference, calibration or accepted work"]}


TR_STATUS = {
    "ready for environment test": "ortam testi için hazır",
    "needs intervention": "müdahale gerekli",
    "not verified for FLOP": "FLOP için doğrulanmadı",
    "possible but unverified": "mümkün ancak doğrulanmadı",
    "insufficient memory": "bellek yetersiz",
    "unknown": "bilinmiyor",
    "supported": "destekleniyor (yalnızca kanıt varsa)",
}
TR_GPU_REASONS = {
    "GPU name or NVIDIA driver version unavailable; inspect driver and nvidia-smi":
        "GPU adı veya NVIDIA sürücü sürümü bilinmiyor; sürücüyü ve nvidia-smi çıktısını inceleyin",
    "GPU memory metrics unavailable; model memory cannot be checked":
        "GPU bellek bilgisi yok; model belleği değerlendirilemiyor",
    "CUDA driver API maximum unavailable; installed CUDA toolkit not detected":
        "CUDA sürücü API üst sınırı bilinmiyor; kurulu CUDA araç takımı ölçülmedi",
    "Compute capability unavailable": "İşlem yeteneği bilinmiyor",
}


def _render_tr(report):
    print("FLOP Local Miner — salt okunur GPU tanısı")
    print("Ortam:", TR_STATUS[report["status"]],
          "| Resmî çalışma zamanı: NOT_IMPLEMENTED (resmî operatör paketi gerekli)")
    print("Makine: [redacted]; GPU sayısı:", report["gpu_count"])
    for gpu in report["gpus"]:
        print("GPU", gpu["index"], gpu["name"] or "bilinmiyor", "UUID: [redacted]",
              "| boş / toplam MiB:", gpu["memory_free_mib"], "/", gpu["memory_total_mib"])
        print("  Sürücü:", gpu["driver_version"], "| CUDA sürücü API üst sınırı:",
              gpu["cuda_driver_max"], "(kurulu araç takımı sürümü değildir) |",
              TR_STATUS[gpu["status"]])
        for reason in gpu["reasons"]:
            print("  -", TR_GPU_REASONS.get(reason, "GPU alanı bilinmiyor"))
    for reason in report["reasons"]:
        if reason.startswith("Dry run:"):
            print("- Deneme modu: donanım veya ağ sorgusu yapılmadı")
        elif reason.startswith("NVIDIA driver/GPU"):
            print("- NVIDIA sürücüsü/GPU kullanılamıyor veya nvidia-smi çıktısı çözümlenemedi")
        elif reason.startswith("No NVIDIA GPU"):
            print("- NVIDIA GPU bulunamadı; yalnızca CPU tanısı FLOP çıkarımı sağlamaz")
        elif reason.startswith("GPU name"):
            print("- GPU adı veya NVIDIA sürücü sürümü bilinmiyor; sürücüyü ve nvidia-smi çıktısını inceleyin")
        else:
            print("- GPU görünürlüğü Docker erişimini, FLOP çıkarımını, kalibrasyonu veya kabul edilen işi kanıtlamaz")
    for model in report["model_recommendations"]:
        if model["status"] == "insufficient memory":
            detail = "Tek bir GPU'da BF16 ağırlıklarının yaklaşık alt sınırına bile yetecek boş bellek yok."
        elif model["status"] == "possible but unverified":
            detail = "Resmî katalogda listeleniyor; tek GPU BF16 ağırlık ön elemesini geçiyor; destek kanıtı değildir."
        else:
            detail = "Resmî katalog veya GPU bellek bilgisi doğrulanamadı; destek bilinmiyor."
        print("Model:", model["name"], "—", TR_STATUS[model["status"]], "—", detail)
        print("  vLLM/KV önbelleği, bağlam ve eşzamanlılık, kayıtlı checkpoint/revizyon, "
              "TOPLOC politikası ve model kökü, gerçek GPU testi, kayıt ve kalibrasyon ayrıca gerekir.")
    print("Sonraki adım: konteyner içinden GPU erişimini kontrol edin; resmî model ve ağda kabul edilen iş ayrı aşamalardır.")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read-only NVIDIA/FLOP environment diagnostics (not a miner)")
    parser.add_argument("--json", action="store_true", help="emit redacted JSON")
    parser.add_argument("--dry-run", action="store_true", help="skip GPU and network probes")
    parser.add_argument("--online-models", action="store_true", help="opt into official FLOP catalog HTTPS GET (3s timeout)")
    parser.add_argument("--lang", choices=("en", "tr"), default="en", help="human-readable report language (JSON keys unchanged)")
    args = parser.parse_args(argv)
    report = detect(dry_run=args.dry_run, online_models=args.online_models)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    elif args.lang == "tr":
        _render_tr(report)
    else:
        print("FLOP Local Miner — read-only GPU diagnostics")
        print("Environment:", report["status"], "| Official runtime: NOT_IMPLEMENTED (official operator assets required)")
        print("Host: [redacted]; GPU count:", report["gpu_count"])
        for gpu in report["gpus"]:
            print("GPU", gpu["index"], gpu["name"] or "unknown", "UUID: [redacted]",
                  "| free / total MiB:", gpu["memory_free_mib"], "/", gpu["memory_total_mib"])
            print("  Driver:", gpu["driver_version"], "| CUDA driver API max:", gpu["cuda_driver_max"],
                  "(not installed toolkit) |", gpu["status"])
            for reason in gpu["reasons"]:
                print("  -", reason)
        for reason in report["reasons"]:
            print("-", reason)
        for model in report["model_recommendations"]:
            print("Model:", model["name"], "—", model["status"], "—", model["reason"])
        print("Next: verify GPU access inside a container; official checkpoint, TOPLOC, registration, calibration and accepted work remain separate gates.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
