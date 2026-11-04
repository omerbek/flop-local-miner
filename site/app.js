"use strict";

// No requests or persistent storage: selected reports stay in this tab's DOM only.
const translations = {
  en: {
    portable: ["Portable GPU", "Check per-device memory, thermal and power limits. Laptop and desktop cards with similar names are not interchangeable."],
    desktop: ["Desktop GPU", "Check free memory, driver compatibility and the actual container test. A product name or large VRAM value alone does not prove FLOP support."],
    workstation: ["Workstation GPU", "Inspect compute capability and memory per device; official checkpoint and decode-policy approval remain separate requirements."],
    multi: ["Multi-GPU host", "Inspect every device separately. The diagnostic does not pool VRAM, imply one miner per device or combine independent computers."],
    copied: "Copied", copyFailed: "Select and copy the command manually", invalidFile: "Choose a .json file of 1 MiB or less; other file types are not opened.",
    invalidReport: "This is not a valid masked gpu_detect.py schema v1 report. No evidence gate changed.",
    readError: "The file could not be read locally. No evidence gate changed.",
    selected: "Local report loaded. GPU visibility is reported by this file, not independently checked here; all other gates remain unknown.",
    selectedEmpty: "Local report loaded; zero devices reported. Dry-run may have skipped all probes, so GPU absence is not established. Every gate remains unknown.",
    reported: "REPORTED, NOT VERIFIED", unknown: "Unknown", count: n => `${n} GPU${n === 1 ? "" : "s"} reported`,
    environment: "Environment classification (not FLOP approval)", status: {"ready for environment test": "Ready for environment test", "needs intervention": "Needs intervention", "not verified for FLOP": "Not verified for FLOP"},
    device: "Device", memoryTotal: "Total VRAM", memoryFree: "Free VRAM", driver: "Driver", cuda: "CUDA driver max", temperature: "Temperature", power: "Power limit", compute: "Compute capability", statusLabel: "Diagnostic status", missing: "Not available", mib: "MiB", celsius: "°C", watts: "W"
  },
  tr: {
    portable: ["Dizüstü GPU", "Her cihazın bellek, sıcaklık ve güç sınırlarını kontrol et. Benzer adlı dizüstü ve masaüstü kartları eşdeğer değildir."],
    desktop: ["Masaüstü GPU", "Boş belleği, sürücü uyumunu ve gerçek konteyner testini kontrol et. Ürün adı veya yüksek VRAM tek başına FLOP desteği kanıtlamaz."],
    workstation: ["İş istasyonu GPU'su", "Cihaz başına işlem yeteneği ve belleği incele; resmî checkpoint ve decode politikası onayı ayrı gereksinimlerdir."],
    multi: ["Çoklu GPU sistemi", "Her cihazı ayrı incele. Teşhis VRAM'i birleştirmez; cihaz başına bir madenci veya bağımsız bilgisayarların birleşmesini varsaymaz."],
    copied: "Kopyalandı", copyFailed: "Komutu seçip elle kopyala", invalidFile: "1 MiB veya daha küçük bir .json dosyası seç; başka dosya türleri açılmaz.",
    invalidReport: "Bu, geçerli ve maskelenmiş gpu_detect.py şema v1 raporu değil. Kanıt eşikleri değişmedi.",
    readError: "Dosya yerelde okunamadı. Kanıt eşikleri değişmedi.",
    selected: "Yerel rapor yüklendi. GPU görünürlüğü bu dosyada bildirilmiştir; burada bağımsız doğrulanmadı. Diğer eşikler bilinmiyor.",
    selectedEmpty: "Yerel rapor yüklendi; sıfır cihaz bildirildi. Deneme modu tüm sorguları atlamış olabilir; GPU yokluğu kanıtlanmaz. Tüm eşikler bilinmiyor.",
    reported: "BİLDİRİLDİ, DOĞRULANMADI", unknown: "Bilinmiyor", count: n => `${n} GPU bildirildi`,
    environment: "Ortam sınıfı (FLOP onayı değil)", status: {"ready for environment test": "Ortam testine hazır", "needs intervention": "Müdahale gerekiyor", "not verified for FLOP": "FLOP için doğrulanmadı"},
    device: "Cihaz", memoryTotal: "Toplam VRAM", memoryFree: "Boş VRAM", driver: "Sürücü", cuda: "CUDA sürücü üst sınırı", temperature: "Sıcaklık", power: "Güç sınırı", compute: "İşlem yeteneği", statusLabel: "Teşhis durumu", missing: "Kullanılamıyor", mib: "MiB", celsius: "°C", watts: "W"
  }
};
let language = "en";
let reportReadSequence = 0;
let reportDisplayState = "none";
let profile = "portable";
const byId = id => document.getElementById(id);
const message = byId("report-message");

