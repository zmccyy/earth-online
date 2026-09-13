/** 前端状态机与渲染:标题 → 投胎 → 人生 → 结算。 */
import { api, fmtMoney } from "./api.js";

const $ = (sel) => document.querySelector(sel);

const ATTR_META = {
  health: { name: "体质", color: "#6fd66f" },
  intellect: { name: "智力", color: "#4f8cff" },
  appearance: { name: "颜值", color: "#ff8fab" },
  happiness: { name: "快乐", color: "#f5b942" },
};

const TAG_RIBBON = {
  normal: "日常任务",
  big: "人生大事",
  bad: "危机警报",
  good: "天降机缘",
};

let life = null;          // 当前人生状态(服务端权威)
let galleryCache = null;  // 成就定义缓存

/* ---------- 屏幕切换 ---------- */
function show(id) {
  document.querySelectorAll(".screen").forEach((s) => s.classList.remove("active"));
  $(id).classList.add("active");
  window.scrollTo(0, 0);
}

function toast(msg) {
  const t = $("#toast");
  t.textContent = msg;
  t.classList.remove("hidden");
  clearTimeout(t._timer);
  t._timer = setTimeout(() => t.classList.add("hidden"), 2600);
}

/* ---------- 渲染:投胎(抽卡) ---------- */
function attrRow(k, v) {
  const m = ATTR_META[k];
  return `<div class="attr-row">
    <div class="attr-label"><span>${m.name}</span><b>${v}</b></div>
    <div class="attr-bar"><div class="attr-fill" style="width:${v}%;background:${m.color}"></div></div>
  </div>`;
}

function renderCreate(state) {
  life = state;
  const fam = state.family, home = state.hometown;
  $("#char-card").className = `gacha-card rar-${fam.tier}`;
  $("#char-card").innerHTML = `
    <div class="rarity-tag">${fam.tier}</div>
    <div class="cc-head">
      <div class="avatar">${state.name[0]}</div>
      <div class="cc-id">
        <b>${state.name}</b><span class="g-tag">${state.gender} · 0岁</span>
        <div class="talent-line">✨ ${state.talent}</div>
      </div>
    </div>
    <div class="cc-rows">
      <div class="cc-row">
        <span class="cc-label">家 境</span>
        <div><b>${fam.name}</b><small>${fam.desc}</small></div>
        <span class="cc-money">${fmtMoney(fam.money)}</span>
      </div>
      <div class="cc-row">
        <span class="cc-label">出生地</span>
        <div><b>${home.name}</b><small>${home.desc}</small></div>
      </div>
    </div>
    <div class="cc-attrs">${Object.entries(state.attrs).map(([k, v]) => attrRow(k, v)).join("")}</div>`;
  $("#reroll-left").textContent = state.rerolls_left;
  $("#btn-reroll").disabled = state.rerolls_left <= 0;
  show("#screen-create");
}

/* ---------- 渲染:主游戏 ---------- */
function renderStatus() {
  $("#p-avatar").textContent = life.name[0];
  $("#p-name").textContent = life.name;
  $("#p-gender").textContent = life.gender;
  $("#p-age").textContent = life.age;
  $("#p-stage").textContent = life.stage || "—";
  $("#attr-list").innerHTML = Object.entries(life.attrs).map(([k, v]) => attrRow(k, v)).join("");
  $("#p-money").textContent = fmtMoney(life.money);
  $("#p-jobname").textContent = life.job ? life.job.name : "无业";
  const flags = Object.keys(life.flags || {}).filter((f) => life.flags[f]);
  $("#p-flags").innerHTML = flags.map((f) => `<span class="flag-chip">${f}</span>`).join("");
}

function logEntry(e, i = 0) {
  const cls = { good: "log-good", bad: "log-bad", big: "log-big", achieve: "log-achieve", calm: "log-calm" }[e.kind] || "";
  const delay = i ? `style="animation-delay:${Math.min(i * 45, 400)}ms"` : "";
  return `<div class="log-entry ${cls}" ${delay}><span class="log-age">${e.age}</span>${e.text}</div>`;
}

function renderTimeline(entries) {
  const tl = $("#timeline");
  entries.forEach((e, i) => tl.insertAdjacentHTML("beforeend", logEntry(e, i)));
  tl.scrollTop = tl.scrollHeight;
}

function resetTimeline() {
  $("#timeline").innerHTML = "";
  renderTimeline(life.log || []);
}

function setAdvanceState(enabled) {
  const b = $("#btn-advance");
  b.disabled = !enabled;
  b.textContent = enabled ? "▶ 活过这一年" : "⏸ 事件待决策";
}

function showEvent(ev) {
  const card = $("#event-card");
  if (!ev) { card.classList.add("hidden"); return; }
  card.className = `event-card ev-${ev.tag || "normal"}`;
  $("#ev-ribbon").textContent = TAG_RIBBON[ev.tag] || "日常任务";
  $("#ev-name").textContent = ev.name;
  $("#ev-text").textContent = ev.text;
  $("#ev-choices").innerHTML = "";
  ev.choices.forEach((c, i) => {
    const b = document.createElement("button");
    b.className = "btn";
    b.textContent = c.text;
    b.dataset.key = i + 1;
    b.onclick = () => choose(i);
    $("#ev-choices").appendChild(b);
  });
  card.classList.remove("hidden");
}

