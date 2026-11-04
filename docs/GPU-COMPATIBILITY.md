# GPU compatibility / GPU uyumluluğu

[EN guide](README.en.md) · [TR rehber](README.tr.md) · [Official miner manual](https://docs.flop.network/docs/run-miner) · [Research](RESEARCH.md)

**EN:** The CLI discovers each GPU via `nvidia-smi --query-gpu ... --format=csv` and parses CSV rather than matching card names. GPU UUID, machine ID and IP are masked by default. Total/free VRAM, Windows/Linux driver, driver-advertised CUDA API maximum, optional compute capability, power and temperature can be missing (`unknown`); `nvidia-smi` CUDA Version is **not** the locally installed CUDA toolkit. A laptop GPU is not automatically equivalent to a desktop GPU with a similar name. A GPU detected on the host is only a candidate for an environment test. A multi-GPU list does not imply memory pooling or one miner serving across computers.

**TR:** CLI her GPU'yu adıyla sabitlemek yerine `nvidia-smi` CSV alanlarıyla ayrı ayrı keşfeder. GPU UUID, makine kimliği ve IP varsayılan olarak maskelenir. Toplam/boş VRAM, sürücü, sürücünün bildirdiği CUDA API üst sınırı, compute capability, güç ve sıcaklık alanları yoksa `unknown` kalır; `nvidia-smi` CUDA Version **kurulu toolkit sürümü değildir**. Laptop ve masaüstü kartları eşdeğer varsayılmaz. Hostta görünmek yalnızca ortam testine adaylık sağlar. Birden fazla GPU otomatik VRAM birleştirmez; farklı bilgisayarlar ayrı kimlikler kullanır.

Some laptop NVML drivers return an unsigned-32 sentinel rendered as `4294967.5 W` for an unsupported power limit; this is normalized to `null`, not a real wattage. / Bazı laptop sürücüleri desteklenmeyen güç sınırını `4294967.5 W` gibi bir değerle döndürür; gerçek ölçüm değil `null` olarak gösterilir.

| Hardware result / Donanım sonucu | Meaning / Anlamı |
| --- | --- |
| `ready for environment test` | Usable inventory found; Docker GPU **not** yet proved / Envanter var; Docker kanıtı yok |
| `needs intervention` | Driver/probe failure, missing prerequisites, or reported memory issue / Sürücü, sorgu veya önkoşul sorunu |
| `not verified for FLOP` | No eligible evidence, non-NVIDIA device, unverified context or partial device state / Kanıt eksikliği veya doğrulanmamış ortam |

Model API access is **opt-in** (`--online-models`) with a finite timeout and limited cache. [FLOP catalog](https://api.flop.network/v1/models) advertises model identifiers/context but no exact checkpoint root, revision, BF16 weight bytes, proof of chain policy or GPU requirements. The [release manifest](https://flop.network/releases.json) advertises some roots and decode-policy preimages but does not replace a finalized-chain allowlist check. Offline examples are **illustrative**: official docs describe Qwen2.5-0.5B-Instruct (A40 measured drill) and Qwen3.8-27B BF16 (much larger). An optimistic BF16 lower bound is parameter count × 2 bytes; it ignores overhead and is useful only to reject devices **below** that minimum, not to prove fit. Actual requirement includes checkpoint bytes, runtime/vLLM overhead, KV-cache at requested context length, concurrency, precision, TOPLOC capture, checkpoint revision/root and allowed decode policy. Quantized weights are never presumed supported.

| Recommendation / Öneri | Required evidence / Gerekli kanıt |
| --- | --- |
| `insufficient memory` | Conservative model-weight minimum already exceeds available memory, for the examined BF16 path / BF16 ağırlık alt sınırı belleği aşıyor |
| `possible but unverified` | Preliminary bound fits, **all** later checks outstanding / Ön filtre uyuyor; kalan kontroller bekliyor |
| `unknown` | Catalog/parameters/measurements missing or offline / Katalog/ölçüm yok |
| `supported` | Registered exact model/root/revision, chain-allowlisted policy, compatible GPU/backend, context/concurrency/KV budget, TOPLOC and actual admission all proven / Tüm koşullar kanıtlandı; **bu araç tek başına asla üretmez** |

No automatic card-name promise for RTX 3060, 4060 Ti, 4090, 5090, A40, A100 or H100. FLOP's published validated A40 drill is not a general certification. WSL2 can omit NVML telemetry. AMD/Intel/CPU-only can be diagnosed but their FLOP GPU runtime is not certified here. If the catalog cannot be reached, proceed with `unknown` and the documented offline examples; do not convert a failed fetch to model support.
