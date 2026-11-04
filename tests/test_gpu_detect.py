"""Synthetic nvidia-smi fixtures only; no physical GPU or live network needed."""

import json
import subprocess
import unittest
from unittest.mock import patch

from scripts import gpu_detect


class GpuDetectorTests(unittest.TestCase):
    @staticmethod
    def smi(args, stdout="", returncode=0):
        return subprocess.CompletedProcess(args, returncode, stdout, "driver error: serial PRIVATE")

    def test_multi_gpu_redaction_and_driver_api_ceiling(self):
        rows = ('0, NVIDIA GeForce RTX 3060 Laptop GPU, GPU-PRIVATE-1, 6144, 5000, 528.49, 63, 115.00, 8.6\n'
                '1, NVIDIA RTX 4090, GPU-PRIVATE-2, 24564, 20000, 550.30, N/A, N/A, 8.9\n')

        def run(args):
            return self.smi(args, rows if args else "NVIDIA-SMI 550.30 CUDA Version: 12.6\n")

        with patch.object(gpu_detect, "_run", side_effect=run):
            report = gpu_detect.detect()
        self.assertEqual(report["gpu_count"], 2)
        self.assertEqual(report["status"], "ready for environment test")
        self.assertEqual(report["gpus"][0]["name"], "NVIDIA GeForce RTX 3060 Laptop GPU")
        self.assertEqual(report["gpus"][1]["name"], "NVIDIA RTX 4090")
        self.assertEqual(report["gpus"][0]["cuda_driver_max"], "12.6")
        self.assertIsNone(report["gpus"][1]["temperature_c"])
        self.assertEqual(report["host"]["hostname"], "[redacted]")
        self.assertNotIn("GPU-PRIVATE", json.dumps(report))
        self.assertNotIn("serial PRIVATE", json.dumps(report))
        self.assertEqual(report["official_runtime"]["status"], "NOT_IMPLEMENTED")
        self.assertEqual(set(gpu_detect.REPORT_FIELDS), set(report["gpus"][0]))

    def test_a40_sparse_unsupported_fields_fallback(self):
        def run(args):
            if not args:
                return self.smi(args, "CUDA Version: 12.4")
            fields = args[0].removeprefix("--query-gpu=")
            if "," in fields:
                return self.smi(args, returncode=2)
            values = {"name": "NVIDIA A40\n", "index": "0\n", "uuid": "SECRET\n",
                      "driver_version": "550.30\n", "memory.total": "N/A\n",
                      "memory.free": "Not Supported\n", "compute_cap": "N/A\n"}
            return self.smi(args, values.get(fields, "N/A\n"))

        with patch.object(gpu_detect, "_run", side_effect=run):
            report = gpu_detect.detect()
        self.assertEqual(report["gpu_count"], 1)
        gpu = report["gpus"][0]
        self.assertIsNone(gpu["memory_free_mib"])
        self.assertIsNone(gpu["compute_capability"])
        self.assertEqual(gpu["uuid"], "[redacted]")
        self.assertEqual(report["model_recommendations"][0]["status"], "unknown")

    def test_missing_nvidia_driver_and_no_gpu_not_claimed(self):
        with patch.object(gpu_detect, "_run", return_value=None):
            missing = gpu_detect.detect()
        self.assertEqual(missing["gpu_count"], 0)
        self.assertEqual(missing["status"], "needs intervention")
        with patch.object(gpu_detect, "_run", return_value=self.smi([], returncode=9)):
            no_gpu = gpu_detect.detect()
        self.assertEqual(no_gpu["gpu_count"], 0)
        self.assertEqual(no_gpu["status"], "needs intervention")
        partial = '0, NVIDIA A40, PRIVATE, 46068, 40000, N/A, 40, 200, 8.6\n'
        with patch.object(gpu_detect, "_run",
                          side_effect=lambda args: self.smi(args, partial if args else "")):
            unknown_driver = gpu_detect.detect()
        self.assertEqual(unknown_driver["gpu_count"], 1)
        self.assertEqual(unknown_driver["status"], "needs intervention")

    def test_malformed_csv_cannot_become_trusted_gpu(self):
        with patch.object(gpu_detect, "_run", return_value=self.smi([], '"NVIDIA A40, incomplete\n')):
            report = gpu_detect.detect()
        self.assertEqual(report["gpu_count"], 0)
        self.assertEqual(report["status"], "needs intervention")

    def test_dry_run_never_invokes_gpu_or_network(self):
        with (patch.object(gpu_detect, "_run", side_effect=AssertionError("GPU probe")),
              patch.object(gpu_detect.compatibility, "get_catalog", return_value=None) as catalog):
            report = gpu_detect.detect(dry_run=True, online_models=True)
        catalog.assert_called_once_with(online=False)
        self.assertEqual(report["status"], "not verified for FLOP")
        self.assertEqual(report["gpu_count"], 0)
        self.assertEqual(report["schema_version"], 1)

    def test_cli_json_redacts_host_and_identifiers(self):
        with (patch.object(gpu_detect, "detect", return_value={
                  "schema_version": 1, "host": {"platform": "win32", "hostname": "[redacted]", "ip": "[redacted]"},
                  "gpu_count": 0, "gpus": [], "status": "needs intervention",
                  "official_runtime": {"status": "NOT_IMPLEMENTED", "reason": "official operator assets required"},
                  "model_recommendations": [], "reasons": ["No NVIDIA GPU detected"]}) as detect,
              patch("builtins.print") as printing):
            self.assertEqual(gpu_detect.main(["--json", "--dry-run"]), 0)
        detect.assert_called_once_with(dry_run=True, online_models=False)
        self.assertEqual(json.loads(printing.call_args.args[0])["host"]["ip"], "[redacted]")

    def test_turkish_report_keeps_json_machine_status_untranslated(self):
        with (patch.object(gpu_detect, "_run", side_effect=AssertionError("GPU probe")),
              patch("builtins.print") as printing):
            gpu_detect.main(["--dry-run", "--lang", "tr"])
        printed = " ".join(str(argument) for call in printing.call_args_list for argument in call.args)
        self.assertIn("salt okunur GPU tanısı", printed)
        self.assertIn("resmî operatör paketi gerekli", printed)
        self.assertNotIn("ready for environment test", printed)

    def test_invalid_metrics_are_unknown_not_exceptions(self):
        rows = '0, NVIDIA RTX 4090, PRIVATE, -1, garbage, 550.30, Infinity, -1, bogus\n'
        with patch.object(gpu_detect, "_run", side_effect=lambda args: self.smi(args, rows if args else "")):
            report = gpu_detect.detect()
        gpu = report["gpus"][0]
        self.assertIsNone(gpu["memory_total_mib"])
        self.assertIsNone(gpu["memory_free_mib"])
        self.assertIsNone(gpu["temperature_c"])
        self.assertIsNone(gpu["power_limit_w"])
        self.assertIsNone(gpu["compute_capability"])

    def test_nvml_unsupported_power_limit_sentinel_is_unknown(self):
        rows = '0, NVIDIA GeForce RTX 3060 Laptop GPU, PRIVATE, 6144, 5000, 528.49, 50, 4294967.50, 8.6\n'
        with patch.object(gpu_detect, "_run", side_effect=lambda args: self.smi(args, rows if args else "")):
            gpu = gpu_detect.detect()["gpus"][0]
        self.assertIsNone(gpu["power_limit_w"])
        self.assertEqual(gpu["memory_total_mib"], 6144)


if __name__ == "__main__":
    unittest.main()
