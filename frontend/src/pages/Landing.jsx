import { Link } from "react-router-dom"
import { useApi } from "../hooks/useApi"
import { api } from "../api"

function Logo({ size = 36 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 40 40" fill="none">
      <path d="M20 2L36 11V29L20 38L4 29V11L20 2Z" fill="#D97706" />
      <path
        d="M20 10C16.13 10 13 13.13 13 17C13 22.25 20 30 20 30C20 30 27 22.25 27 17C27 13.13 23.87 10 20 10Z"
        fill="white" opacity="0.95"
      />
      <circle cx="20" cy="17" r="3" fill="#D97706" />
    </svg>
  )
}

export default function Landing() {
  const { data: insights } = useApi(api.insights)
  const { data: health }   = useApi(api.health)

  const hasInsights = insights?.generated_at
  const topSkills   = hasInsights ? insights.most_in_demand_skills?.slice(0, 5) : []
  const topRole     = hasInsights ? insights.fastest_growing_roles?.[0] : null
  const topCity     = hasInsights ? insights.top_hiring_cities?.[0] : null
  const dataDate    = health?.last_updated?.slice(0, 10) ?? null

  return (
    <div className="min-h-screen bg-cream flex flex-col">

      {/* Nav */}
      <nav className="px-4 sm:px-8 py-3 sm:py-4 flex items-center justify-between
                      border-b border-border bg-white shrink-0 sticky top-0 z-20">
        <div className="flex items-center gap-2 sm:gap-3">
          <Logo size={32} />
          <div>
            <p className="font-semibold text-ink text-sm sm:text-base leading-tight tracking-tight">
              HireMap <span className="text-amber">PH</span>
            </p>
            <p className="text-xs text-muted leading-none hidden sm:block">Philippine job intelligence</p>
          </div>
        </div>
        <Link to="/dashboard" className="btn-primary text-xs sm:text-sm px-3 sm:px-5 py-1.5 sm:py-2">
          Open Dashboard
        </Link>
      </nav>

      {/* Body */}
      <div className="flex-1 flex flex-col items-center justify-center
                      px-4 sm:px-8 gap-4 sm:gap-5 py-8 sm:py-12">

        {/* Live badge */}
        <div className="inline-flex items-center gap-2 bg-amber-pale border border-amber-light
                        rounded-full px-3 py-1 text-xs text-amber font-medium">
          <span className="w-1.5 h-1.5 rounded-full bg-amber animate-pulse" />
          Live · {health?.total_active_jobs?.toLocaleString() ?? "—"} listings
          {dataDate && <span className="opacity-60 hidden sm:inline"> · {dataDate}</span>}
        </div>

        {/* Hero */}
        <div className="text-center max-w-xl px-2">
          <h1 className="font-display text-4xl sm:text-5xl text-ink leading-[1.1] mb-2">
            See where the jobs are<br />
            <em className="text-amber not-italic">in the Philippines.</em>
          </h1>
          <p className="text-muted text-sm leading-relaxed">
            Real-time job market intelligence — map, trends, skill gaps, all in one place.
          </p>
        </div>

        {/* CTA */}
        <Link to="/dashboard"
              className="btn-primary px-6 sm:px-8 py-2.5 sm:py-3 text-sm sm:text-base rounded-xl shadow-sm">
          Explore the map →
        </Link>

        {/* How it works */}
        <div className="w-full max-w-2xl">
          <p className="section-label text-center mb-3">How it works</p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {[
              { n: "1", title: "Collect", body: "Daily scrape from DOLE, Kalibrr, and JSearch" },
              { n: "2", title: "Map",     body: "Geocoded by city and region across the PH" },
              { n: "3", title: "Analyze", body: "AI-powered insights on trends and skills" },
            ].map(s => (
              <div key={s.n} className="bg-white border border-border rounded-xl p-4 flex items-start gap-3">
                <div className="w-6 h-6 rounded-full bg-amber flex items-center justify-center
                                text-xs font-bold text-white shrink-0 mt-0.5">
                  {s.n}
                </div>
                <div>
                  <p className="font-semibold text-ink text-sm">{s.title}</p>
                  <p className="text-xs text-muted leading-relaxed">{s.body}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Today's highlights — only when pipeline has run */}
        {hasInsights && (
          <div className="w-full max-w-2xl">
            <p className="section-label text-center mb-3">Today's highlights</p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {topRole && (
                <div className="bg-white border border-border rounded-xl p-4">
                  <p className="section-label mb-1">Top role</p>
                  <p className="font-semibold text-ink text-sm leading-snug">{topRole.role}</p>
                  {topRole.city && <p className="text-xs text-muted mt-1">{topRole.city}</p>}
                </div>
              )}
              {topCity && (
                <div className="bg-white border border-border rounded-xl p-4">
                  <p className="section-label mb-1">Top city</p>
                  <p className="font-semibold text-ink text-sm">{topCity.city}</p>
                  <p className="text-xs text-muted mt-1">{topCity.count} active listings</p>
                </div>
              )}
              {topSkills.length > 0 && (
                <div className="bg-white border border-border rounded-xl p-4">
                  <p className="section-label mb-2">In demand</p>
                  <div className="flex flex-wrap gap-1">
                    {topSkills.map(s => <span key={s} className="tag text-xs">{s}</span>)}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

      </div>

      {/* Footer */}
      <div className="px-4 sm:px-8 py-3 border-t border-border text-center text-xs text-muted shrink-0">
        Data: DOLE Phil-JobNet · Kalibrr · JSearch · Portfolio project
      </div>
    </div>
  )
}
