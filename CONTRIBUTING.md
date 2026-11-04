# Contributing / Katkıda bulunma

**EN:** Open an issue for a proposed change, then a focused pull request. Keep `docs/README.en.md` and `docs/README.tr.md` technically equivalent; update the date/links in `docs/RESEARCH.md` when upstream conditions change. Add tests for parsing, boundaries, error handling and decision statuses. Do not include raw machine reports, tokens, keys, addresses, wallet files, model weights or unsupported hardware promises. Do not promote a candidate device to FLOP-supported without a verifiable authorized release, measured checkpoint/policy, calibration and accepted work evidence. Preserve distinct evidence levels. CI runs Python tests and Bash/PowerShell syntax checks; physical Docker GPU and FLOP acceptance require separately authorized, manually reported tests.

**TR:** Değişiklik için önce issue, sonra odaklı pull request açın. `docs/README.en.md` ve `docs/README.tr.md` dosyalarını teknik olarak eşdeğer tutun; resmî şartlar değişirse `docs/RESEARCH.md` kaynak tarihlerini güncelleyin. Ayrıştırma, sınırlar, hata işleme ve durum kararları için test ekleyin. Ham sistem raporu, token, anahtar, adres, cüzdan, model ağırlığı veya doğrulanmamış donanım uyumu yüklemeyin. Yetkili sürüm, ölçülmüş checkpoint/policy, kalibrasyon ve kabul edilen iş kanıtı olmadan cihazı FLOP destekli diye işaretlemeyin. Kanıt seviyelerini ayrı tutun. CI Python testlerini ve Bash/PowerShell sözdizimini çalıştırır; fiziksel GPU/Docker ve FLOP kabulü ayrı, yetkili manuel test gerektirir.

## Local checks / Yerel kontroller

```sh
python -m unittest discover -s tests -v
bash -n scripts/preflight.sh scripts/gpu-container-test.sh
python scripts/gpu_detect.py --json --dry-run
```

On Windows, check PowerShell syntax with the Windows CI job and inspect the read-only diagnostic before running it. On machines without Docker/GPU, do not mistake unit fixtures for physical test results.
