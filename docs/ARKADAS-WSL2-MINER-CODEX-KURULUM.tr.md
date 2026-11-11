# FLOP Devnet GPU Miner + Codex — İkinci Windows/WSL2 Bilgisayar Kurulum Rehberi

**Tarih:** 11 Kasım 2026  
**Hedef:** Windows 10/11, WSL2 Ubuntu 24.04, NVIDIA RTX 5090 Laptop GPU (veya uygun başka NVIDIA GPU), bağımsız FLOP Miner ve WSL içinde Codex.  
**Kurulum yaklaşımı:** Resmî FLOP miner paketini temel al; her cihaz için farklı cüzdan, signer, enclave seed ve session token kullan. Mevcut birinci Miner'ın kimliğini veya Docker volume'lerini **kopyalama**.

> **Devnet uyarısı:** Devnet test ağıdır; token ve işlem ücretleri gerçek para geliri değildir. Resmî FLOP sürümleri sık değişiyor. Bu rehberdeki sürüm/digest örnekleri 11 Kasım 2026 saha gözlemleridir, otomatik olarak güncel veya resmen onaylı kabul edilmez. Nihai sürümü resmî paket README'si ve `https://flop.network/releases.json` ile doğrula. Aynı GPU modeli aynı kalibrasyonu garanti etmez.
>
> **Önemli mimari ayrım:** Codex CLI, terminalde çalışan bir yazılım ajanıdır; `codex` komutu kendi başına 7/24 izleme servisi değildir. Sağlık takibi için ayrıca bağımsız bir systemd timer/monitor kurulur. Codex dosyaları inceler ve önerilen bakım/iyileştirmeleri yürütür; açık oturum ve signer güvenliğini gözetir.

---

## 0 — Hazırlık ve kontrol listesi

Her adımda **Windows PowerShell** veya **WSL Ubuntu** etiketi var. Kod bloklarını yalnızca belirtilen ortamda çalıştır.

- Windows bilgisayarda güncel NVIDIA **Windows** GPU sürücüsü yüklü olmalı. NVIDIA CUDA WSL rehberi: https://docs.nvidia.com/cuda/wsl-user-guide/
- En az 80–120 GB boş disk hedefle (GPU model imajları, Docker ve yedekler için); gerçek gereksinim artabilir.
- Sürekli çalışacaksa Windows uyku/hibernation ayarını kapat ve dizüstü bilgisayarın soğutmasını takip et.
- Her iki Miner için **farklı signer, farklı keystore, farklı enclave seed** şarttır. Arkadaşın kendi ChatGPT hesabıyla Codex'e giriş yapmalıdır.
- Cihazı fiziksel olarak kontrol edebilen kullanıcı hesap/keystore dosyalarını güvenli şekilde yerel olarak yedeklemeli. **Asla GitHub'a veya sohbete yüklememeli.**

### 0.1 — Windows PowerShell (Yönetici) — Windows, WSL ve GPU

```powershell
nvidia-smi
wsl --version
wsl --update
wsl --list --verbose
```

WSL kurulu değilse **yalnızca o durumda**:

```powershell
wsl --install -d Ubuntu-24.04
```

Gerekirse Windows'u yeniden başlat, Ubuntu ilk açılışında yeni bir Linux kullanıcı adı ve parola oluştur. `wsl --list --verbose` çıktısında Ubuntu sürümü **2** olmalı. WSL sürümü 1 ise doğru dağıtım adıyla dönüştür:

```powershell
wsl --set-version Ubuntu-24.04 2
```

### 0.2 — Windows PowerShell (Yönetici) — WSL kaynakları (isteğe bağlı)

Özellikle 64 GB fiziksel RAM'i olan bilgisayarda WSL bellek üst sınırı 32–40 GB seçilebilir. Windows tarafında kullanıcı profilindeki `.wslconfig` dosyasını aç:

```powershell
notepad "$env:USERPROFILE\.wslconfig"
```

Örnek içerik (**kendi RAM durumuna göre düzenle**):

```ini
[wsl2]
memory=36GB
processors=12
swap=8GB
```

Uygulamak için **Windows PowerShell**:

```powershell
wsl --shutdown
wsl -d Ubuntu-24.04
```

> `wsl --shutdown` bütün WSL dağıtımlarını kapatır. Sadece bu yeni bilgisayarda ve henüz Miner çalışmıyorken yap.

---

## 1 — WSL Ubuntu — temel paketler ve sistemd

