"""Opt-in, read-only reachability checks of fixed official FLOP HTTPS URLs."""

import argparse
import json
from http.client import HTTPException
from urllib import request
from urllib.error import HTTPError, URLError


URLS = (
    "https://docs.flop.network/operators",
    "https://docs.flop.network/docs/run-miner",
    "https://api.flop.network/v1/models",
    "https://flop.network/releases.json",
)


def check(*, dry_run=False, timeout=3):
    """Never contact untrusted user URLs; no POST, account, credential or miner calls."""
    results = []
    for url in URLS:
        if dry_run:
            status, note = "not checked", "dry run: no HTTP request sent"
        else:
            try:
                with request.urlopen(request.Request(url, method="GET"), timeout=timeout) as response:
                    status = "reachable" if 200 <= response.status < 300 else "unknown"
                    note = "HTTPS response received" if status == "reachable" else "unexpected HTTP status"
            except (HTTPError, URLError, HTTPException, OSError, TimeoutError, ValueError):
                status, note = "unknown", "HTTPS request failed or timed out"
        results.append({"url": url, "status": status, "note": note})
    return {"schema_version": 1, "mode": "dry-run" if dry_run else "read-only GET",
            "checks": results, "note": "Reachability is not GPU readiness, FLOP admission or accepted work"}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check fixed official FLOP HTTPS URLs; no account access")
    parser.add_argument("--dry-run", action="store_true", help="show targets without network requests")
    parser.add_argument("--json", action="store_true", help="emit JSON report")
    parser.add_argument("--lang", choices=("en", "tr"), default="en", help="human-readable report language (JSON keys unchanged)")
    args = parser.parse_args(argv)
    report = check(dry_run=args.dry_run)
    if args.json:
        print(json.dumps(report, indent=2))
    elif args.lang == "tr":
        print("Resmî FLOP URL erişimi (madenci kabulü değildir)")
        statuses = {"reachable": "erişilebilir", "unknown": "bilinmiyor", "not checked": "kontrol edilmedi"}
        notes = {"dry run: no HTTP request sent": "deneme modu: HTTP isteği gönderilmedi",
                 "HTTPS response received": "HTTPS yanıtı alındı",
                 "unexpected HTTP status": "beklenmeyen HTTP durumu",
                 "HTTPS request failed or timed out": "HTTPS isteği başarısız veya zaman aşımına uğradı"}
        for item in report["checks"]:
            print(statuses[item["status"]], item["url"], "—", notes[item["note"]])
        print("Erişilebilirlik GPU hazırlığını, FLOP kabulünü veya kabul edilmiş işi kanıtlamaz")
    else:
        print("Official FLOP URL reachability (not miner admission)")
        for item in report["checks"]:
            print(item["status"], item["url"], "—", item["note"])
        print(report["note"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
