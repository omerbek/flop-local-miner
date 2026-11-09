# FLOP Devnet — Eğitim yol haritası (Miner + Validator)

[English](LEARNING-PATH.en.md) · [Etkileşimli adımlar](../site/validator.html) · [Miner komutları](VERIFIED-DEVNET-SETUP.tr.md) · [Validator komutları](VALIDATOR-SETUP.tr.md)

> **Amaç:** Okuyucu, başkasının hesabını veya makinesini kopyalamadan kendi ortamını anlayabilsin; kurulumdan önce kontrol, kurulumdan sonra kanıt ve sorun anında güvenli teşhis yapabilsin. Bu belge eğitim amaçlıdır; yatırım tavsiyesi, ödül garantisi veya resmî FLOP dağıtımı değildir.

## Öğrenme sırası

| Seviye | Öğreneceğin şey | Bir sonraki aşamaya geçme şartı |
| --- | --- | --- |
| 0 | Devnet, Testnet, Miner, Validator ve zincir kaydı farkı | Hangi rolü kurduğunu açıklayabilmek |
| 1 | Windows/WSL2, GPU ve Docker | Gerçek host ve konteyner testleri |
| 2 | Sürüm, SHA256, Cosign ve genesis kontrolü | Kaynak bütünlüğünü doğrulamak |
| 3 | Miner signer, model kökü, worker ve kalibrasyon | Zincirden kayıt/kalibrasyon okumak |
| 4 | Validator paket hazırlığı ve bağımsız kimlik | Preflight, yedek ve onay akışı |
| 5 | Sürekli işletim | Kesinti, log, anahtar ve yedek yönetimi |

## 1. Miner ve Validator aynı şey değildir

**Miner** GPU ile kayıtlı model üzerinde inference üretir ve ağın doğrulayabildiği hesaplama kanıtlarına katkıda bulunur. **Validator** ayrı bir blockchain/DA operatör rolüdür; GPU gerektirmeyebilir fakat güçlü CPU, RAM, hızlı ve yüksek kapasiteli depolama ile düşük gecikmeli ağ erişimi ister.

İki süreç ayrı cüzdan/kimlik, servis ve yaşam döngüsü kullanır. Bir Miner'ın kalibrasyonu Validator aktivasyonu sağlamaz. Devnet işlemleri gerçek ödül veya Testnet önceliğini kanıtlamaz.

## 2. WSL2 ortamında neyi test ediyoruz?

```bash
cat /etc/os-release | grep PRETTY_NAME
uname -r
nvidia-smi
docker info --format '{{.OSType}}'
docker compose version
free -h
df -h /
```

**Neden?** `docker --version` yalnızca istemcinin varlığını gösterir; Docker daemon erişimini göstermez. WSL içindeki `nvidia-smi` bazı GPU bellek/güç değerlerini eksik gösterebilir. Windows'un uyku modu WSL işlerini kesebilir.

**Başarı:** GPU görünür, Docker Linux daemon yanıtlar, ilgili volume'ler erişilebilir. **Başarısızsa:** Önce hangi katmanın eksik olduğuna bak; cüzdanı silme veya yeniden kurma.

## 3. SHA256 ile Cosign arasındaki fark

**SHA256**, indirilen arşivin beklenen dosyayla aynı olup olmadığını kontrol eder. Beklenen hash'in **güvenilir resmî kaynaktan** alınması gerekir. Aynı güvensiz sitedeki dosya ile hash'i eşleştirmek tek başına yayıncıyı doğrulamaz.

**Cosign**, konteyner imzası ve sertifika kimliği gibi yayınlama kanıtlarını kontrol eder. İmza olumlu olsa bile paket yapılandırması, sürüm uyumu ve çalıştırma yetkisi ayrı doğrulanır.

```bash
sha256sum -c SHA256SUMS
node preflight.mjs
```

**Genesis hash** ağın kimliğidir. Yanlış genesis üzerinden kurulu bir node, hedef Devnet'e değil başka bir zincire bağlanabilir. Preflight'ın **verified** demesi validator'ın ağa katıldığı anlamına gelmez.

## 4. Miner akışını nasıl okumalısın?

1. **Kimlik:** Özel signer anahtarı cihazda kalır; sadece açık SS58 adresini göster. `registered:true` kaydı ayrı kontrol edilir.
2. **Model:** Ağda kayıtlı model köküyle indirilen BF16 checkpoint kökü eşleşmeli. `MODEL_VERIFICATION_FAILED` hata olarak ele alınır; atlanmaz.
3. **Backend:** Sağlık sorgusunda doğru model hash, precision ve decode policy görülmeli. HTTP 200 sadece servis ayakta demek olabilir; veriyi kontrol et.
4. **Worker:** Worker'ın doğru signer ile `model-gate OK`, session listener ve endpoint advertisement üretmesini doğrula.
5. **Kalibrasyon:** `answered task` log sayısı, zincirdeki `verifiedJobs` ile aynı olmak zorunda değildir. Kesinleşmiş `calibration` kaydını sorgula. `130 GFLOP/s` yalnızca **örnek laptopun saha ölçümüdür**.
6. **Ödül:** Kalibrasyon, GPU kullanım yüzdesi veya test görevi **ücretli kabul makbuzu değildir**.