Ubuntu terminalini aç, **normal Linux kullanıcısıyla** başla. `sudo` gereken komutların önünde belirtilmiştir.

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y ca-certificates curl wget git jq unzip tar openssl python3 python3-venv python3-pip gnupg lsb-release coreutils
uname -a
cat /etc/os-release
free -h
df -h ~
```

GPU'yu WSL içinde kontrol et:

```bash
/usr/lib/wsl/lib/nvidia-smi || nvidia-smi
```

**WSL Ubuntu içine NVIDIA Linux display driver kurma:** `nvidia-driver-*`, `nvidia-open`, `cuda-drivers` kurmak Windows'un WSL GPU köprüsünü bozabilir.

Systemd durumunu kontrol et:

```bash
ps -p 1 -o comm=
```

`systemd` değilse `/etc/wsl.conf` içine ekle veya mevcut dosyayla birleştir:

```bash
sudo nano /etc/wsl.conf
```

```ini
[boot]
systemd=true
```

Ardından **Windows PowerShell**'de:

```powershell
wsl --shutdown
wsl -d Ubuntu-24.04
```

Tekrar WSL'de:

```bash
ps -p 1 -o comm=
```

---

## 2 — WSL Ubuntu — Docker Engine + NVIDIA Container Toolkit

> Bu rehber **WSL içindeki Docker Engine** yaklaşımını kullanır. Arkadaşının bilgisayarında Docker Desktop WSL entegrasyonu kuruluysa ikinci Docker daemon kurup çakıştırma. Önce `docker info` ve `docker context ls` ile mevcut kurulumu kontrol et; Desktop mevcutsa resmî Desktop WSL entegrasyonunu kullan, aşağıdaki Linux Docker Engine kurulumunu atla.

### 2.1 — Docker mevcut mu?

```bash
command -v docker || true
docker context ls 2>/dev/null || true
docker info 2>/dev/null | head -25 || true
```

Docker yoksa **WSL Ubuntu**:

```bash
sudo apt remove -y docker.io docker-doc docker-compose docker-compose-v2 podman-docker containerd runc 2>/dev/null || true
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
. /etc/os-release
printf 'Types: deb\nURIs: https://download.docker.com/linux/ubuntu\nSuites: %s\nComponents: stable\nSigned-By: /etc/apt/keyrings/docker.asc\n' "$VERSION_CODENAME" | sudo tee /etc/apt/sources.list.d/docker.sources >/dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl enable --now docker
sudo docker version
sudo docker compose version
```

### 2.2 — NVIDIA Container Toolkit (Linux Docker Engine kullanıyorsan)

Kaynak: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html

```bash
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -fsSL https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list >/dev/null
sudo apt update
sudo apt install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

GPU'yu Docker içinde doğrula:

```bash
sudo docker run --rm --gpus all nvidia/cuda:12.8.0-base-ubuntu24.04 nvidia-smi
```

> Bu örnek CUDA imajının etiketi değişmişse NVIDIA'nın güncel ve GPU'ya uyumlu resmî base imajını kullan. Bu adım çalışmadan Miner backend'i başlatma. Docker Desktop kullanıyorsan `sudo nvidia-ctk` adımını Desktop daemon'una körlemesine uygulama.

### 2.3 — Çalışma klasörünü oluştur

```bash
sudo install -d -m 700 /opt/flop-miner
sudo chown "$(id -u):$(id -g)" /opt/flop-miner
cd /opt/flop-miner
umask 077
```

> Örneklerde doğrudan `docker` kullanılır. Normal kullanıcı için `docker` yetkisi yoksa komutları `sudo docker` ile çalıştır veya (Docker yetkisi root eşdeğeridir) yönetici onayıyla kullanıcıyı docker grubuna ekle. **Yalnızca yetkili kullanıcıya** Docker erişimi ver.

---

## 3 — WSL Ubuntu — resmî FLOP paketini indir ve checksum doğrula

**Resmî doküman:** https://docs.flop.network/docs/run-miner  
**Resmî paket dizini (11 Kasım 2026 örneği):** https://flop.network/releases/cli/miner-pack-devnet-ts-20261106/

```bash
cd /opt/flop-miner
BASE=https://flop.network/releases/cli/miner-pack-devnet-ts-20261106
curl -fL --retry 3 -o flop-miner-pack-devnet-ts-20261106.tar.gz "$BASE/flop-miner-pack-devnet-ts-20261106.tar.gz"
curl -fL --retry 3 -o OFFICIAL-PACK-README.md "$BASE/README.md"
echo '35f222f748447a8aabdd015d94260d8facfd29305691c3cf7ed033cbb2b514b1  flop-miner-pack-devnet-ts-20261106.tar.gz' | sha256sum -c -
```

**Checksum `OK` değilse devam etme.** Resmî doküman güncellenmişse yeni paketi ve onun resmî checksum değerini kullan.

Arşiv içeriğini listele, beklenmeyen yol/tür olmadığını incele:

```bash
tar -tzf flop-miner-pack-devnet-ts-20261106.tar.gz | head -70
```

Arşivden dosyaları temiz bir alt klasöre çıkar:

```bash
mkdir -p official-pack
tar -xzf flop-miner-pack-devnet-ts-20261106.tar.gz -C official-pack
find official-pack -maxdepth 3 -type f | sort | head -100
```

