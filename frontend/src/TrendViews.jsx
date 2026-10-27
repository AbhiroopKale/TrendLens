import { useEffect, useMemo } from "react";
import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
} from "recharts";
import { Activity, X, ArrowUpRight, Newspaper, TrendingUp, Info } from "lucide-react";
import {
  classify, describe, heatColors, breakdown, matchesChip, MIN_FOR_GROWTH,
} from "./trendUtils";

const score1 = (t) => Number(t?.trend_score || 0).toFixed(1);

export function TrendHero({ trend, detail, onOpen }) {
  if (!trend) {
    return (
      <section className="hero hero-empty">
        <h2 className="hero-topic">No trends yet</h2>
        <p className="hero-why">Run the pipeline once, then press Refresh data.</p>
      </section>
    );
  }
  const c = classify(trend);
  const { accent } = heatColors(trend.trend_score);
  const heads = [
    ...(detail?.articles || []).slice(0, 2).map((a) => ({ id: `a${a.id}`, kind: "News", title: a.title, url: a.url })),
    ...(detail?.posts || []).slice(0, 1).map((p) => ({
      id: `p${p.id}`, kind: "Hacker News", title: p.title,
      url: p.url || `https://news.ycombinator.com/item?id=${p.id}`,
    })),
  ];
  const pct = Math.min(100, Number(trend.trend_score || 0));

  return (
    <section className="hero" style={{ "--accent": accent }}>
      <div className="hero-main">
        <p className="hero-kicker">{c.icon} {c.label}, hottest topic right now</p>
        <h2 className="hero-topic">{trend.topic_or_keyword}</h2>
        <p className="hero-why">{describe(trend)}</p>
        <button className="hero-btn" onClick={() => onOpen(trend.topic_or_keyword)}>
          See why it is trending
        </button>
      </div>
      <div className="hero-meter" aria-label={`Heat ${score1(trend)} out of 100`}>
        <div className="meter-num">{score1(trend)}</div>
        <div className="meter-label">heat, out of 100</div>
        <div className="meter-track"><div className="meter-fill" style={{ width: `${pct}%` }} /></div>
      </div>
      {heads.length > 0 && (
        <ul className="hero-heads">
          {heads.map((h) => (
            <li key={h.id}>
              <span className="hero-src">{h.kind}</span>
              <a href={h.url} target="_blank" rel="noreferrer">{h.title}</a>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export function HeatBoard({ trends, onSelect }) {
  if (!trends.length) {
    return <div className="empty-state">Nothing matches. Clear the search or pick another filter.</div>;
  }
  return (
    <div className="heat-board">
      {trends.map((t) => {
        const c = classify(t);
        const { accent, tint, deep } = heatColors(t.trend_score);
        const big = c.tier === "surging" || c.tier === "rising";
        const m = Number(t.mention_count || 0);
        const s = Number(t.source_count || 1);
        return (
          <button
            key={t.id ?? t.topic_or_keyword}
            className={`tile ${big ? "tile-big" : ""}`}
            style={{ "--accent": accent, "--tint": tint, "--deep": deep }}
            onClick={() => onSelect(t.topic_or_keyword)}
            title={describe(t)}
          >
            <span className="tile-top">
              <span className="tile-badge">{c.icon} {c.label}</span>
              <span className="tile-score">{score1(t)}</span>
            </span>
            <span className="tile-topic">{t.topic_or_keyword}</span>
            <span className="tile-meta">Covered by {s} outlet{s === 1 ? "" : "s"} · {m} article{m === 1 ? "" : "s"}</span>
          </button>
        );
      })}
    </div>
  );
}

const CHIPS = [
  { id: "all", label: "All World News" },
  { id: "world", label: "World" },
  { id: "business", label: "Business" },
  { id: "technology", label: "Technology" },
  { id: "sports", label: "Sports" },
  { id: "hot", label: "Rising / Surging" },
  { id: "confirmed", label: "Multi-outlet (2+)" },
];

export function FilterChips({ value, onChange, trends }) {
  return (
    <div className="chips" role="group" aria-label="Filter topics">
      {CHIPS.map((c) => (
        <button key={c.id} className={`chip ${value === c.id ? "chip-on" : ""}`} onClick={() => onChange(c.id)}>
          {c.label} <span className="chip-n">{trends.filter((t) => matchesChip(t, c.id)).length}</span>
        </button>
      ))}
    </div>
  );
}

export function TrendDetailModal({ topic, detail, loading, onClose }) {
  useEffect(() => {
    const onKey = (e) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const latest = detail?.latest;
  const history = useMemo(() => {
    if (!detail?.results) return [];
    return [...detail.results].reverse().map((r) => ({
      time: new Date(r.computed_at).toLocaleString("en-US", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" }),
      score: Number(r.trend_score || 0),
    }));
  }, [detail]);

  const mentions = Number(latest?.mention_count || 0);
  const velocity = Number(latest?.velocity_score || 0);
  const growthKnown = (detail?.count || 0) >= 2 && mentions >= MIN_FOR_GROWTH;
  const tone = Number(latest?.sentiment_delta || 0);
  const parts = latest ? breakdown(latest) : [];

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card" role="dialog" aria-modal="true" aria-label={`Details for ${topic}`} onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <p className="modal-kicker">{latest ? `${classify(latest).icon} ${classify(latest).label}` : "Trend details"}</p>
            <h2>{topic}</h2>
            {latest && <p className="modal-why">{describe(latest)}</p>}
          </div>
          <button className="modal-close-btn" onClick={onClose} aria-label="Close"><X size={20} /></button>
        </div>

        {loading ? (
          <div className="modal-loading"><Activity size={24} className="spin" /> Loading details…</div>
        ) : !detail || !latest ? (
          <div className="empty-state">No history for this topic yet. Run the pipeline again later.</div>
        ) : (
          <div className="modal-body">
            <div className="detail-stat-grid">
              <div className="detail-stat-card primary">
                <span className="stat-label">Heat</span>
                <div className="stat-big">{score1(latest)} <small>/ 100</small></div>
                <div className="stat-note">Combined score, explained below</div>
              </div>
              <div className="detail-stat-card">
                <span className="stat-label">Growth</span>
                <div className="stat-big">{growthKnown ? `${velocity > 0 ? "+" : ""}${Math.round(velocity * 100)}%` : "Too early"}</div>
                <div className="stat-note">{growthKnown ? "Since the last check" : `Needs ${MIN_FOR_GROWTH}+ mentions and 2+ checks`}</div>
              </div>
              <div className="detail-stat-card">
                <span className="stat-label">Seen in</span>
                <div className="stat-big">{mentions} <small>mentions</small></div>
                <div className="stat-note">{latest.source_count ?? 1} source{Number(latest.source_count) === 1 ? "" : "s"}</div>
              </div>
              <div className="detail-stat-card">
                <span className="stat-label">Tone change</span>
                <div className="stat-big">{Math.abs(tone) < 0.05 ? "Steady" : "Shifting"}</div>
                <div className="stat-note">How coverage tone moved since last check</div>
              </div>
            </div>

            <div className="detail-section">
              <div className="section-title"><TrendingUp size={16} /> <span>Heat over time ({detail.count} check{detail.count === 1 ? "" : "s"})</span></div>
              {detail.count < 2 ? (
                <p className="soft-note">Only one check so far. The curve appears after the next pipeline run.</p>
              ) : (
                <div className="modal-chart-wrap">
                  <ResponsiveContainer width="100%" height={200}>
                    <AreaChart data={history} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
                      <defs>
                        <linearGradient id="heatGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#f97316" stopOpacity={0.45} />
                          <stop offset="95%" stopColor="#f97316" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                      <XAxis dataKey="time" tick={{ fontSize: 10 }} stroke="#94a3b8" />
                      <YAxis domain={[0, 100]} tick={{ fontSize: 10 }} stroke="#94a3b8" />
                      <Tooltip />
                      <Area type="monotone" dataKey="score" name="Heat" stroke="#ea580c" strokeWidth={2.5} fill="url(#heatGrad)" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>

            <div className="detail-section">
              <div className="section-title"><Info size={16} /> <span>How the score is built</span></div>
              <div className="build-bar" role="img" aria-label="Score breakdown">
                {parts.map((p) => p.pts > 0 && (
                  <div key={p.key} className={`build-seg seg-${p.key}`} style={{ width: `${p.pts}%` }} title={`${p.label}: ${p.pts.toFixed(1)} points`} />
                ))}
              </div>
              <ul className="build-legend">
                {parts.map((p) => (
                  <li key={p.key}>
                    <span className={`dot seg-${p.key}`} />
                    {p.label}
                    <strong>{p.pts.toFixed(1)} of {p.max}</strong>
                  </li>
                ))}
              </ul>
            </div>

            <div className="detail-section">
              <div className="section-title"><Newspaper size={16} /> <span>Stories behind it ({detail.articles?.length || 0} news, {detail.posts?.length || 0} discussions)</span></div>
              <div className="modal-content-list">
                {detail.articles?.map((a) => (
                  <div key={`a${a.id}`} className="modal-content-item">
                    <span className="content-pill news">{a.source_name || "News"}</span>
                    <a href={a.url} target="_blank" rel="noreferrer" className="headline-link">{a.title} <ArrowUpRight size={13} /></a>
                  </div>
                ))}
                {detail.posts?.map((p) => (
                  <div key={`p${p.id}`} className="modal-content-item">
                    <span className="content-pill social">Hacker News</span>
                    <a href={p.url || `https://news.ycombinator.com/item?id=${p.id}`} target="_blank" rel="noreferrer" className="headline-link">{p.title} <ArrowUpRight size={13} /></a>
                  </div>
                ))}
                {!detail.articles?.length && !detail.posts?.length && (
                  <div className="empty-state">No matching stories found for this keyword.</div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
