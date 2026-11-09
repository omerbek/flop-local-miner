# FLOP Devnet Validator — Gerçek WSL2 hazırlık rehberi 🇹🇷

[**Animasyonlu adım adım rehber**](../site/validator.html) · [English](VALIDATOR-SETUP.en.md) · [GPU Miner rehberi](VERIFIED-DEVNET-SETUP.tr.md)

> **Durum: 9 Kasım 2026.** Bu belge, Windows + WSL2 Ubuntu 24.04.5 ortamında **gerçekten uygulanan Validator hazırlığını** anlatır. Paket, genesis, Docker imzaları, Node/pnpm, hesap ve yedekler doğrulandı. **Validator ağa katılmadı, aktif değil ve blok üretmiyor.** Kullanıcı FLOP Validator interest formunu (Self-hosted) gönderdiğini ve [network Issue #10](https://github.com/flop-labs/network/issues/10)'a yorum yaptığını bildirdi. FLOP Operations'ın erişim/aktivasyon yanıtı bekleniyor. Testnet'e otomatik kabul/ödül garantisi yok.

## 1. Miner'dan bağımsız kurulum

Gerçek sistem: aynı Windows bilgisayarında RTX 5090 Laptop GPU Miner **/opt/flop-miner** dizininde; Validator hazırlığı ayrı **/opt/flop-validator** dizininde. İki rolün cüzdanı, signer'ı, SSH host anahtarı ve kalıcı verileri birbirine karıştırılmamalı. Mevcut Miner'da 130 GFLOP/s SOFT kalibrasyon zincirde kabul edildi; bu yeni Validator'a bir yetki vermez.

WSL içinde gözlenen kaynaklar: Intel Core Ultra 9 290HX Plus (24 mantıksal CPU), 31 GiB ayrılmış RAM, 1 TB WSL ext4 dosya sistemi ve Windows disklerinde ilave alan. FLOP'un 4 TB NVMe / 32 GB RAM / dedicated çekirdek değerleri *planlama hedefleri*; gerçek katılım öncesi eşzamanlı Miner + Validator kaynak kapasitesini ve **Windows uyku/WSL kapanma riskini** değerlendir.

```bash
cat /etc/os-release | grep PRETTY_NAME
free -h
lsblk -o NAME,SIZE,TYPE,MOUNTPOINTS
df -h /
docker compose version
```

## 2. Sürüm sabitlenmiş resmî paketi doğrula

Kaynak: [FLOP Validator dokümanı](https://docs.flop.network/docs/run-validator) ve [UfukNode'un 8 Kasım 2026 tarihli rehberi](https://github.com/UfukNode/flop-validator-setup/blob/main/Turkce-Kurulum.md). Paket ve checksum URL'lerini daima güncel resmî kaynaklardan yeniden doğrula. Saha denemesinde kullanılan sürüm:

```bash
mkdir -p /opt/flop-validator && cd /opt/flop-validator
curl -fL -O https://explorer.devnet.flop.network/validator-downloads/validator-cs-be91fe83-0.3.0-devnet.1.tar.gz
echo 'bf98e281b7d3217fb52e9aeba75886d2165e66d32f0159dbc3f1f2e998e30ba7  validator-cs-be91fe83-0.3.0-devnet.1.tar.gz' | sha256sum -c -
```

**İlerleme şartı:** `OK` görmeden arşivi açma.

```bash
tar -xzf validator-cs-be91fe83-0.3.0-devnet.1.tar.gz
cd validator-cs-be91fe83
sha256sum -c SHA256SUMS
node preflight.mjs
```

**Saha sonucu:** 26/26 dosya `OK`; `validator preflight: verified`; genesis `0x99c172c095340ace980631f9123544c6bebd4839f3437e463533422d8be2d631`; son kesinleşmiş blok 3,277,782; 15 eş (anlık saha ölçümü, güncel değer değişir). `preflight` için Node.js mevcut sürümde çalışmış olsa da onboarding bağımlılıkları için Node 24 kuruldu.

## 3. Cosign ile Docker imzalarını kontrol et

GitHub Release'den Cosign ikili dosyası indirmeye çalışırken tekrarlı HTTP 504 alındı. **Çözüm:** Cosign 3.1.4'ü resmî Docker imajından çalıştırmak. Docker imajı kullanmak Cosign'in kendisine duyulan güveni ayrıca değerlendirme gereğini ortadan kaldırmaz; kullanılacak Cosign imajını da mümkünse digest'e sabitle.

```bash
docker run --rm ghcr.io/sigstore/cosign/cosign:v3.1.4 version

WF='https://github.com/flop-labs/flop-core/.github/workflows/build-services.yml@refs/heads/main'
for IMG in \
  'ghcr.io/flop-labs/flop-core/node-devnet@sha256:84498fd73db2464eb13088ab34d369ddf7cddd22a45c810d140c9ff8ec16c91d' \
  'ghcr.io/flop-labs/flop-core/da-validator@sha256:c6709bb5bba04978a7800daccd87bb2bf916edd34d7dbf09f84aba5be9aca949'
do
  docker run --rm ghcr.io/sigstore/cosign/cosign:v3.1.4 verify "$IMG" \
    --certificate-oidc-issuer 'https://token.actions.githubusercontent.com' \
    --certificate-identity "$WF" >/dev/null && echo "OK: ${IMG%%@*}" || { echo "FAILED: $IMG"; exit 1; }
done
```

**Saha sonucu:** iki imajda da `OK`. İmza/şeffaflık kaydı denetimleri geçti; imza kontrolü tek başına çalıştırma izni veya aktif validator anlamına gelmez. Başka bir güncel resmi paket farklı digest isteyebilir.

## 4. Node.js 24 ve pnpm'i Miner'ı bozmadan kullan

Sahada sistemde Node 18.19.1 vardı; `pnpm`/`corepack` bulunmuyordu. Node 24 ayrı dizine kuruldu; sistem `/usr/bin/node` değiştirilmedi.

```bash
export PATH="/opt/flop-validator/tools/node24/bin:$PATH"
cd /opt/flop-validator/validator-cs-be91fe83
node --version
node -p "require('./package.json').packageManager"
corepack --version
pnpm --version
export COREPACK_ENABLE_DOWNLOAD_PROMPT=0
pnpm install --frozen-lockfile --ignore-scripts
```

**Saha sonucu:** pnpm `12.14.0`, `install: Done`. Node24'ü ilk kez kuranlar resmi [Node.js dağıtım](https://nodejs.org/dist/) dosyasının SHA256 değerini doğrulamalı. `pnpm` sürümünü `package.json` ile eşleştir; rastgele en son sürüme geçme.

## 5. Validator hesabını oluştur (bir kez)

`pnpm onboard prepare` yeni `account.json` ve `.env` oluşturabilir; bunların içeriği **gizlidir**. Mevcut dosyaların üzerine kesinlikle yazma. Host adı başlangıçta `omer` iken, başvuru yapılmadan önce `omerbektas` olarak kalıcı şekilde değiştirildi ve Validator hesabı aynı kaldı.

```bash
cd /opt/flop-validator/validator-cs-be91fe83
export PATH="/opt/flop-validator/tools/node24/bin:$PATH"
umask 077
if [ -e account.json ] || [ -e .env ]; then
  echo 'Mevcut Validator hesabı korunuyor: onboard prepare yeniden çalıştırılmadı'
else
  pnpm onboard prepare
fi
stat -c '%a %n' account.json .env
```

Beklenen izinler `600`. Bu saha örneğinde Validator SS58 `5CScVJxv99DxKhWdUTdSW8JiYdxqiA3G5UCTRjg4HYc7pk1A`. Bu **başkasının kullanacağı bir cüzdan değil**, yalnızca halka açık başarılı hazırlık örneği.

## 6. WSL hostname ve SSH host anahtarı

WSL2 `/etc/hosts` dosyasını yeniden oluşturur. Kalıcı hostname için mevcut diğer ayarları koruyarak `/etc/wsl.conf` içindeki `[network] hostname=...` ayarını kullan. Sistemi sırf bunu kontrol etmek için `wsl --shutdown` ile kapatma; bu Miner'ı keser.

```bash
hostname
stat -c '%a %n' account.json .env
test -f /etc/ssh/ssh_host_ed25519_key.pub && \
  ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub
```

Sahada `omerbektas` hostname ve SSH ED25519 fingerprint `SHA256:DjcFtpXJYSIse6wP9QVowbnoXKJvYiZ66T0fOXTQkn0` görüldü. Host **public** key FLOP ile paylaşılabilir; `/etc/ssh/ssh_host_ed25519_key` **private** dosyası asla paylaşılmaz. SSH sunucusu açmak ve 22 portunu internete yayınlamak başvuru için gerekmez.

## 7. Kimlik yedekleri (şifreli)

WSL içindeki `account.json`, `.env` ve ED25519 host anahtarının güvenli yedeği alınmalı. Sahada iki farklı `.tar.gz` arşivi `age -p` ile şifrelenip Windows D: sürücüsüne kaydedildi. Şifreler sohbette veya GitHub'da tutulmadı.

```bash
# Sadece örnek: Önce kendi dosyalarınız ve dosya izinlerini doğrulayın
mkdir -p /root/flop-validator-backup && chmod 700 /root/flop-validator-backup
cd /opt/flop-validator/validator-cs-be91fe83
tar -czf /root/flop-validator-backup/validator-identity.tar.gz account.json .env
tar -czf /root/flop-validator-backup/ssh-identity.tar.gz -C /etc/ssh ssh_host_ed25519_key ssh_host_ed25519_key.pub
chmod 600 /root/flop-validator-backup/*.tar.gz

# Windows D: sürücüsü varsa; parolayı çevrimdışı saklayın
mkdir -p /mnt/d/FLOP-Validator-Backup
age -p -o /mnt/d/FLOP-Validator-Backup/validator-identity.tar.gz.age /root/flop-validator-backup/validator-identity.tar.gz
age -p -o /mnt/d/FLOP-Validator-Backup/ssh-identity.tar.gz.age /root/flop-validator-backup/ssh-identity.tar.gz
```

**Önemli:** `age` parolası güçlü olmalı; Windows'ta `777` görünen dosya izinleri nedeniyle şifresiz arşivleri oraya taşıma. **Geri yükleme testi henüz yapılmadı.** Şifresiz yerel arşivleri uzun süre tutma; şifreli yedeğin doğrulanmasını ayrıca planla. Sıkıştırılmış `.tar.gz` dosyasına `tar -r` ile dosya eklenmez.

## 8. Başvuru ve beklenen erişim

9 Kasım 2026 itibarıyla kullanıcı [Validator Interest Form](https://flop.finance/apply/validator)'da **Self-hosted validator server** seçtiğini ve [GitHub FLOP Network Issue #10](https://github.com/flop-labs/network/issues/10) altında yorum yaptığını bildirdi. Bu **onay veya ağa katılım değildir**. FLOP Operations'ın doğrudan iletişim, tek kullanımlık Tailscale erişimi, DA peer yapılandırması, fonlama ve aktivasyon talimatları vermesi bekleniyor; iletişim yöntemi ve süre garantisi yok.

**Onay gelmeden `pnpm onboard join` çalıştırma.** Erişim materyali gelirse kimlik ve dosyaların kaynağını bağımsız doğrula; SSH private key, validator private key, mnemonic veya age parolasını kimseye gönderme. Testnet kabulü ayrı ağ kurallarına bağlıdır.

## 9. Rehberin teknik sınırları

- Bu repo **resmî Validator paketini dağıtmaz**; yalnızca doğrulama komutları ve saha sürecini açıklar.
- Saha kanıtları kullanıcının terminal çıktılarından; CI gerçek ağ bağlantısını veya validator aktivasyonunu test etmez.
- Miner ve Validator aynı WSL2 üzerinde *hazırlanmış* olsa da Validator henüz gerçek DA/node yüküyle birlikte çalıştırılmadı; eşzamanlı performans **ölçülmedi**.
- Sürüm, güvenlik ve kabul koşulları değişebilir: [resmî rehber](https://docs.flop.network/docs/run-validator), [UfukNode](https://github.com/UfukNode/flop-validator-setup), [FLOP Network Issue #10](https://github.com/flop-labs/network/issues/10).