> **Önemli:** Resmî arşivin klasör hiyerarşisini ve betik adlarını burada tahmin etmiyoruz. `OFFICIAL-PACK-README.md` ile indirilen dosyaların gerçek adımlarını karşılaştır. `./sponsor.sh`, `./decode-policy.sh` ve miner hesabı hazırlama komutlarını **resmî paketin kendi README'sindeki sırayla** çalıştır. Resmî paket yoluyla üretilen `miner.env` / `docker-compose.yml` bizim çalışma dizinimizde bulunacak şekilde kurulum yap. Eğer paket artık farklı bir yapıya sahipse Codex'e yeni yapılandırmayı incelet; eski dosyaların üzerine körlemesine yazma.

Resmî yönergede ilk hesap oluşturma, sponsor, model identity/decode policy ve Compose aşamaları vardır. İleride çalışacak kontrol komutları için önce bunları tamamlamak gerekir.

---

## 4 — WSL Ubuntu — ayrı Miner kimliği, sponsor ve doğru CLI

**BİRİNCİ BİLGİSAYARIN signer/keystore/seed veya miner.env dosyasını kopyalama.** İkinci cihaz için ayrı hesabı **resmî paketin README komutuyla** oluştur. Oluşan adresi güvenle not et; özel anahtarı gösterme.

Resmî paketin `miner.env` ve `docker-compose.yml` dosyaları hazırlanıp oluşturulduktan sonra:

```bash
cd /opt/flop-miner
ls -l docker-compose.yml miner.env
chmod 600 miner.env
ls -l signer session-keys/enclave.seed 2>/dev/null || true
```

FLOP Devnet 7 Kasım'da runtime `1014014`'e geçtiğinde CLI `v0.1.220` uyumsuzdu. Sahada **`v0.1.290`** ile salt-okunur `miner status` çalıştı. **Bu CLI'nin güncel runtime ile uyumunu yeniden doğrula**; daha yeni, resmen uygun sürüm varsa onu seç:

```bash
curl -fsSL https://flop.network/releases.json | python3 -m json.tool | head -100
```

Aşağıdaki image **sahada doğrulanan uyumluluk örneğidir; güncel resmî manifest ile karşılaştırılmalıdır**:

```bash
FLOP_CLI_TEST='ghcr.io/flop-labs/flop-core/cli:v0.1.290@sha256:24e32b034b0d3600ee28127dad30d4228e623235f2dc62da34c2c85ba5e21a88'
docker run --rm --network host "$FLOP_CLI_TEST" --network devnet --rpc wss://rpc.devnet.flop.network network status || true
```

`miner.env` içindeki CLI alanı eski ise, resmî kurulum komutlarının gerektirdiği sürüme **kontrollü** geç. Özel anahtarları yazdırma. `sponsor.sh` yalnızca **ikinci cihazın yeni signer'ı** için çalıştırılmalı. Sponsor `429` / `403` / hata döndürürse adresi değiştirmek yerine hata koduna göre ilerle; onaylı kayıt görünmeden sonraki aşamalara geçme.

Kendi SS58 adresini terminalde bir değişkene yaz (buradaki örnek adresi kendi adresinle değiştir):

```bash
read -r -p 'YENI miner SS58 adresi: ' MINER_ADDRESS
printf '%s\n' "$MINER_ADDRESS" > /opt/flop-miner/miner.address
chmod 600 /opt/flop-miner/miner.address
```

CLI ile salt-okunur zincir doğrulaması:

```bash
docker run --rm --network host "$FLOP_CLI_TEST" \
  --network devnet --rpc wss://rpc.devnet.flop.network \
  miner status "$MINER_ADDRESS" --json
```

**Beklenen:** `registered:true` ve `stake.active:true` (sponsor işlemi tamamlandıktan sonra). Bunun otomatik gerçekleştiğini varsayma. Yanıt `Unsupported runtime spec version` ise CLI sürümü değişmiş olabilir; imaj sürümünü gözden geçir.

---

## 5 — WSL Ubuntu — doğru BF16 modeli indir ve doğrula

Kayıtlı saha modeli: `Qwen/Qwen2.5-0.5B-Instruct`, BF16, root:

`0x1a52c1abe781db051e70ae357f72bb70161ca0c092df0b618f22a9292ba63306`

Modeli kendi adresine kayıtlı modellerle uyumlu şekilde ve *resmî paketin tarif ettiği imaj/CLI* ile indir. Resmî dosya yolu farklıysa parametrelerini README'den al. Saha komutu:

```bash
cd /opt/flop-miner
mkdir -p models/qwen2.5-0.5b-instruct
docker run --rm --network host \
  -v /opt/flop-miner:/work "$FLOP_CLI_TEST" \
  --network devnet --rpc wss://rpc.devnet.flop.network \
  model fetch 0x1a52c1abe781db051e70ae357f72bb70161ca0c092df0b618f22a9292ba63306 \
  --precision BF16 --output-dir /work/models/qwen2.5-0.5b-instruct --json
```

