"""Fixed official targets; every test avoids live network."""

import io
import json
import unittest
from unittest.mock import patch
from urllib.error import URLError

from scripts import network_check


class NetworkCheckTests(unittest.TestCase):
    def test_dry_run_never_contacts_network(self):
        with patch.object(network_check.request, "urlopen", side_effect=AssertionError("network")):
            report = network_check.check(dry_run=True)
        self.assertEqual([item["url"] for item in report["checks"]], list(network_check.URLS))
        self.assertTrue(all(item["status"] == "not checked" for item in report["checks"]))

    def test_get_only_fixed_https_urls_with_timeout(self):
        seen = []

        def fetch(req, timeout):
            seen.append((req.full_url, req.get_method(), timeout))
            result = io.BytesIO(b"ok")
            result.status = 200
            return result

        with patch.object(network_check.request, "urlopen", side_effect=fetch):
            report = network_check.check(timeout=2)
        self.assertEqual(seen, [(url, "GET", 2) for url in network_check.URLS])
        self.assertTrue(all(item["status"] == "reachable" for item in report["checks"]))

    def test_network_failure_does_not_expose_raw_exception(self):
        with patch.object(network_check.request, "urlopen", side_effect=URLError("SECRET/TOKEN")):
            report = network_check.check()
        self.assertTrue(all(item["status"] == "unknown" for item in report["checks"]))
        self.assertNotIn("SECRET/TOKEN", json.dumps(report))

    def test_cli_dry_run_json_has_no_live_network(self):
        with (patch.object(network_check.request, "urlopen", side_effect=AssertionError("network")),
              patch("builtins.print") as printing):
            self.assertEqual(network_check.main(["--json", "--dry-run"]), 0)
        self.assertEqual(json.loads(printing.call_args.args[0])["mode"], "dry-run")

    def test_turkish_human_output_is_offline_and_localized(self):
        with (patch.object(network_check.request, "urlopen", side_effect=AssertionError("network")),
              patch("builtins.print") as printing):
            self.assertEqual(network_check.main(["--lang", "tr", "--dry-run"]), 0)
        rendered = " ".join(str(arg) for call in printing.call_args_list for arg in call.args)
        self.assertIn("kontrol edilmedi", rendered)
        self.assertIn("kabul edilmiş işi kanıtlamaz", rendered)
        self.assertNotIn("not checked", rendered)


if __name__ == "__main__":
    unittest.main()
