/** 与后端的唯一通信层。 */

async function req(path, opts = {}) {
  const r = await fetch("/api" + path, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  let data = null;
  try { data = await r.json(); } catch { /* 空响应 */ }
  if (!r.ok) {
    const msg = data && data.detail ? data.detail : `请求失败(${r.status})`;
    throw new Error(msg);
  }
  return data;
}

const POST = (body) => ({ method: "POST", body: body ? JSON.stringify(body) : null });

export const api = {
  health: () => req("/health"),
  achievements: () => req("/achievements"),
  reincarnate: (name) => req("/reincarnate", POST(name ? { name } : {})),
  reroll: (id) => req(`/life/${id}/reroll`, POST()),
  start: (id) => req(`/life/${id}/start`, POST()),
  get: (id) => req(`/life/${id}`),
  advance: (id) => req(`/life/${id}/advance`, POST()),
  choose: (id, index) => req(`/life/${id}/choose`, POST({ index })),
};

export function fmtMoney(n) {
  if (n === null || n === undefined) return "0";
  if (n < 0) return `-${fmtMoney(-n)}(负债)`;
  if (n >= 1e8) return `${(n / 1e8).toFixed(2)}亿`;
  if (n >= 1e4) return `${(n / 1e4).toFixed(1)}万`;
  return String(n);
}