`ok:true` ve `computed_verity_root` eşleşmesini görmeden devam etme. Birden fazla eşzamanlı fetch başlatma. FP16 ile BF16 kimliğini karıştırma.

---

## 6 — WSL Ubuntu — Compose ve kritik TOPLOC ayarları

**Resmî pack'ten üretilmiş Compose** üzerinde `SESSION_COMMIT_IDS` ayarını kontrol et. Bu ayar eksikse v0.1.286/OpenAI/TOPLOC modunda `V2 leaf cannot bind a TOPLOC activation commitment (fail closed)` hatası görülmüştü.

```bash
cd /opt/flop-miner
# Değerleri gizli tokenlarla birlikte tam olarak ekrana bastırma!
grep -nE 'SESSION_COMMIT_IDS:|TOPLOC_ENABLED:|MINER_BACKEND:|SESSION_CHAIN:' docker-compose.yml || true
```

İlgili `worker.environment` içinde bu değerler yer almalı (resmî paketteki eşdeğer değerlerle eşleştir):

```yaml
MINER_BACKEND: openai
TOPLOC_ENABLED: "1"
SESSION_CHAIN: "1"
SESSION_COMMIT_IDS: "1"
```

**Yalnızca `SESSION_CHAIN: "1"` satırı gerçekten varsa** ve `SESSION_COMMIT_IDS` eksikse otomatik ekle:

```bash
cp -p docker-compose.yml "docker-compose.yml.bak-$(date +%Y%m%d-%H%M%S)"
python3 - <<'PY'
from pathlib import Path
p=Path('docker-compose.yml'); s=p.read_text()
if 'SESSION_COMMIT_IDS:' in s:
    print('Already defined; review current value manually.')
else:
    anchor='      SESSION_CHAIN: "1"'
    if s.count(anchor)!=1: raise SystemExit('Anchor not found exactly once. No edits applied. Review Compose YAML.')
    p.write_text(s.replace(anchor, anchor+'\n      SESSION_COMMIT_IDS: "1"'))
    print('SESSION_COMMIT_IDS=1 added')
PY
```

**Worker imajı:** Resmî `releases.json` tarafından onaylanan uyumlu Worker/Backend çiftini kullan. 11 Kasım saha doğrulamasında Worker `v0.1.286` ve Backend `v0.1.239` kombinasyonu ile başarılı settle görüldü; bu kombinasyon evrensel olarak en iyi veya en güncel sürüm demek değildir. Üçüncü taraf worker yaması veya otomatik fence guard'ı yeni bilgisayara **doğrudan ve körlemesine** kopyalama; önce Codex sürüm/digest kontrolü, test ve rollback hazırlasın.

Compose doğrulaması:

```bash
docker compose --env-file miner.env -f docker-compose.yml config -q
# Yalnızca gizli olmayan alanlar:
docker compose --env-file miner.env -f docker-compose.yml config --format json \
  | jq -r '{worker_image:.services.worker.image,backend_image:.services.backend.image,commit_ids:.services.worker.environment.SESSION_COMMIT_IDS,chain:.services.worker.environment.SESSION_CHAIN}'
```

Backend başlat:

```bash
docker compose --env-file miner.env -f docker-compose.yml pull backend worker
docker compose --env-file miner.env -f docker-compose.yml up -d backend
docker compose --env-file miner.env -f docker-compose.yml logs --tail=100 backend
```

Backend model health **pakette tanımlı token'ı konteynerin kendi ortamından kullanarak**:

```bash
docker compose --env-file miner.env -f docker-compose.yml exec -T backend python3 -c '
import os,urllib.request,json
r=urllib.request.Request("http://127.0.0.1:8000/health", headers={"Authorization":"Bearer "+os.environ["INFERENCE_API_KEY"]})
d=json.loads(urllib.request.urlopen(r,timeout=20).read())
print(json.dumps({k:d.get(k) for k in ("model_identity","model_hash","precision","decode_policy_hash")},indent=2))
'
```

---

## 7 — WSL Ubuntu — Cloudflare Quick Tunnel (ücretsiz, geçici)

Yalnızca worker portu `127.0.0.1:8645` tünele bağlanacak; backend portu `8000` **internet üzerinden açılmayacak**.

Cloudflared kurulum dokümanı: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/

Ubuntu amd64 için yayımlanan `.deb` paketini indir ve kur (host mimarisini önce `uname -m` ile doğrula):

```bash
uname -m
cd /tmp
curl -fL --retry 3 -o cloudflared.deb \
  https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared.deb
cloudflared --version
```

Önce manuel tünel aç; URL'yi terminaldeki çıktıda gör:

```bash
cloudflared tunnel --no-autoupdate --url http://127.0.0.1:8645
```

`https://XXXX.trycloudflare.com` adresini not et. `Ctrl+C` yapınca tünel kapanır; otomatik çalıştırmaya geçmeden önce bu bağlantının geçici olduğunu bil.

