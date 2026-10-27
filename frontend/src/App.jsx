import { useEffect, useMemo, useState } from "react";
import axios from "axios";
import {
  ResponsiveContainer, PieChart, Pie, Cell, Tooltip,
  BarChart, Bar, XAxis, YAxis, CartesianGrid
} from "recharts";
import {
  Activity, LayoutDashboard, TrendingUp, HeartPulse, Newspaper,
  RefreshCw, Search, ExternalLink, Menu, Flame
} from "lucide-react";
import "./App.css";
import "./heat.css";
import { TrendHero, HeatBoard, FilterChips, TrendDetailModal } from "./TrendViews";
import { matchesChip } from "./trendUtils";

const API_URL =
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
const COLORS = ["#16a36a", "#94a3b8", "#ef4444"];

const NAV = [
  { id: "overview", label: "Overview", icon: LayoutDashboard },
  { id: "trends", label: "Trending Topics", icon: TrendingUp },
  { id: "sentiment", label: "Sentiment Analysis", icon: HeartPulse },
  { id: "feed", label: "News & Social Feed", icon: Newspaper },
];

export default function App() {
  const [page, setPage] = useState("overview");
  const [data, setData] = useState({
    trends: [], sentiment: [], articles: [], posts: []
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [source, setSource] = useState("all");
  const [mobileMenu, setMobileMenu] = useState(false);

  // Heat board & filter state
  const [chip, setChip] = useState("all");
  const [heroDetail, setHeroDetail] = useState(null);

  // Trend Drill-down modal state
  const [selectedTopic, setSelectedTopic] = useState(null);
  const [trendDetail, setTrendDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  
async function loadDashboard() {
  setLoading(true);
  setError("");

  try {
    const [t, s, a, p] = await Promise.all([
      axios.get(`${API_URL}/trends/`),
      axios.get(`${API_URL}/sentiment/`),
      axios.get(`${API_URL}/articles/`),
      axios.get(`${API_URL}/posts/`),
    ]);

    setData({
      trends: t.data.trends ?? [],
      sentiment: s.data.sentiment ?? [],
      articles: a.data.articles ?? [],
      posts: p.data.posts ?? [],
    });
  } catch (e) {
    console.error("TrendLens API error:", e);
    setError(
      "Could not connect to the TrendLens API. Please try again later."
    );
  } finally {
    setLoading(false);
  }
}


  useEffect(() => { loadDashboard(); }, []);

  const sortedTrends = useMemo(() =>
    [...data.trends].sort((a, b) =>
      Number(b.trend_score || 0) - Number(a.trend_score || 0)
    ), [data.trends]);

  // Fetch contextual details for the #1 top trending hero
  useEffect(() => {
    if (sortedTrends.length > 0) {
      const topTopic = sortedTrends[0].topic_or_keyword;
      axios.get(`${API_URL}/trends/${encodeURIComponent(topTopic)}`)
        .then(res => setHeroDetail(res.data))
        .catch(err => console.error("Could not fetch hero detail:", err));
    }
  }, [sortedTrends]);

  async function openTrendDetail(topic) {
    if (!topic) return;
    setSelectedTopic(topic);
    setDetailLoading(true);
    try {
      const res = await axios.get(
  `${API_URL}/trends/${encodeURIComponent(topic)}`
);
      setTrendDetail(res.data);
    } catch (err) {
      console.error("Error loading trend details:", err);
    } finally {
      setDetailLoading(false);
    }
  }

  function closeTrendDetail() {
    setSelectedTopic(null);
    setTrendDetail(null);
  }

  const sentimentCounts = useMemo(() => {
    const result = { positive: 0, neutral: 0, negative: 0 };
    data.sentiment.forEach((x) => {
      const label = (x.label || "neutral").toLowerCase();
      if (label in result) result[label]++;
      else result.neutral++;
    });
    return result;
  }, [data.sentiment]);

  const sentimentData = [
    { name: "Positive", value: sentimentCounts.positive, color: COLORS[0] },
    { name: "Neutral", value: sentimentCounts.neutral, color: COLORS[1] },
    { name: "Negative", value: sentimentCounts.negative, color: COLORS[2] },
  ];

  const content = useMemo(() => [
    ...data.articles.map(x => ({ ...x, kind: "News" })),
    ...data.posts.map(x => ({ ...x, kind: "Hacker News" })),
  ].sort((a, b) =>
    new Date(b.published_at || b.created_utc || b.created_at || 0) -
    new Date(a.published_at || a.created_utc || a.created_at || 0)
  ), [data.articles, data.posts]);

  const filteredTrends = sortedTrends.filter(x =>
    String(x.topic_or_keyword || "").toLowerCase().includes(search.toLowerCase())
  );

  const chipFilteredTrends = useMemo(() => {
    return filteredTrends.filter(t => matchesChip(t, chip));
  }, [filteredTrends, chip]);

  const filteredContent = content.filter(x => {
    const matchesSearch = `${x.title || ""} ${x.content || ""} ${x.body || ""}`
      .toLowerCase().includes(search.toLowerCase());
    const matchesSource = source === "all" ||
      (source === "news" && x.kind === "News") ||
      (source === "hacker" && x.kind === "Hacker News");
    return matchesSearch && matchesSource;
  });

  const currentTitle = NAV.find(x => x.id === page)?.label || "Overview";

  return (
    <div className="app-shell">
      <aside className={`sidebar ${mobileMenu ? "sidebar-open" : ""}`}>
        <div className="brand">
          <div className="brand-icon"><Activity size={23}/></div>
          <div><strong>TrendLens</strong><small>MEDIA INTELLIGENCE</small></div>
        </div>
        <div className="nav-caption">WORKSPACE</div>
        <nav>
          {NAV.map(({ id, label, icon: Icon }) => (
            <button key={id}
              className={`nav-item ${page === id ? "active" : ""}`}
              onClick={() => { setPage(id); setSearch(""); setMobileMenu(false); }}>
              <Icon size={18}/><span>{label}</span>
            </button>
          ))}
        </nav>
        <div className="sidebar-status">
          <span className="status-dot"/>
          <div><strong>API connection</strong><small>TrendLens backend online</small></div>
        </div>
        <div className="sidebar-footer">TREND INTELLIGENCE PLATFORM</div>
      </aside>

      <main className="main-content">
        {/* Live Top Trend Pulse Ticker */}
        {sortedTrends.length > 0 && (
          <div className="trend-ticker">
            <span className="ticker-label"><Flame size={14}/> LIVE TREND PULSE</span>
            <div className="ticker-scroll">
              {sortedTrends.slice(0, 6).map((t, idx) => (
                <button
                  key={t.id ?? t.topic_or_keyword}
                  className="ticker-chip"
                  onClick={() => openTrendDetail(t.topic_or_keyword)}
                  title="Click to inspect this trend"
                >
                  <span className="ticker-rank">#{idx + 1}</span>
                  <span className="ticker-topic">{t.topic_or_keyword}</span>
                  <span className="ticker-score">{Number(t.trend_score || 0).toFixed(1)}</span>
                  {Number(t.velocity_score) > 0 && (
                    <span className="ticker-growth">+{Math.round(Number(t.velocity_score) * 100)}%</span>
                  )}
                </button>
              ))}
            </div>
          </div>
        )}

        <header className="topbar">
          <button className="mobile-menu" onClick={() => setMobileMenu(!mobileMenu)} aria-label="Toggle menu">
            <Menu size={21}/>
          </button>
          <div className="page-heading">
            <div className="eyebrow">WORKSPACE / {currentTitle.toUpperCase()}</div>
            <h1>{page === "overview" ? "Trend Intelligence Dashboard" : currentTitle}</h1>
            <p>
              {page === "overview" && "Trending in the news: real-time global topics synthesized across worldwide publications, GDELT, and international outlets."}
              {page === "trends" && "Click any topic to explore its growth velocity, distinct news outlets, and full headline coverage."}
              {page === "sentiment" && "Emotional tone and consensus distribution across collected articles and stories."}
              {page === "feed" && "Search and inspect individual articles and social posts."}
            </p>
          </div>
          <button className="refresh-btn" onClick={loadDashboard} disabled={loading}>
            <RefreshCw size={16} className={loading ? "spin" : ""}/>
            <span>{loading ? "Refreshing..." : "Refresh data"}</span>
          </button>
        </header>

        {error && <div className="error-banner">{error}</div>}

        {loading ? <div className="loading"><Activity size={24}/> Loading analytics…</div> : (
          <>
            {page === "overview" && (
              <>
                {/* Visual Trend Hero */}
                <TrendHero
                  trend={sortedTrends[0]}
                  detail={heroDetail}
                  onOpen={openTrendDetail}
                />

                <section className="metric-grid">
                  <Metric label="Active Trends" value={data.trends.length} note="Verified multi-source topics" icon={<TrendingUp/>}/>
                  <Metric label="News Articles" value={data.articles.length} note="GNews verified coverage" icon={<Newspaper/>}/>
                  <Metric label="Social Stories" value={data.posts.length} note="Hacker News community" icon={<Activity/>}/>
                  <Metric label="Analyzed Content" value={data.sentiment.length} note="Sentiment & NLP processed" icon={<HeartPulse/>}/>
                </section>

                <section className="overview-grid">
                  <Panel title="Sentiment distribution" subtitle="Classification across collected documents">
                    <SentimentChart data={sentimentData}/>
                  </Panel>
                  <Panel title="Top trending topics" subtitle="Ranked by growth velocity & cross-platform validation (click to explore)">
                    <TrendList trends={sortedTrends.slice(0, 6)} onSelect={openTrendDetail}/>
                    <button className="text-link" onClick={() => setPage("trends")}>Explore all trends <span>→</span></button>
                  </Panel>
                </section>

                <Panel title="Latest collected content" subtitle="Recently collected news and social posts">
                  <ContentList items={content.slice(0, 6)}/>
                  <button className="text-link" onClick={() => setPage("feed")}>Explore all content <span>→</span></button>
                </Panel>
              </>
            )}

            {page === "trends" && (
              <>
                {/* Heat Board with Chips */}
                <section className="board-section">
                  <div className="board-head">
                    <h2>Interactive Heat Board</h2>
                    <p>Pick a topic to see why it is moving. Colors show heat: yellow is warm, red is hot.</p>
                  </div>
                  <FilterChips value={chip} onChange={setChip} trends={filteredTrends} />
                  <HeatBoard trends={chipFilteredTrends} onSelect={openTrendDetail} />
                </section>

                <Panel title="Trend Explorer & Rankings" subtitle="Click any row to open the Explainable AI breakdown and supporting articles">
                  <SearchBox value={search} onChange={setSearch} placeholder="Search topics (e.g., openai, model, china)…"/>
                  <div className="chart-large">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={chipFilteredTrends.slice(0, 10).map(x => ({
                        name: x.topic_or_keyword, score: Number(x.trend_score || 0)
                      }))} layout="vertical" margin={{left: 18, right: 25}}>
                        <CartesianGrid strokeDasharray="3 3" horizontal={false}/>
                        <XAxis type="number" domain={[0, 100]} tick={{fontSize: 11}}/>
                        <YAxis type="category" dataKey="name" width={155} tick={{fontSize: 11, fontWeight: 600}}/>
                        <Tooltip formatter={(val) => [`${val} / 100`, "Trend Score"]}/>
                        <Bar dataKey="score" name="Trend score" fill="#f97316" radius={[0, 6, 6, 0]}/>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                  <TrendList trends={chipFilteredTrends.slice(0, 50)} detailed onSelect={openTrendDetail}/>
                </Panel>
              </>
            )}

            {page === "sentiment" && (
              <>
                <section className="metric-grid">
                  {sentimentData.map((x) => (
                    <Metric key={x.name} label={`${x.name} sentiment`} value={x.value}
                      note={`${data.sentiment.length ? (100*x.value/data.sentiment.length).toFixed(1) : "0.0"}% of analyzed records`}
                      icon={<HeartPulse/>} color={x.color}/>
                  ))}
                  <Metric label="Total analyzed" value={data.sentiment.length} note="VADER scored items" icon={<Activity/>}/>
                </section>
                <section className="overview-grid">
                  <Panel title="Sentiment breakdown" subtitle="Distribution by predicted tone">
                    <SentimentChart data={sentimentData}/>
                  </Panel>
                  <Panel title="How Sentiment Momentum Works" subtitle="Transparent NLP explainability">
                    <div className="explanation-list">
                      <p><span className="sentiment-dot positive"/> <strong>Positive Tone:</strong> News & posts praising advancements, funding, or efficiency.</p>
                      <p><span className="sentiment-dot neutral"/> <strong>Neutral Tone:</strong> Technical announcements, benchmark logs, and documentation.</p>
                      <p><span className="sentiment-dot negative"/> <strong>Negative / Skeptical:</strong> Safety risks, regulatory scrutiny, outages, and critique.</p>
                      <small>TrendLens weights sentiment momentum (shifts in tone) rather than simply rewarding raw positivity.</small>
                    </div>
                  </Panel>
                </section>
                <Panel title="Sentiment records" subtitle="Individual document classifications">
                  <div className="table-wrap">
                    <table>
                      <thead><tr><th>Type</th><th>Content ID</th><th>Sentiment</th><th>Compound score</th></tr></thead>
                      <tbody>{data.sentiment.slice(0, 50).map(x => (
                        <tr key={x.id}><td>{x.content_type}</td><td>{x.content_id}</td>
                          <td><span className={`pill ${x.label}`}>{x.label}</span></td>
                          <td>{Number(x.compound || 0).toFixed(3)}</td></tr>
                      ))}</tbody>
                    </table>
                  </div>
                </Panel>
              </>
            )}

            {page === "feed" && (
              <Panel title="Content library" subtitle={`${filteredContent.length} matching collected items`}>
                <div className="filter-row">
                  <SearchBox value={search} onChange={setSearch} placeholder="Search titles and content…"/>
                  <select value={source} onChange={e => setSource(e.target.value)}>
                    <option value="all">All sources</option>
                    <option value="news">News articles</option>
                    <option value="hacker">Hacker News</option>
                  </select>
                </div>
                <ContentList items={filteredContent} detailed/>
              </Panel>
            )}
          </>
        )}
        <footer className="page-footer">TrendLens Media Intelligence · Verified PostgreSQL & NLP Analysis Engine</footer>
      </main>

      {/* Interactive Trend Deep-Dive Modal */}
      {selectedTopic && (
        <TrendDetailModal
          topic={selectedTopic}
          detail={trendDetail}
          loading={detailLoading}
          onClose={closeTrendDetail}
        />
      )}
    </div>
  );
}

function Metric({ label, value, note, icon, color }) {
  return <div className="metric-card">
    <div className="metric-top"><span>{label}</span>
      <div style={color ? {color, background: `${color}18`} : {}}>{icon}</div></div>
    <div className="metric-value">{Number(value).toLocaleString()}</div>
    <div className="metric-caption">{note}</div>
  </div>;
}

function Panel({ title, subtitle, children }) {
  return <section className="panel">
    <div className="panel-heading"><div><h2>{title}</h2><p>{subtitle}</p></div></div>
    {children}
  </section>;
}

function SearchBox({ value, onChange, placeholder }) {
  return <label className="search-box"><Search size={17}/>
    <input value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder}/>
  </label>;
}

function SentimentChart({ data }) {
  return <>
    <div className="chart-wrap">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie data={data} dataKey="value" nameKey="name" innerRadius={62} outerRadius={91}
            paddingAngle={3} cx="50%" cy="50%">
            {data.map((x) => <Cell key={x.name} fill={x.color}/>)}
          </Pie>
          <Tooltip/>
        </PieChart>
      </ResponsiveContainer>
    </div>
    <div className="legend">{data.map(x => (
      <div key={x.name}><span style={{background:x.color}}/>{x.name}<strong>{x.value}</strong></div>
    ))}</div>
  </>;
}

function TrendList({ trends, detailed = false, onSelect }) {
  if (!trends.length) return <div className="empty-state">No matching trends found.</div>;
  return <div className="trend-list">{trends.map((x, i) => {
    const vel = Number(x.velocity_score || 0);
    const sources = Number(x.source_count || 1);
    const score = Number(x.trend_score || 0).toFixed(1);
    const mentions = Number(x.mention_count || 0);

    return (
      <div
        className={`trend-row ${detailed ? "trend-row-detailed" : ""} clickable-trend`}
        key={x.id ?? `${x.topic_or_keyword}-${i}`}
        onClick={() => onSelect && onSelect(x.topic_or_keyword)}
        title="Click to view full trend analysis"
      >
        <span className="rank">{String(i+1).padStart(2,"0")}</span>
        <div className="trend-info">
          <span className="trend-name">{x.topic_or_keyword}</span>
          <div className="trend-badges">
            {vel > 0 && <span className="badge-growth">🔥 +{Math.round(vel * 100)}% Growth</span>}
            {sources > 1 && <span className="badge-source">🌐 {sources} Outlets</span>}
            <span className="badge-mentions">{mentions} doc{mentions === 1 ? "" : "s"}</span>
          </div>
        </div>
        {detailed && (
          <div className="trend-meta">
            <span>Covered by {sources} outlet{sources === 1 ? "" : "s"}</span>
            <small>{vel > 0 ? "Accelerating" : "Baseline"}</small>
          </div>
        )}
        <div className="score-badge">
          <strong>{score}</strong>
          <small>/100</small>
        </div>
      </div>
    );
  })}</div>;
}

function ContentList({ items, detailed = false }) {
  if (!items.length) return <div className="empty-state">No content matches your search.</div>;
  return <div className="content-list">{items.map((x, i) => (
    <article className="content-row" key={`${x.kind}-${x.id ?? i}`}>
      <span className={`content-tag ${x.kind === "News" ? "tag-news" : "tag-social"}`}>{x.kind}</span>
      <div className="content-main">
        <strong>{x.title || "Untitled"}</strong>
        {detailed && <p>{(x.content || x.body || "").slice(0, 220) || "No description available."}</p>}
        <small>{x.source_name || x.kind}</small>
      </div>
      {x.url && <a className="open-link" href={x.url} target="_blank" rel="noreferrer" aria-label="Open source"><ExternalLink size={16}/></a>}
    </article>
  ))}</div>;
}
