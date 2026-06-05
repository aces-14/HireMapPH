import { useState } from "react"
import { api } from "../api"

const DOMAIN_LABELS = {
  linkedin: "LinkedIn", jobstreet: "JobStreet", indeed: "Indeed",
  kalibrr: "Kalibrr", glassdoor: "Glassdoor", jobsdb: "JobsDB", mynimo: "Mynimo",
}
function applyLabel(link) {
  try {
    const host = new URL(link.url).hostname.replace(/^www\./, "")
    const match = Object.keys(DOMAIN_LABELS).find(k => host.includes(k))
    if (match) return DOMAIN_LABELS[match]
  } catch {}
  if (link.source === "dole")    return "DOLE"
  if (link.source === "kalibrr") return "Kalibrr"
  return "Apply"
}

function JobRef({ job }) {
  const urls = job.apply_urls?.length
    ? job.apply_urls
    : job.apply_url ? [{ url: job.apply_url, source: job.source }] : []
  return (
    <div className="flex items-center justify-between gap-2 py-2.5
                    border-b border-border last:border-0">
      <div className="flex-1 min-w-0">
        <p className="text-xs font-medium text-ink truncate">{job.title}</p>
        <p className="text-xs text-muted truncate">
          {job.company}{job.city ? ` · ${job.city}` : ""}{job.remote ? " · Remote" : ""}
        </p>
      </div>
      <div className="flex gap-1 shrink-0">
        {urls.slice(0, 2).map((link, i) => (
          <a key={i} href={link.url} target="_blank" rel="noopener noreferrer"
             className="text-xs font-medium text-amber border border-amber-light
                        bg-amber-pale px-2 py-0.5 rounded-full hover:bg-amber
                        hover:text-white transition-colors whitespace-nowrap">
            {applyLabel(link)}
          </a>
        ))}
      </div>
    </div>
  )
}