let displayedReport = null;

function localizedText(element, english, turkish) {
  element.dataset.en = english;
  element.dataset.tr = turkish;
  element.textContent = language === "tr" ? turkish : english;
  return element;
}
function setLanguage(next) {
  language = next;
  document.documentElement.lang = next;
  document.title = next === "tr" ? "FLOP Local Miner · Teşhis Konsolu" : "FLOP Local Miner · Diagnostic Mission Control";
  document.querySelectorAll("[data-en][data-tr]").forEach(node => { node.textContent = node.dataset[next]; });
  const labels = [
    [".primary-nav", "aria-label", "Primary navigation", "Ana gezinme"],
    [".lang-switch", "aria-label", "Language", "Dil"],
    [".notice", "aria-label", "Current project status", "Güncel proje durumu"],
    [".profile-tabs", "aria-label", "Illustrative GPU profiles", "Temsili GPU profilleri"],
    [".path-switch", "aria-label", "Operating system path", "İşletim sistemi yolu"],
    [".art-strip img", "alt", "Four independent stages, all initially unknown", "Dört bağımsız aşama, başlangıçta hepsi bilinmiyor"],
    [".wide-art", "alt", "Windows and native Ubuntu paths converge on local diagnostics; official FLOP and accepted work require separate proof", "Windows ve yerel Ubuntu yolları yerel teşhiste birleşir; resmî FLOP ve kabul edilen iş ayrı kanıt gerektirir"],
    [".flow-figure img", "alt", "Illustrative Windows, WSL2, Docker, GPU, then locked FLOP path", "Temsili Windows, WSL2, Docker, GPU, ardından kilitli FLOP yolu"]
  ];
  for (const [selector, attribute, english, turkish] of labels) {
    document.querySelector(selector).setAttribute(attribute, next === "tr" ? turkish : english);
  }
  document.querySelectorAll(".copy").forEach(button => {
    button.dataset.ariaEn ??= button.getAttribute("aria-label");
    button.setAttribute("aria-label", next === "tr" ? "Komutu kopyala" : button.dataset.ariaEn);
  });
  byId("lang-en").setAttribute("aria-pressed", String(next === "en"));
  byId("lang-tr").setAttribute("aria-pressed", String(next === "tr"));
  byId("guide-link").href = `../docs/README.${next}.md`;
  setProfile(profile);
  if (displayedReport) {
    displayReport(displayedReport);
  } else if (reportDisplayState !== "none") {
    message.textContent = translations[next][reportDisplayState];
  }
}
byId("lang-en").addEventListener("click", () => setLanguage("en"));
byId("lang-tr").addEventListener("click", () => setLanguage("tr"));

function setProfile(next) {
  profile = next;
  document.querySelectorAll(".profile-choice").forEach(button => {
    const active = button.dataset.profile === next;
    button.classList.toggle("is-selected", active);
    button.setAttribute("aria-pressed", String(active));
  });
  [byId("profile-heading").textContent, byId("profile-description").textContent] = translations[language][next];
}
document.querySelectorAll(".profile-choice").forEach(button => button.addEventListener("click", () => setProfile(button.dataset.profile)));

