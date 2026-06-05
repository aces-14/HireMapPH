export default function MarketIntel({ insights, trending, topCities = [] }) {
  const hasAI  = insights?.generated_at
  const skills = hasAI
    ? insights.most_in_demand_skills?.slice(0, 8)
    : Object.keys(trending?.all_time_top_skills || {}).slice(0, 8)
  const growing = hasAI
    ? insights.fastest_growing_roles?.slice(0, 3)
    : trending?.fastest_growing_roles?.slice(0, 3) || []
  const shifts = hasAI ? insights.notable_shifts?.slice(0, 2) : []

  return (
    <aside className="flex flex-col gap-5 h-full">

      {/* Top cities — moved here from bottom strip */}
      {topCities.length > 0 && (
        <div>
          <p className="section-label mb-2">Top Cities</p>
          <div className="flex flex-col gap-1.5">
            {topCities.map((c, i) => {
              const max = topCities[0]?.job_count || 1
              const pct = Math.round((c.job_count / max) * 100)
              return (
                <div key={c.city}
                     className="flex items-center gap-2 rounded-md px-1 py-0.5
                                hover:bg-cream-dark transition-colors duration-150 cursor-default">
                  <span className="text-xs text-muted w-4 text-right">{i+1}</span>
                  <div className="flex-1">
                    <div className="flex justify-between mb-0.5">
                      <span className="text-xs font-medium text-ink">{c.city}</span>
                      <span className="text-xs text-muted">{c.job_count}</span>
                    </div>
                    <div className="h-1 bg-border rounded-full overflow-hidden">
                      <div
                        className="h-full bg-amber rounded-full transition-all duration-700 ease-out"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Notable shifts */}
      {shifts.length > 0 && (
        <div>
          <p className="section-label mb-2">Shifts</p>
          <div className="flex flex-col gap-1.5">
            {shifts.map((s, i) => (
              <div key={i} className="bg-amber-pale border-l-2 border-amber
                                      text-xs text-ink px-2.5 py-2 rounded-r-md">
                {s}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Growing roles */}
      {growing.length > 0 && (
        <div>
          <p className="section-label mb-2">Fastest Growing</p>
          <div className="flex flex-col gap-1.5">
            {growing.map((g, i) => (
              <div key={i} className="card !p-2.5 flex justify-between items-start gap-2
                                    hover:shadow-sm hover:-translate-y-0.5 transition-all duration-200">
                <span className="text-xs text-ink font-medium leading-snug line-clamp-2 flex-1">
                  {g.role}
                </span>
                {g.change_pct != null && (
                  <span className="text-xs font-semibold text-amber shrink-0 bg-amber-pale
                                   px-1.5 py-0.5 rounded">
                    +{g.change_pct}%
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* In-demand skills */}
      {skills.length > 0 && (
        <div>
          <p className="section-label mb-2">In-Demand Skills</p>
          <div className="flex flex-wrap gap-1.5">
            {skills.map(s => <span key={s} className="tag">{s}</span>)}
          </div>
        </div>
      )}

      {/* This week count if no AI */}
      {!hasAI && trending?.this_week && (
        <div>
          <p className="section-label mb-1">This Week</p>
          <div className="card !p-3">
            <p className="text-2xl font-semibold text-ink leading-none">
              {trending.this_week.new_jobs}
            </p>
            <p className="text-xs text-muted mt-1">new listings</p>
          </div>
        </div>
      )}

      {/* Caption */}
      <p className="text-xs text-muted mt-auto pt-2 border-t border-border">
        {hasAI ? `AI analysis · ${insights.generated_at}` : "Live data · AI pending"}
      </p>
    </aside>
  )
}