[Adım adım gerçek komutlar](VERIFIED-DEVNET-SETUP.tr.md)

## 5. Validator akışını nasıl okumalısın?

1. İmaj ve arşiv sürümlerini resmî belgelerden belirle.
2. Arşiv SHA256 kontrolünü **açmadan önce** yap; içindeki tüm dosyaları kontrol et.
3. Preflight'ta beklenen canlı genesis hash'ini doğrula.
4. Node ve DA imajlarının Cosign imzalarını **digest bazında** doğrula.
5. Paket `packageManager` değerine uygun Node.js/pnpm kullan. Mevcut miner için sistem Node sürümünü değiştirmek yerine ayrı `PATH` kullanabilirsin.
6. `pnpm onboard prepare` kimlik oluşturur. Var olan `account.json` ve `.env` üzerine yazma.
7. SSH **açık** anahtarını hazırla, özel anahtarı cihazdan paylaşma. Anahtarı ve validator kimliğini şifreli olarak farklı depolama alanına yedekle.
8. Başvuru/iletişim ayrı; `join` veya aktivasyon için uygun ağ erişimi olmadan işlem yapma.

[Validator komutlu rehberi](VALIDATOR-SETUP.tr.md)

## 6. Sorun giderme: Kanıta dayalı karar ağacı

| Belirti | Olası katman | Güvenli ilk adım |
| --- | --- | --- |
| `HTTP 429` sponsor | Sunucu kontenjanı / oran sınırı | Hata kodu ve `retryAfterSeconds` kaydet; yeni cüzdanlarla sınırı aşmaya çalışma |
| `MODEL_VERIFICATION_FAILED` | Model/precision/indirme | Kayıtlı kök, BF16, dosya boyutu ve tek indirme işlemini kontrol et |
| `1006 Abnormal Closure` | RPC WebSocket | Bağımsız CLI `network status` ve zaman damgalı son 5 dakika worker loglarını karşılaştır |
| `No response ... 60s` | RPC gecikmesi veya bağlantı | Tek hata ile bütün makineyi yeniden başlatma; servis ve zincir durumunu ayır |
| GitHub Release `504` | Dosya dağıtım ağ geçidi | Güvenilir bir alternatif yayın yöntemi kullan; Cosign resmî imajını doğrula |
| `attested_gpu_inventory: []` | Beyan / attestasyon ayrımı | GPU beyanı zincir işlemini kontrol et; zorunluluk kanıtlanmadan ikinci işlem gönderme |
| `ssh_host_ed25519_key.pub` yok | Host SSH kimliği eksik | ED25519 host anahtarını oluştur; SSH portunu açmak şart değil |
| Validator `prepare` başarılı | Sadece hazırlık | Onay ve gerçek `join/verify` olmadan aktif olduğunu iddia etme |

## 7. Güvenlik ve yayınlama ilkeleri

- **Asla paylaşma:** miner signer, mnemonic, `miner.json`, `account.json`, `.env`, SSH özel anahtarı, `session-keys`, yaş (age) parolaları, gizli tokenlar.
- **Yalnızca incelenmiş şekilde paylaş:** SS58 adresleri, SSH **public** anahtarları, kişisel tanımlayıcı içerebilen loglar.
- Şifreli yedek için dosyanın oluşturulması **geri yükleme kanıtı değildir**; kontrollü geri açma testi gerekir.
- Çalışan miner üzerinde `docker compose down -v` kullanma.
- Bu rehber, gerçek WSL2 üzerinde doğrulanmış sonuçları **örnek vaka** olarak sunar; okuyucunun kendi cihazında aynı sonucu garantilemez.

## 8. Eğitim kaynağını nasıl kullanmalı?

Önce terimleri öğren; sonra kendi cihazına uygun kontrolleri yap; her adımda **ölçülen kanıtı** kaydet; hatada ilgili katmana dön. Son olarak da [resmî FLOP Miner dokümanı](https://docs.flop.network/docs/run-miner) ve [resmî Validator dokümanı](https://docs.flop.network/docs/run-validator) ile güncel sürüm/katılım kurallarını kontrol et.

Rehberin animasyonları **temsili**, metrikleri ise yalnızca belirtildiği tarihte gözlenmiş **saha örnekleridir**. Canlı zincir veya GPU telemetrisi sağlamaz.