function MatchBar({ matched, total }) {
  const pct   = total === 0 ? 0 : Math.round((matched / total) * 100)
  const color = pct >= 70 ? "bg-green-500" : pct >= 40 ? "bg-amber" : "bg-red-400"
  const label = pct >= 70 ? "Strong match" : pct >= 40 ? "Partial match" : "Needs work"
  return (
    <div>
      <div className="flex items-baseline justify-between mb-1.5">
        <span className="text-2xl font-semibold text-ink">
          {pct}% <span className="text-xs font-normal text-muted">{label}</span>
        </span>
        <span className="text-xs text-muted">{matched} / {total} skills</span>
      </div>
      <div className="h-2 bg-border rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full transition-all duration-700`}
             style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

export default function SkillGap() {
  const [role,     setRole]     = useState("")
  const [city,     setCity]     = useState("")
  const [myInput,  setMyInput]  = useState("")
  const [roleData, setRoleData] = useState(null)
  const [jobs,     setJobs]     = useState([])
  const [compared, setCompared] = useState(false)
  const [loading,  setLoading]  = useState(false)
  const [error,    setError]    = useState(null)

  async function analyze() {
    if (!role.trim()) return
    setLoading(true)
    setError(null)
    setCompared(false)
    setMyInput("")
    try {
      const params = { role: role.trim(), city: city.trim() || undefined }
      const [skillData, jobsData] = await Promise.all([
        api.skillGap(params),
        api.jobs({ ...params, page_size: 20 }),
      ])
      setRoleData(skillData)
      setJobs(jobsData?.results || [])
    } catch {
      setError("Could not fetch data. Make sure the backend is running.")
    } finally {
      setLoading(false)
    }
  }

  const mySkillsSet = new Set(
    myInput.split(",").map(s => s.trim().toLowerCase()).filter(Boolean)
  )
  const have       = (roleData?.top_skills || []).filter(s =>  mySkillsSet.has(s.skill))
  const missing    = (roleData?.top_skills || []).filter(s => !mySkillsSet.has(s.skill))
  const topLearn   = missing.slice(0, 5)
  const hasResults = roleData && roleData.total_postings > 0
  const matchedJobs = jobs

  return (
    <div className={hasResults ? "grid grid-cols-1 lg:grid-cols-[1fr_1.4fr] gap-5" : "flex items-start justify-center"}>

      {/* ── LEFT: form + comparison results ── */}
      <div className="flex flex-col gap-4">

        <div className="card flex flex-col gap-3">
          {!hasResults && (
            <div>
              <p className="font-semibold text-ink">Skill Gap Analyzer</p>
              <p className="text-xs text-muted mt-0.5">
                See what Philippine employers ask for — then compare your own skills.
              </p>
            </div>
          )}

          <div className="grid grid-cols-2 gap-2">
            <div className="flex flex-col gap-1">
              <label className="section-label">Target role</label>
              <input
                className="border border-border rounded-lg px-3 py-1.5 text-sm text-ink
                           placeholder:text-muted bg-cream focus:outline-none focus:border-amber"
                placeholder="e.g. Data Analyst"
                value={role}
                onChange={e => setRole(e.target.value)}
                onKeyDown={e => e.key === "Enter" && analyze()}
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="section-label">
                City <span className="font-normal text-muted">(optional)</span>
              </label>
              <input
                className="border border-border rounded-lg px-3 py-1.5 text-sm text-ink
                           placeholder:text-muted bg-cream focus:outline-none focus:border-amber"
                placeholder="e.g. Manila"
                value={city}
                onChange={e => setCity(e.target.value)}
                onKeyDown={e => e.key === "Enter" && analyze()}
              />
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              className="btn-primary self-start px-5 py-1.5 text-sm
                         disabled:opacity-50 disabled:cursor-not-allowed"
              onClick={analyze}
              disabled={loading || !role.trim()}
            >
              {loading ? "Analyzing…" : "Analyze →"}
            </button>
            {error && <p className="text-xs text-red-500">{error}</p>}
          </div>
        </div>

        {/* No results */}
        {roleData && roleData.total_postings === 0 && (
          <div className="card text-center py-6">
            <p className="text-sm font-medium text-ink">No postings found</p>
            <p className="text-xs text-muted mt-1">Try a broader search term or remove the city filter.</p>
          </div>
        )}

        {/* Step 2 — enter skills */}
        {hasResults && !compared && (
          <div className="card border-2 border-dashed border-amber-light bg-amber-pale/30 flex flex-col gap-2">
            <p className="text-sm font-semibold text-ink">How do you compare?</p>
            <input
              className="border border-border rounded-lg px-3 py-1.5 text-sm text-ink
                         placeholder:text-muted bg-white focus:outline-none focus:border-amber"
              placeholder="python, sql, excel, react…"
              value={myInput}
              onChange={e => setMyInput(e.target.value)}
              onKeyDown={e => e.key === "Enter" && myInput.trim() && setCompared(true)}
              autoFocus
            />
            <div className="flex items-center justify-between">
              <p className="text-xs text-muted">Comma-separated</p>
              <button
                className="btn-primary px-4 py-1.5 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                onClick={() => setCompared(true)}
                disabled={!myInput.trim()}
              >
                Compare →
              </button>
            </div>
          </div>
        )}

        {/* Comparison results */}
        {compared && mySkillsSet.size > 0 && (
          <>
            <div className="card">
              <p className="section-label mb-2">Your match</p>
              <MatchBar matched={have.length} total={roleData.top_skills.length} />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="card">
                <p className="section-label mb-2" style={{ color: "#16a34a" }}>
                  You have ({have.length})
                </p>
                {have.length === 0
                  ? <p className="text-xs text-muted">None matched top requirements.</p>
                  : <div className="flex flex-wrap gap-1">
                      {have.map(s => (
                        <span key={s.skill}
                              className="inline-flex items-center gap-0.5 bg-green-50 text-green-700
                                         border border-green-200 text-xs font-medium px-2 py-0.5 rounded-full">
                          ✓ {s.skill}
                        </span>
                      ))}
                    </div>
                }
              </div>
              <div className="card">
                <p className="section-label mb-2 text-amber">Missing ({missing.length})</p>
                {missing.length === 0
                  ? <p className="text-xs text-muted">You have all the top skills.</p>
                  : <div className="flex flex-wrap gap-1">
                      {missing.map(s => (
                        <span key={s.skill} className="tag text-xs">{s.skill}</span>
                      ))}
                    </div>
                }
              </div>
            </div>

            {topLearn.length > 0 && (
              <div className="card">
                <p className="section-label mb-3">Top {topLearn.length} to learn next</p>
                <div className="flex flex-col gap-2.5">
                  {topLearn.map((s, i) => (
                    <div key={s.skill} className="flex items-center gap-2">
                      <span className="text-xs text-muted w-4 text-right shrink-0">{i + 1}</span>
                      <span className="text-xs font-medium text-ink w-24 shrink-0">{s.skill}</span>
                      <div className="flex-1 h-1.5 bg-border rounded-full overflow-hidden">
                        <div className="h-full bg-amber rounded-full transition-all duration-700"
                             style={{ width: `${s.pct}%` }} />
                      </div>
                      <span className="text-xs text-muted w-16 text-right shrink-0">
                        {s.pct}% of jobs
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <button
              className="text-xs text-muted hover:text-ink underline self-start"
              onClick={() => { setCompared(false); setMyInput("") }}
            >
              ← Change my skills
            </button>
          </>
        )}
      </div>

      {/* ── RIGHT: required skills + jobs ── */}
      {hasResults && (
        <div className="flex flex-col gap-4">
          <div className="card flex flex-col gap-2">
            <div className="flex items-baseline justify-between">
              <p className="section-label">Required skills</p>
              <p className="text-xs text-muted">
                {roleData.total_postings} postings · {roleData.role}
                {roleData.city !== "All cities" ? ` · ${roleData.city}` : ""}
              </p>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {roleData.top_skills.map(s => (
                <span key={s.skill}
                      className={`text-xs font-medium px-2.5 py-1 rounded-full border transition-colors
                        ${compared && have.find(h => h.skill === s.skill)
                          ? "bg-green-50 text-green-700 border-green-200"
                          : compared && missing.find(m => m.skill === s.skill)
                            ? "bg-amber-pale text-amber border-amber-light"
                            : "tag"
                        }`}
                      title={`${s.pct}% of postings`}>
                  {compared && have.find(h => h.skill === s.skill) ? "✓ " : ""}{s.skill}
                </span>
              ))}
            </div>
            {compared && (
              <p className="text-xs text-muted pt-1">
                <span className="text-green-700 font-medium">Green</span> = you have it ·{" "}
                <span className="text-amber font-medium">Amber</span> = learn this
              </p>
            )}
          </div>

          {matchedJobs.length > 0 && (
            <div className="card flex flex-col flex-1 min-h-0">
              <div className="flex items-center justify-between mb-2">
                <p className="section-label">Matching jobs ({matchedJobs.length})</p>
                <p className="text-xs text-muted">Click to apply</p>
              </div>
              <div className="overflow-y-auto flex-1">
                {matchedJobs.map(j => <JobRef key={j.job_id} job={j} />)}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