const pathTabs = [byId("tab-windows"), byId("tab-ubuntu")];
function setPath(tab, focus = false) {
  pathTabs.forEach(button => {
    const active = button === tab;
    button.setAttribute("aria-selected", String(active));
    button.tabIndex = active ? 0 : -1;
    byId(button.getAttribute("aria-controls")).hidden = !active;
  });
  if (focus) tab.focus();
}
pathTabs.forEach((tab, index) => {
  tab.addEventListener("click", () => setPath(tab));
  tab.addEventListener("keydown", event => {
    if (!["ArrowRight", "ArrowLeft", "Home", "End"].includes(event.key)) return;
    event.preventDefault();
    const next = event.key === "Home" ? 0 : event.key === "End" ? pathTabs.length - 1 : (index + (event.key === "ArrowRight" ? 1 : -1) + pathTabs.length) % pathTabs.length;
    setPath(pathTabs[next], true);
  });
});

function commandText(button) { return button.closest(".command").querySelector("code").innerText.replace(/\r/g, ""); }
async function copyCommand(button) {
  const value = commandText(button);
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(value);
    } else {
      const temporary = document.createElement("textarea");
      temporary.value = value;
      temporary.style.position = "fixed";
      temporary.style.opacity = "0";
      document.body.append(temporary);
      temporary.select();
      try {
        if (!document.execCommand("copy")) throw new Error("Clipboard unavailable");
      } finally { temporary.remove(); }
    }
    button.textContent = translations[language].copied;
  } catch {
    button.textContent = translations[language].copyFailed;
  }
  window.setTimeout(() => { button.textContent = button.dataset[language]; }, 2200);
}
document.querySelectorAll(".copy").forEach(button => button.addEventListener("click", () => { void copyCommand(button); }));