function afterYearUpdate(yearLogs) {
  renderStatus();
  renderTimeline(yearLogs);
  if (life.status === "dead") { renderSummary(life); return; }
  showEvent(life.pending_event);
  setAdvanceState(!life.pending_event);
}

async function advance() {
  if (!life || life.status !== "living" || life.pending_event) return;
  try {
    const r = await api.advance(life.life_id);
    life = r.state;
    afterYearUpdate(r.logs);
  } catch (e) { toast(e.message); }
}

async function choose(index) {
  try {
    const r = await api.choose(life.life_id, index);
    life = r.state;
    afterYearUpdate(r.logs);
  } catch (e) { toast(e.message); }
}

/* ---------- 渲染:结算 ---------- */
function renderSummary(state) {
  const s = state.summary;
  showEvent(null);
  $("#s-grade").textContent = s.grade;
  $("#s-grade").className = `grade-badge g-${s.grade.replace("+", "")}`;
  $("#s-grade-name").textContent = `${s.grade_name} · 享年${s.age}岁`;
  $("#s-cause").textContent = `注销原因:${s.cause}`;
  $("#s-comment").textContent = s.comment;
  $("#s-stats").innerHTML = `
    <div>💰 最终存款<b>${fmtMoney(s.final_money)}</b></div>
    <div>🎓 最高学历<b>${s.education || "无"}</b></div>
    <div>🏅 成就数<b>${s.achievements.length}</b></div>
    <div>⏳ 游戏时长<b>${s.age} 年</b></div>`;
  $("#s-highlights").innerHTML = (s.highlights || []).map((h) => `<div>· ${h}</div>`).join("")
    || "<div>· 一生平淡,没有值得写进回忆录的大事。</div>";
  $("#s-review").textContent = s.review;
  unlockAchievements(state.achievements);
  show("#screen-summary");
}

/* ---------- 成就图鉴 ---------- */
function unlockedSet() {
  return new Set(JSON.parse(localStorage.getItem("eol_achievements") || "[]"));
}

function unlockAchievements(ids) {
  const set = unlockedSet();
  const before = set.size;
  ids.forEach((i) => set.add(i));
  localStorage.setItem("eol_achievements", JSON.stringify([...set]));
  if (set.size > before) toast(`🏅 人生图鉴已更新(${set.size} 枚徽章)`);
}

async function openGallery() {
  if (!galleryCache) galleryCache = await api.achievements();
  const set = unlockedSet();
  const defs = galleryCache.achievements;
  const got = defs.filter((a) => set.has(a.id)).length;
  $("#gallery-count").textContent = `${got} / ${defs.length}`;
  $("#gallery-grid").innerHTML = defs.map((a) => `
    <div class="ach-card ${set.has(a.id) ? "" : "locked"}">
      <span class="ach-rarity ${rarityClass(a.rarity)}">${a.rarity}</span>
      <div class="ach-icon">${a.icon}</div>
      <div class="ach-name">${a.name}</div>
      <div class="ach-desc">${a.desc}</div>
    </div>`).join("");
  $("#modal-gallery").classList.remove("hidden");
}

function rarityClass(tier) { return `r-${tier}`; }

/* ---------- 键盘:空格快进,数字键选择 ---------- */
document.addEventListener("keydown", (e) => {
  if ($("#modal-gallery").classList.contains("hidden") === false) {
    if (e.key === "Escape") $("#modal-gallery").classList.add("hidden");
    return;
  }
  if (!$("#screen-game").classList.contains("active")) return;
  if (e.code === "Space") { e.preventDefault(); advance(); return; }
  const n = parseInt(e.key, 10);
  if (n >= 1 && life && life.pending_event && n <= life.pending_event.choices.length) {
    choose(n - 1);
  }
});

/* ---------- 事件绑定 ---------- */
$("#btn-login").onclick = async () => {
  try { renderCreate(await api.reincarnate()); }
  catch (e) { toast(e.message); }
};
$("#btn-reroll").onclick = async () => {
  try { renderCreate(await api.reroll(life.life_id)); }
  catch (e) { toast(e.message); }
};
$("#btn-confirm").onclick = async () => {
  try {
    life = await api.start(life.life_id);
    $("#event-card").classList.add("hidden");
    renderStatus();
    resetTimeline();
    setAdvanceState(true);
    show("#screen-game");
  } catch (e) { toast(e.message); }
};
$("#btn-advance").onclick = advance;
$("#btn-again").onclick = async () => {
  try { renderCreate(await api.reincarnate()); }
  catch (e) { toast(e.message); }
};
$("#btn-gallery").onclick = openGallery;
$("#btn-gallery2").onclick = openGallery;
$("#btn-close-gallery").onclick = () => $("#modal-gallery").classList.add("hidden");
$("#modal-gallery").onclick = (e) => {
  if (e.target === $("#modal-gallery")) $("#modal-gallery").classList.add("hidden");
};

/* ---------- 启动 ---------- */
(async () => {
  try {
    const h = await api.health();
    // 横幅里的在线人数保持梗数字,health 只用于探活
  } catch {
    document.querySelector("#server-banner").innerHTML =
      '<span class="dot" style="background:var(--red);box-shadow:0 0 8px var(--red)"></span> 服务器离线,天道正在加班抢修……';
  }
})();