**Systemd tünel servisi** (WSL Ubuntu'da):

```bash
sudo tee /etc/systemd/system/flop-tunnel.service >/dev/null <<'UNIT'
[Unit]
Description=FLOP Miner Cloudflare Quick Tunnel
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/bin/cloudflared tunnel --no-autoupdate --url http://127.0.0.1:8645
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
UNIT
```

**Kontrol:** `command -v cloudflared` başka bir konuma işaret ediyorsa `ExecStart` yolunu gerçek konuma göre değiştir.

```bash
command -v cloudflared
sudo systemctl daemon-reload
sudo systemctl enable --now flop-tunnel.service
systemctl status flop-tunnel --no-pager -l
journalctl -u flop-tunnel --no-pager -n 70
```

Güncel URL'yi tünel logundan al, **sadece host adını** `SESSION_PUBLIC_HOST=` alanına yaz:

```bash
TUNNEL_URL=$(journalctl -u flop-tunnel --no-pager -o cat | grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' | tail -1)
printf 'Tunnel URL: %s\n' "$TUNNEL_URL"
SESSION_HOST=${TUNNEL_URL#https://}
[ -n "$SESSION_HOST" ] || { echo 'Tunnel hostname not found'; exit 1; }
cp -p miner.env "miner.env.bak-$(date +%Y%m%d-%H%M%S)"
if grep -q '^SESSION_PUBLIC_HOST=' miner.env; then
  sed -i "s|^SESSION_PUBLIC_HOST=.*|SESSION_PUBLIC_HOST=$SESSION_HOST|" miner.env
else
  printf '\nSESSION_PUBLIC_HOST=%s\n' "$SESSION_HOST" >> miner.env
fi
chmod 600 miner.env
```

> `trycloudflare.com` hızlı tünelleri kalıcı değil. URL değişirse endpoint duyurusunu yeniden yap. 7/24 kararlılık için kendi domain'inle yönetilen sabit Cloudflare Tunnel daha uygundur; onun için ayrı Cloudflare hesabı/domain ayarı gerekir.

---

## 8 — WSL Ubuntu — Worker başlat ve doğrula

```bash
cd /opt/flop-miner
docker compose --env-file miner.env -f docker-compose.yml up -d worker
docker compose --env-file miner.env -f docker-compose.yml ps
docker compose --env-file miner.env -f docker-compose.yml logs --tail=100 worker \
  | grep -Ei 'Signer:|ghost|model-gate|Session host|Endpoint ad|error|failed'
```

**Görülmesi gerekenler:** doğru (ikinci cihaza ait) `Signer`, `ghost key`, `model-gate OK`, `Session host listening on :8645`, `Endpoint ad (...) published`.

Worker konteynerinde kritik değişkenleri kontrol et:

```bash
docker compose --env-file miner.env -f docker-compose.yml exec -T worker sh -c \
  'printf "SESSION_COMMIT_IDS=%s\nTOPLOC_ENABLED=%s\n" "$SESSION_COMMIT_IDS" "$TOPLOC_ENABLED"'
```

Yerel sağlık durumunu gizli tokenı bastırmadan kontrol et:

```bash
docker compose --env-file miner.env -f docker-compose.yml exec -T worker node --input-type=module -e '
const base="http://127.0.0.1:"+(process.env.SESSION_PORT||8645);
const r=await fetch(base+"/session/info",{headers:{Authorization:"Bearer "+process.env.SESSION_AUTH_TOKEN},signal:AbortSignal.timeout(15000)});
const d=await r.json();
console.log(JSON.stringify({http:r.status,is_ready:d.is_ready,calibration:d.calibration},null,2));
'
```

Başlangıçta `calibration.ready=false` olması **normal olabilir**; Ghost doğrulanıp kalibrasyon kabul edilmeden önce Worker ücretli oturum almaya hazır sayılmaz.

Dışarıdan endpoint erişimi:

```bash
curl -sS -o /dev/null -w 'public HTTP %{http_code}\n' "https://$SESSION_HOST/session/info"
```

`401` (yetkisiz) bağlantının erişilebilir ve korumalı olduğuna işaret edebilir; içerik doğrulaması değildir. Dışarıda `200` ile token veya özel bilgi ifşa edilmemeli.

---

## 9 — WSL Ubuntu — Ghost kalibrasyonu, gerçek iş ve ödeme

Ghost cevaplarının logunu kontrol et:

```bash
cd /opt/flop-miner
docker compose --env-file miner.env -f docker-compose.yml logs --since=60m worker \
  | grep -Ei 'ghost|calibration|model-gate' | tail -60
```

Zincir kaydı:

```bash
docker run --rm --network host "$FLOP_CLI_TEST" --network devnet \
  --rpc wss://rpc.devnet.flop.network miner status "$MINER_ADDRESS" --json
```

Saha örneğinde Ghost'a cevap verilen iş ile zincirde `verifiedJobs` aynı şey değildi. `calibration.ready:true`, `registered:true`, `stake.active:true` kontrollerini ayrı değerlendir.

Canlı oturum ve işlem hatalarını izlemek için:

```bash
docker compose --env-file miner.env -f docker-compose.yml logs -f --since=5m --timestamps --no-color worker \
  | grep --line-buffered -Ei '\[session\]|minerPaid|settle|ghost.*answered|calibration check failed|TOPLOC.*failed|RefundNoSlash|fenced|timeout|1006'
```

İstenen başarılı akış:

```text
[session] open ...
[session] turn ... toploc=yes
[session] settle cooperative ... minerPaid=...
```

Ayrıca FLOP Explorer'da **aynı kanal için** `registerSessionEvidence`, `submitToplocEvidence` ve `settle` işlemlerini incele. `registerSessionEvidence Success` tek başına ödeme değildir. Devnet'te işlem ücretleri özellikle yüksek olabilir; gerçek gelir/gider için `TransactionFeePaid` olaylarını izle.

---

## 10 — WSL Ubuntu — Codex CLI'yi kur ve kendi hesabınla aç

**Codex = terminalde yerel dosya ve Docker logları üzerinde çalışabilen yazılım ajanı.** Arkadaşın kendi ChatGPT hesabıyla oturum açmalı. Codex'in birinci bilgisayarın ChatGPT oturumunu kullanmasına gerek yok.

**Resmî kurulum rehberi:** https://developers.openai.com/codex/cli

```bash
curl -fsSL https://chatgpt.com/codex/install.sh -o /tmp/install-codex.sh
less /tmp/install-codex.sh
sh /tmp/install-codex.sh
```

> Kurulumun `curl | sh` biçimi de vardır; yukarıda script önce incelenebilsin diye ayrı indirdik. Dağıtım sürümüne göre kurulum yöntemi değişebilir. Önce resmî Codex sayfasını doğrula.

Kurulum sonrası `codex` bulunmuyorsa **bizim WSL saha çözümümüz**:

```bash
ls -l "$HOME/.local/bin/codex" 2>/dev/null || true
export PATH="$HOME/.local/bin:$PATH"
grep -qxF 'export PATH="$HOME/.local/bin:$PATH"' "$HOME/.bashrc" || \
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
hash -r
codex --version
```

Başlat:

```bash
cd /opt/flop-miner
codex
```

İlk açılışta **Sign in with ChatGPT** seçeneğiyle kendi hesabınla giriş yap. Tarayıcı WSL'de açılamıyorsa cihaz-kodlu veya CLI'nin sunduğu başka resmî giriş yöntemini kullan. `--yolo`/onaysız tam sistem yetkisi modlarını kullanma.

> **Öneri:** İlk keşif için Codex'i root yerine normal Linux kullanıcısıyla çalıştır. Docker erişimi ve keystore okuma yetkisi bulunan hesaplar geniş yetkilidir. Codex `codex` komutuyla açılır; terminal kapanınca kendi başına 7/24 izleyen bir servis değildir.

### 10.1 — Codex'e ilk mesaj (kopyala)

```text
Bu Windows/WSL2 Ubuntu bilgisayarında /opt/flop-miner dizinindeki FLOP Devnet GPU Miner'ın teknik bakım asistanısın.

Önce işletim sistemi, Docker, GPU, resmi FLOP miner pack/README, image digest, miner signer SS58, Ghost, kalibrasyon, TOPLOC ve HTTPS tunnel yapılandırmasını incele. Bu bilgisayar için ayrı miner hesabı kullanılmalı; başka host'un signer/seed/keystore dosyaları kopyalanmamalı.

Önce read-only sağlık raporu hazırla. Çalışan oturumları ve belirsiz on-chain işlemleri koru. Signer-fence dosyasını elle silme. Özel anahtarları, mnemonic, bearer token, şifre, imza, inference prompt ve private dosya içeriğini log/ChatGPT/GitHub'a aktarma.

Sorun bulduğunda düzeltme, rollback ve test planını üret; düşük riskli müdahaleleri kullanıcı onayıyla uygula. Devnet'te zincir ücretleri yüksektir: kayıt maliyetini ve minerPaid tutarını ayrı takip et. Sadece `registered:true` veya `docker running` görmek gerçek `settle` kanıtı değildir.

İlk çıktıyı Türkçe özetle: GPU/Docker sağlığı, Worker/Backend sürümleri, model-gate, Ghost, is_ready, calibration.ready, signer fenced, tunnel endpoint, zincir kayıt ve oturum/settle başarısı.
```

---

## 11 — WSL Ubuntu — bağımsız 7/24 gözlem (Codex'ten ayrı)

Codex'in kendi kendine 7/24 çalıştığını **varsayma**. İlk kurulumda güvenli bir **salt okunur** systemd kontrolü kuracağız; signer-fence ve açık oturumları doğrulamadan otomatik restart **etmeyeceğiz**. Böylece cihaz yanlışlıkla oturum ortasında restart döngüsüne girmez.

Aşağıdaki Python programı Docker CLI üzerinden Worker'ın yetkili `/session/info` ve `/internal/signer-fence` endpoint'lerini sorgular; tokenı dışarı yazmaz. Docker Compose env dosyası içinden tokenı çekip loglamaz; sorgu worker içinde yapılır.

```bash
sudo install -d -m 750 /opt/flop-monitor
sudo tee /opt/flop-monitor/health.py >/dev/null <<'PY'
#!/usr/bin/env python3
import json, subprocess, datetime, sys
BASE='/opt/flop-miner'
SCRIPT=r'''const base='http://127.0.0.1:'+(process.env.SESSION_PORT||8645);
async function call(path){const r=await fetch(base+path,{headers:{Authorization:'Bearer '+process.env.SESSION_AUTH_TOKEN},signal:AbortSignal.timeout(10000)});if(!r.ok)throw Error(path+' HTTP '+r.status);return await r.json()}
try{const i=await call('/session/info'),f=await call('/internal/signer-fence');console.log(JSON.stringify({ready:i.is_ready,calibration_ready:i.calibration?.ready,calibration_state:i.calibration?.state,calibration_reason:i.calibration?.reason||null,fenced:f.fenced}));}catch(e){console.error(String(e.message));process.exitCode=2;}'''
cmd=['docker','compose','--env-file','miner.env','-f','docker-compose.yml','exec','-T','worker','node','--input-type=module','-e',SCRIPT]
try:
    p=subprocess.run(cmd,cwd=BASE,text=True,capture_output=True,timeout=25)
    if p.returncode!=0: raise RuntimeError((p.stderr or 'worker query failed')[-200:])
    d=json.loads(p.stdout)
    print(datetime.datetime.now(datetime.timezone.utc).isoformat(), 'miner-health', json.dumps(d,ensure_ascii=False))
except Exception as e:
    print(datetime.datetime.now(datetime.timezone.utc).isoformat(), 'monitor-error',str(e)[:220]);sys.exit(2)
PY
sudo chmod 750 /opt/flop-monitor/health.py
```

Servis (root yetkili; Docker erişimi gerektirir):

```bash
sudo tee /etc/systemd/system/flop-readonly-health.service >/dev/null <<'UNIT'
[Unit]
Description=FLOP Devnet miner read-only health check
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 /opt/flop-monitor/health.py
UNIT

sudo tee /etc/systemd/system/flop-readonly-health.timer >/dev/null <<'UNIT'
[Unit]
Description=Check FLOP miner health every 2 minutes

[Timer]
OnBootSec=2min
OnUnitInactiveSec=2min
Unit=flop-readonly-health.service

[Install]
WantedBy=timers.target
UNIT

sudo systemctl daemon-reload
sudo systemctl enable --now flop-readonly-health.timer
systemctl list-timers flop-readonly-health.timer --all
sudo systemctl start flop-readonly-health.service
journalctl -u flop-readonly-health.service -n 20 --no-pager
```

> Bu **gözlemci** otomatik restart yapmaz. Bizim önceki Miner sistemimizde signer-fence, aktif kanallar ve DA belirsizliği yüzünden otomatik restart'ın fail-closed kalması gerektiği görüldü. Codex'e, yeni cihazdaki gerçek zincir koşullarını doğrulamadan restart otomasyonu yazdırma.

---

## 12 — Windows bilgisayar kapanınca/uykuya geçince ne olur?

Windows uyursa WSL, Docker ve Codex de durabilir. Windows açılması WSL'nin otomatik açılacağı anlamına gelmez. En basit güvenilir işletim: Windows'ta Görev Zamanlayıcı ile **kendi kullanıcı hesabına ait** WSL dağıtımını oturum açıldıktan sonra başlat; ancak ilk kurulum ve sağlık testleri tamamlanmadan otomatik başlatma ayarlama.

Windows PowerShell'de manuel doğrulama:

```powershell
wsl -d Ubuntu-24.04 --exec /bin/bash -lc 'systemctl is-active docker; systemctl is-active flop-tunnel; systemctl is-active flop-readonly-health.timer'
```

`docker compose` servislerinde uygun `restart: unless-stopped` politikası tanımlı olmalı. Quick Tunnel adresi WSL yeniden başladığında değişebileceğinden eski `SESSION_PUBLIC_HOST` değerinin kalması **yeni iş almayı engelleyebilir**. Bunu güvenli biçimde keşfedip güncelleyecek ayrı bir yönetim mekanizması Codex tarafından geliştirilebilir, ancak açık kanallar varken Worker'ı körlemesine yeniden başlatmamalı.

---

## 13 — Güvenlik, yedek ve sorun giderme

**Yalnız yeni bilgisayarda, ayrı gizli yedek:**

```bash
cd /opt/flop-miner
umask 077
BACKUP="$HOME/flop-miner-backup-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$BACKUP"
cp -p docker-compose.yml miner.env "$BACKUP/"
for p in signer session-keys/enclave.seed miner.json miner.address; do
  [ ! -e "$p" ] || cp --parents -p "$p" "$BACKUP/"
done
chmod -R go-rwx "$BACKUP"
echo "Backup directory created under home (private): $BACKUP"
```

**Not:** Bu yedek klasörü gizli anahtar içerebilir; Windows Downloads'a, GitHub'a veya Discord'a kopyalama. Fiziksel disk arızası için **şifrelenmiş, ayrı depolama alanında** yedek de oluştur. Docker named volume'deki Ghost anahtarı ve worker state de kritik olabilir; onu ayrıca, Worker güvenli şekilde boşta olduğunda yedekle. `docker compose down -v` **kullanma**.

### Sahada görülen hatalar

| Hata | Ne anlama gelir / kontrol |
|---|---|
| `Unsupported runtime spec version 1014014` | CLI eski olabilir; uyumlu resmî image/digest kontrol et |
| `MODEL_VERIFICATION_FAILED` | Model hash, BF16 precision ve indirme bütünlüğünü kontrol et |
| `V2 leaf cannot bind a TOPLOC activation commitment` | `SESSION_COMMIT_IDS=1` ve Worker/Backend sürüm eşleşmesine bak |
| `ghost poll failed` | Mailbox DNS/HTTPS ve container erişimini test et; aralıklı timeout olabilir |
| `calibration check failed ... 60s` | Kalibrasyon ağır RPC sorguları; `state_getRuntimeVersion` tek başına yeterli test değil |
| `/session/info is_ready=false` | Worker yeni oturum kabul etmeye hazır olmayabilir; `calibration.reason` oku |
| `miner signer is fenced` | İşlem sonucu belirsiz; **fence dosyasını silme**; finalized nonce ve pending sonuçları uzlaştır |
| `registerSessionEvidence Success` ama ödeme yok | Bu ödeme değil; kanıt kayıt ücreti ödenmiştir, `submitToplocEvidence` ve `settle` ayrıca izlenmeli |
| `Closed` ve 1 raw-unit escrow | Dust/test gateway kanalı olabilir; otomatik olarak miner arızası sayma |
| Cloudflare hostname değişti | Güncel endpoint ile `SESSION_PUBLIC_HOST` ve duyuruyu eşleştir |
| `codex` bulunamıyor | `$HOME/.local/bin` PATH'e eklenmiş mi, link sağlam mı kontrol et |

### Faydalı kaynaklar

- Resmî Miner dokümanı: https://docs.flop.network/docs/run-miner
- Resmî yayın manifesti: https://flop.network/releases.json
- Resmî Devnet Explorer: https://explorer.devnet.flop.network/
- Resmî FLOP destek konuları: https://github.com/flop-labs/network/issues
- Bağımsız TR/EN eğitim kaynağı (çalıştırılabilir resmî paket yerine geçmez): https://github.com/omerbek/flop-local-miner
- Codex CLI dokümanı: https://developers.openai.com/codex/cli
- NVIDIA CUDA on WSL: https://docs.nvidia.com/cuda/wsl-user-guide/

---

## 14 — Son kabul kontrol listesi

- [ ] WSL2 Ubuntu 24.04 ve `systemd` etkin.
- [ ] Windows NVIDIA sürücüsü ve WSL içi `nvidia-smi` çalışıyor.
- [ ] Docker GPU konteyner testi çalışıyor.
- [ ] Resmî miner pack checksum **OK**.
- [ ] İkinci bilgisayar için **ayrı Miner signer/keystore** oluşturuldu, özel yedeklendi.
- [ ] Yeni hesap sponsor ile kayıtlı ve `stake.active:true`.
- [ ] BF16 model indirildi ve verity root eşleşti.
- [ ] Backend `/health` modeli doğruluyor.
- [ ] Cloudflare tüneli güncel public host ile çalışıyor.
- [ ] Worker signer doğru; `SESSION_COMMIT_IDS=1`; `model-gate OK`.
- [ ] Ghost işlerine yanıt ve kalibrasyon `active/ready`.
- [ ] En az bir ücretli oturumda `registerSessionEvidence → submitToplocEvidence → settle` zincirden doğrulandı (sırf `open` yeterli değil).
- [ ] Codex CLI ayrı hesapta açıldı.
- [ ] 2 dakikalık salt-okunur monitor/timer çalışıyor; otomatik restart güvenlik onayı olmadan kapalı.
- [ ] Bakiye/işlem ücretleri, key/fence/WSL kapanma davranışı anlaşıldı.

**Bitti sayma kriteri:** Sadece `docker ps` veya `registered:true` değil, çalışan GPU + `calibration.ready:true` + finalized `settle` doğrulaması.