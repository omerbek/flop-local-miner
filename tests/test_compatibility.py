"""Model suggestions deliberately do not assert actual FLOP support."""

import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import compatibility


class CompatibilityTests(unittest.TestCase):
    @staticmethod
    def gpu(free):
        return {"name": "NVIDIA GPU", "driver_version": "550.30", "memory_free_mib": free}

    def test_offline_catalog_unknown_even_with_large_gpu(self):
        with patch.object(compatibility.request, "urlopen", side_effect=AssertionError("network")):
            self.assertIsNone(compatibility.get_catalog())
            recommendations = compatibility.recommend([self.gpu(100_000)])
        self.assertEqual([item["status"] for item in recommendations], ["unknown", "unknown"])
        self.assertTrue(all("TOPLOC" in item["reason"] and "KV-cache" in item["reason"]
                            and "revision" in item["reason"] for item in recommendations))

    def test_only_conservative_bf16_weight_floor_can_rule_out(self):
        recommendations = compatibility.recommend([self.gpu(128)], {"qwen/qwen2.5-0.5b-instruct"})
        self.assertEqual([item["status"] for item in recommendations],
                         ["insufficient memory", "insufficient memory"])
        low = compatibility.recommend([self.gpu(24_000)], {"qwen/qwen2.5-0.5b-instruct"})
        self.assertEqual(low[0]["status"], "possible but unverified")
        self.assertEqual(low[1]["status"], "insufficient memory")
        self.assertFalse(any(item["status"] == "supported" for item in low))

    def test_memory_not_pooled_across_multiple_cards(self):
        cards = [self.gpu(30_000), self.gpu(30_000)]
        recommendation = compatibility.recommend(cards, {"qwen/qwen3.8-27b"})[1]
        self.assertEqual(recommendation["status"], "insufficient memory")
        self.assertIn("single GPU", recommendation["reason"])
        cards.append(self.gpu(None))
        self.assertEqual(compatibility.recommend(cards, {"qwen/qwen3.8-27b"})[1]["status"],
                         "unknown")

    def test_catalog_is_only_allowlisted_ids_cache_and_ttl(self):
        payload = {"data": [{"id": "qwen/qwen2.5-0.5b-instruct",
                             "x-flop": {"price_sources": [{"miner_address": "SECRET-ADDRESS"}]}},
                            {"id": "unknown/private-secret-model"}]}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "model-cache.json"
            with patch.object(compatibility.request, "urlopen", return_value=io.BytesIO(json.dumps(payload).encode())) as fetch:
                ids = compatibility.get_catalog(online=True, cache_path=path, now=1_000_000)
                self.assertEqual(ids, {"qwen/qwen2.5-0.5b-instruct"})
                self.assertEqual(compatibility.get_catalog(online=True, cache_path=path, now=1_000_001), ids)
            fetch.assert_called_once()
            contents = path.read_text(encoding="utf-8")
            self.assertNotIn("SECRET-ADDRESS", contents)
            self.assertNotIn("unknown/private-secret-model", contents)
            with patch.object(compatibility.request, "urlopen", side_effect=OSError("offline")):
                self.assertIsNone(compatibility.get_catalog(online=True, cache_path=path,
                                                              now=1_000_000 + compatibility.CACHE_TTL_SECONDS))

    def test_invalid_api_payload_never_claims_model(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "model-cache.json"
            with patch.object(compatibility.request, "urlopen", return_value=io.BytesIO(b'{"data": "not a list"}')):
                self.assertIsNone(compatibility.get_catalog(online=True, cache_path=path))
            self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main()
