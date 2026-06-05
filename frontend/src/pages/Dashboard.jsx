import { useState } from "react"
import { Link } from "react-router-dom"
import { useApi } from "../hooks/useApi"
import { api } from "../api"
import MapChart from "../components/MapChart"
import MarketIntel from "../components/MarketIntel"
import JobsTable from "../components/JobsTable"
import SkillGap from "../components/SkillGap"

const TABS = ["Map", "Trends", "Jobs", "Skill Gap", "Market Intelligence"]

export default function Dashboard() {
  const [tab, setTab]         = useState("Map")
  const [filters, setFilters] = useState({ role: "", city: "", remote: "", experience: "" })

  const { data: health }   = useApi(api.health)
  const { data: trending } = useApi(api.trending)
  const { data: insights } = useApi(api.insights)
  const { data: mapData }  = useApi(
    () => api.mapData({ role: filters.role || undefined, remote: filters.remote || undefined }),
    [filters.role, filters.remote]
  )
  const { data: jobsData } = useApi(
    () => api.jobs({
      role:       filters.role       || undefined,
      city:       filters.city       || undefined,
      remote:     filters.remote     || undefined,
      experience: filters.experience || undefined,
    }),
    [filters.role, filters.city, filters.remote, filters.experience]
  )

  const topCities = (mapData || []).slice(0, 5)

  return (
    <div className="h-screen flex flex-col bg-cream overflow-hidden">

      {/* Top bar */}
      <div className="border-b border-border bg-white px-5 h-12 flex items-center justify-between shrink-0">
        <Link to="/" className="flex items-center gap-1.5 text-muted hover:text-ink transition-colors text-sm">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
          <div className="flex items-center gap-1.5">
            <div className="w-5 h-5 rounded bg-amber flex items-center justify-center">
              <svg viewBox="0 0 24 24" fill="none" className="w-3 h-3 text-white"
                   stroke="currentColor" strokeWidth="2.5">
                <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z" />
                <circle cx="12" cy="9" r="2.5" />
              </svg>
            </div>
            <span className="font-semibold text-ink text-sm">HireMap <span className="text-amber">PH</span></span>
          </div>
        </Link>

        {health?.total_active_jobs > 0 && (
          <div className="flex items-center gap-1.5 text-xs text-muted">
            <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
            {health.total_active_jobs.toLocaleString()} listings · {health.last_updated?.slice(0,10)}
          </div>
        )}
      </div>

      {/* Filter bar */}
      <div className="border-b border-border bg-white px-5 py-2 flex items-center gap-2 flex-wrap shrink-0">
        <input
          className="border border-border rounded-lg px-3 py-1.5 text-sm text-ink
                     placeholder:text-muted bg-cream focus:outline-none focus:border-amber w-40"
          placeholder="Role / keyword"
          value={filters.role}
          onChange={e => setFilters(f => ({ ...f, role: e.target.value }))}
        />
        <input
          className="border border-border rounded-lg px-3 py-1.5 text-sm text-ink
                     placeholder:text-muted bg-cream focus:outline-none focus:border-amber w-32"
          placeholder="City"
          value={filters.city}
          onChange={e => setFilters(f => ({ ...f, city: e.target.value }))}
        />
        <select
          className="border border-border rounded-lg px-3 py-1.5 text-sm text-ink
                     bg-cream focus:outline-none focus:border-amber"
          value={filters.remote}
          onChange={e => setFilters(f => ({ ...f, remote: e.target.value }))}
        >
          <option value="">Any work type</option>
          <option value="true">Remote only</option>
          <option value="false">Onsite only</option>
        </select>
        <select
          className="border border-border rounded-lg px-3 py-1.5 text-sm text-ink
                     bg-cream focus:outline-none focus:border-amber"
          value={filters.experience}
          onChange={e => setFilters(f => ({ ...f, experience: e.target.value }))}
        >
          <option value="">Any level</option>
          <option value="entry">Entry</option>
          <option value="mid">Mid</option>
          <option value="senior">Senior</option>
        </select>
        {Object.values(filters).some(Boolean) && (
          <button
            className="text-xs text-muted hover:text-ink underline"
            onClick={() => setFilters({ role:"", city:"", remote:"", experience:"" })}
          >
            Clear
          </button>
        )}
      </div>

      {/* Pill tabs */}
      <div className="border-b border-border bg-white px-5 py-2 shrink-0">
        <div className="inline-flex gap-1 bg-cream rounded-lg p-1">
          {TABS.map(t => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all duration-150 ${
                tab === t
                  ? "bg-white text-ink shadow-sm border border-border"
                  : "text-muted hover:text-ink"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* Tab content — all mounted, hidden when not active to avoid white flash */}
      <div className="flex-1 overflow-hidden relative">

        {/* MAP */}
        <div className={`absolute inset-0 ${tab === "Map" ? "flex" : "hidden"} flex-col`}>
          <div className="flex-1 grid grid-cols-[1fr_260px] overflow-hidden">
            <div className="overflow-hidden p-4 h-full">
              <MapChart mapData={mapData || []} />
            </div>
            <div className="border-l border-border p-4 overflow-y-auto">
              <MarketIntel
                insights={insights || {}}
                trending={trending || {}}
                topCities={topCities}
              />
            </div>
          </div>
        </div>

        {/* TRENDS */}
        <div className={`absolute inset-0 overflow-y-auto p-6 ${tab === "Trends" ? "block" : "hidden"}`}>
          {trending ? (
            <div className="max-w-3xl mx-auto flex flex-col gap-6">

              {/* KPI row */}
              <div className="grid grid-cols-3 gap-4">
                {[
                  { label: "New this week", value: trending.this_week?.new_jobs ?? "—", sub: "listings entered the market" },
                  { label: "New last week", value: trending.last_week?.new_jobs ?? "—", sub: "for comparison" },
                  { label: "Top role",      value: Object.keys(trending.this_week?.top_roles || {})[0] ?? "—", sub: "most listed this week" },
                ].map(k => (
                  <div key={k.label} className="card">
                    <p className="section-label">{k.label}</p>
                    <p className="text-2xl font-semibold text-ink mt-1 truncate">{k.value}</p>
                    <p className="text-xs text-muted mt-0.5">{k.sub}</p>
                  </div>
                ))}
              </div>

              {/* Skills — ranked list with bar */}
              <div className="card">
                <p className="section-label mb-4">Most In-Demand Skills</p>
                <div className="flex flex-col gap-3">
                  {Object.entries(trending.all_time_top_skills || {}).slice(0, 10).map(([skill, count], i) => {
                    const max = Object.values(trending.all_time_top_skills)[0] || 1
                    const pct = Math.round((count / max) * 100)
                    return (
                      <div key={skill} className="flex items-center gap-3">
                        <span className="text-xs text-muted w-5 text-right shrink-0">{i + 1}</span>
                        <span className="text-sm font-medium text-ink w-24 shrink-0">{skill}</span>
                        <div className="flex-1 h-2 bg-border rounded-full overflow-hidden">
                          <div className="h-full bg-amber rounded-full transition-all"
                               style={{ width: `${pct}%` }} />
                        </div>
                        <span className="text-xs text-muted w-10 text-right shrink-0">
                          {count} jobs
                        </span>
                      </div>
                    )
                  })}
                </div>
              </div>

              {/* Fastest growing — cards */}
              <div>
                <p className="section-label mb-3">Fastest Growing Roles</p>
                {trending.fastest_growing_roles?.length > 0 ? (
                  <div className="grid grid-cols-2 gap-3">
                    {trending.fastest_growing_roles.map(g => {
                      const pct = g.change_pct
                      const isUp = pct >= 0
                      return (
                        <div key={g.role} className="card flex items-start justify-between gap-3">
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-ink truncate">{g.role}</p>
                            <p className="text-xs text-muted mt-0.5">
                              {g.this_week} this week · {g.last_week} last week
                            </p>
                          </div>
                          <div className={`flex items-center gap-1 shrink-0 px-2 py-0.5 rounded-full text-xs font-semibold
                            ${isUp ? "bg-green-50 text-green-700" : "bg-red-50 text-red-600"}`}>
                            <span>{isUp ? "↑" : "↓"}</span>
                            <span>{Math.abs(pct)}%</span>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                ) : (
                  <div className="card text-center py-8">
                    <p className="text-sm text-muted">
                      Not enough history yet.<br />
                      <span className="text-xs">Run the pipeline over several days to see trends.</span>
                    </p>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <p className="text-sm text-muted text-center py-12">Loading trends…</p>
          )}
        </div>

        {/* JOBS */}
        <div className={`absolute inset-0 overflow-y-auto p-6 ${tab === "Jobs" ? "block" : "hidden"}`}>
          <div className="max-w-3xl mx-auto">
            <JobsTable data={jobsData} />
          </div>
        </div>

        {/* SKILL GAP */}
        <div className={`absolute inset-0 overflow-y-auto p-6 ${tab === "Skill Gap" ? "block" : "hidden"}`}>
          <SkillGap />
        </div>

        {/* MARKET INTELLIGENCE */}
        <div className={`absolute inset-0 overflow-y-auto p-6 ${tab === "Market Intelligence" ? "block" : "hidden"}`}>
          <div className="max-w-3xl mx-auto">
            {insights?.generated_at ? (
              <div className="flex flex-col gap-5">
                <p className="text-xs text-muted">AI analysis · {insights.generated_at}</p>
                <div className="grid grid-cols-2 gap-4">
                  {insights.fastest_growing_roles?.map(g => (
                    <div key={g.role} className="card flex items-center justify-between gap-3">
                      <div>
                        <p className="section-label">Growing role</p>
                        <p className="font-medium text-ink text-sm">{g.role}</p>
                        <p className="text-xs text-muted">{g.city}</p>
                      </div>
                      <span className="text-amber font-semibold shrink-0">+{g.change_pct}%</span>
                    </div>
                  ))}
                </div>
                {insights.notable_shifts?.length > 0 && (
                  <div>
                    <p className="section-label mb-2">Notable Shifts</p>
                    <div className="flex flex-col gap-2">
                      {insights.notable_shifts.map((s, i) => (
                        <div key={i} className="bg-amber-pale border-l-2 border-amber
                                                 text-sm text-ink px-4 py-3 rounded-r-lg">
                          {s}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {insights.most_in_demand_skills?.length > 0 && (
                  <div>
                    <p className="section-label mb-2">Most In-Demand Skills</p>
                    <div className="flex flex-wrap gap-2">
                      {insights.most_in_demand_skills.map(s => (
                        <span key={s} className="tag text-sm px-3 py-1">{s}</span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex flex-col gap-5">
                <p className="text-sm text-muted">
                  Full AI insights appear here after the pipeline runs with Groq.
                  Showing live data below.
                </p>
                {trending && (
                  <div className="card">
                    <p className="section-label mb-3">All-time top skills</p>
                    <div className="flex flex-wrap gap-2">
                      {Object.keys(trending.all_time_top_skills || {}).map(s => (
                        <span key={s} className="tag">{s}</span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  )
}