const isRecord = value => value !== null && typeof value === "object" && !Array.isArray(value);
const isNullableString = value => value === null || (typeof value === "string" && value.length <= 160);
const isNullableNumber = value => value === null || (typeof value === "number" && Number.isFinite(value));
function validReport(value) {
  if (!isRecord(value) || value.schema_version !== 1 || !isRecord(value.host)) return false;
  if (!isNullableString(value.host.platform) || !["[redacted]", null].includes(value.host.hostname) || !["[redacted]", null].includes(value.host.ip)) return false;
  if (!Number.isSafeInteger(value.gpu_count) || value.gpu_count < 0 || value.gpu_count > 128 || !Array.isArray(value.gpus) || value.gpus.length !== value.gpu_count) return false;
  if (!["ready for environment test", "needs intervention", "not verified for FLOP"].includes(value.status)) return false;
  if (!isRecord(value.official_runtime) || value.official_runtime.status !== "NOT_IMPLEMENTED" || !Array.isArray(value.model_recommendations)) return false;
  const seen = new Set();
  for (const gpu of value.gpus) {
    if (!isRecord(gpu) || !Number.isSafeInteger(gpu.index) || gpu.index < 0 || seen.has(gpu.index)) return false;
    seen.add(gpu.index);
    if (!isNullableString(gpu.name) || !["[redacted]", null].includes(gpu.uuid)) return false;
    if (![gpu.memory_total_mib, gpu.memory_free_mib, gpu.temperature_c, gpu.power_limit_w].every(isNullableNumber)) return false;
    if (![gpu.driver_version, gpu.cuda_driver_max, gpu.compute_capability, gpu.status].every(isNullableString)) return false;
    if (!Array.isArray(gpu.reasons)) return false;
  }
  return true;
}
function statusText(status) { return translations[language].status[status] || translations[language].unknown; }
function dataText(value, suffix = "") { return value === null || value === undefined || value === "" ? translations[language].missing : `${value}${suffix}`; }
function resetReport(state = "none") {
  reportDisplayState = state;
  displayedReport = null;
  byId("report-details").hidden = true;
  byId("report-gpus").replaceChildren();
  byId("report-models").replaceChildren();
  byId("clear-report").hidden = true;
  const tag = byId("visibility-state");
  tag.classList.remove("reported", "absent");
  localizedText(tag, "UNKNOWN", "BİLİNMİYOR");
  message.textContent = state === "none" ? message.dataset[language] : translations[language][state];
}
function gpuCard(gpu) {
  const t = translations[language];
  const card = document.createElement("article");
  card.className = "gpu-result";
  const title = document.createElement("h3");
  title.textContent = `${t.device} ${gpu.index}: ${dataText(gpu.name)}`;
  card.append(title);
  const dl = document.createElement("dl");
  const fields = [
    ["memoryTotal", dataText(gpu.memory_total_mib, ` ${t.mib}`)], ["memoryFree", dataText(gpu.memory_free_mib, ` ${t.mib}`)],
    ["driver", dataText(gpu.driver_version)], ["cuda", dataText(gpu.cuda_driver_max)],
    ["temperature", dataText(gpu.temperature_c, ` ${t.celsius}`)], ["power", dataText(gpu.power_limit_w, ` ${t.watts}`)],
    ["compute", dataText(gpu.compute_capability)], ["statusLabel", statusText(gpu.status)]
  ];
  for (const [key, value] of fields) {
    const dt = document.createElement("dt");
    localizedText(dt, translations.en[key], translations.tr[key]);
    const dd = document.createElement("dd");
    dd.textContent = value;
    dl.append(dt, dd);
  }
  card.append(dl);
  return card;
}
function displayReport(report) {
  displayedReport = report;
  reportDisplayState = report.gpu_count > 0 ? "loaded" : "empty";
  const tag = byId("visibility-state");
  tag.classList.remove("reported", "absent");
  if (report.gpu_count > 0) tag.classList.add("reported");
  localizedText(tag, report.gpu_count > 0 ? translations.en.reported : "UNKNOWN", report.gpu_count > 0 ? translations.tr.reported : "BİLİNMİYOR");
  message.textContent = translations[language][report.gpu_count > 0 ? "selected" : "selectedEmpty"];
  const counter = byId("report-gpu-count");
  counter.dataset.count = String(report.gpu_count);
  counter.textContent = translations[language].count(report.gpu_count);
  const status = byId("report-status");
  status.dataset.status = report.status;
  status.textContent = `${translations[language].environment}: ${statusText(report.status)}`;
  const cards = document.createDocumentFragment();
  report.gpus.forEach(gpu => cards.append(gpuCard(gpu)));
  byId("report-gpus").replaceChildren(cards);
  // Model recommendations cannot establish FLOP eligibility; do not elevate them to evidence.
  localizedText(byId("report-models"),
    "Model suggestions are intentionally not shown as FLOP approval. Check the official checkpoint, policy, memory and calibration requirements independently.",
    "Model önerileri bilerek FLOP onayı olarak gösterilmez. Resmî checkpoint, politika, bellek ve kalibrasyon gereksinimlerini ayrı doğrula.");
  byId("report-details").hidden = false;
  byId("clear-report").hidden = false;
}
byId("report-file").addEventListener("change", async event => {
  const sequence = ++reportReadSequence;
  resetReport();
  const file = event.target.files?.[0];
  if (!file) return;
  if (!/\.json$/i.test(file.name) || file.size < 1 || file.size > 1024 * 1024 || (file.type && !["application/json", "text/json"].includes(file.type))) {
    resetReport("invalidFile");
    return;
  }
  try {
    const report = JSON.parse((await file.text()).replace(/^\uFEFF/, ""));
    if (sequence !== reportReadSequence) return;
    if (!validReport(report)) { resetReport("invalidReport"); return; }
    displayReport({
      gpu_count: report.gpu_count,
      status: report.status,
      gpus: report.gpus.map(gpu => ({
        index: gpu.index, name: gpu.name, memory_total_mib: gpu.memory_total_mib,
        memory_free_mib: gpu.memory_free_mib, driver_version: gpu.driver_version,
        cuda_driver_max: gpu.cuda_driver_max, temperature_c: gpu.temperature_c,
        power_limit_w: gpu.power_limit_w, compute_capability: gpu.compute_capability,
        status: gpu.status
      }))
    });
  } catch {
    if (sequence === reportReadSequence) resetReport("readError");
  }
});
byId("clear-report").addEventListener("click", () => {
  reportReadSequence++;
  byId("report-file").value = "";
  resetReport();
  byId("report-file").focus();
});
