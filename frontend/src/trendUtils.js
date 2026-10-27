export const MIN_FOR_GROWTH = 3;
export const MIN_FOR_SURGE = 5;

const num = (v) => Number(v) || 0;
const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));

export function classify(t) {
  const mentions = num(t.mention_count);
  const sources = num(t.source_count) || 1;
  const velocity = num(t.velocity_score);
  const growing = velocity > 0 && mentions >= MIN_FOR_GROWTH;

  if (growing && velocity >= 0.5 && mentions >= MIN_FOR_SURGE)
    return { tier: "surging", label: "Surging", icon: "🔥" };
  if (growing) return { tier: "rising", label: "Rising", icon: "📈" };
  if (sources > 1 && mentions >= 2)
    return { tier: "confirmed", label: "Confirmed", icon: "✅" };
  return { tier: "early", label: "Early signal", icon: "🌱" };
}

export function describe(t) {
  const m = num(t.mention_count);
  const s = num(t.source_count) || 1;
  const v = num(t.velocity_score);
  const base = `Covered by ${s} outlet${s === 1 ? "" : "s"} across ${m} article${m === 1 ? "" : "s"}`;
  const { tier } = classify(t);
  if (tier === "surging" || tier === "rising")
    return `${base}, up ${Math.round(v * 100)}% since the last check.`;
  if (tier === "confirmed")
    return `${base}. Outlets agree, but there is no growth history yet.`;
  return `${base}. Early signal in the global news cycle.`;
}

export const heatOf = (score) => clamp(num(score) / 50, 0, 1);

export function heatColors(score) {
  const hue = Math.round(48 - 40 * heatOf(score));
  return {
    accent: `hsl(${hue} 92% 50%)`,
    tint: `hsl(${hue} 95% ${96 - heatOf(score) * 7}%)`,
    deep: `hsl(${hue} 85% 30%)`,
  };
}

export function matchesChip(t, chip) {
  const { tier } = classify(t);
  const cat = (t.category || "world").toLowerCase();
  if (chip === "hot") return tier === "surging" || tier === "rising";
  if (chip === "confirmed") return num(t.source_count) > 1;
  if (chip === "early") return tier === "early";
  if (["world", "business", "technology", "sports", "health", "nation"].includes(chip)) {
    return cat === chip || (chip === "technology" && cat === "tech");
  }
  return true;
}

export function breakdown(l) {
  const v = clamp(num(l.velocity_score), 0, 1);
  const b = clamp(num(l.burst_score), 0, 1);
  const s = clamp(num(l.source_count), 0, 3) / 3;
  const parts = [
    { key: "velocity", label: "Growth", pts: 40 * v, max: 40 },
    { key: "burst", label: "Sudden spike", pts: 30 * b, max: 30 },
    { key: "source", label: "Seen in several sources", pts: 20 * s, max: 20 },
  ];
  const known = parts.reduce((a, p) => a + p.pts, 0);
  parts.push({
    key: "other",
    label: "Names and tone",
    pts: clamp(num(l.trend_score) - known, 0, 10),
    max: 10,
  });
  return parts;
}
