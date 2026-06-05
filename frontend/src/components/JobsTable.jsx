import { useState } from "react"

const DOMAIN_LABELS = {
  "linkedin":   "LinkedIn",
  "jobstreet":  "JobStreet",
  "indeed":     "Indeed",
  "kalibrr":    "Kalibrr",
  "glassdoor":  "Glassdoor",
  "jobsdb":     "JobsDB",
  "mynimo":     "Mynimo",
}

function applyLabel(link) {
  try {
    const host = new URL(link.url).hostname.replace(/^www\./, "")
    const match = Object.keys(DOMAIN_LABELS).find(k => host.includes(k))
    if (match) return `Apply on ${DOMAIN_LABELS[match]}`
  } catch { /* invalid URL */ }
  if (link.source === "dole")     return "Apply on DOLE"
  if (link.source === "kalibrr")  return "Apply on Kalibrr"
  return "Apply Now"
}

function JobRow({ job }) {
  const [open, setOpen] = useState(false)
  const remote = job.remote ? "Remote" : "Onsite"
  const salary = job.salary_min
    ? `₱${job.salary_min.toLocaleString()}–₱${job.salary_max?.toLocaleString()}`
    : null

  return (
    <div className="border border-border rounded-lg overflow-hidden bg-white
                    hover:shadow-md hover:-translate-y-0.5 transition-all duration-200">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-start justify-between gap-3 px-4 py-3
                   hover:bg-cream-dark transition-colors text-left cursor-pointer"
      >
        <div className="flex-1 min-w-0">
          <p className="font-medium text-ink text-sm truncate">{job.title}</p>
          <p className="text-xs text-muted mt-0.5">{job.company} · {job.city}</p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className={`text-xs px-2 py-0.5 rounded-full font-medium
            ${job.remote ? "bg-green-50 text-green-700" : "bg-stone-100 text-stone-600"}`}>
            {remote}
          </span>
          {salary && <span className="text-xs text-muted hidden sm:block">{salary}</span>}
          <svg className={`w-4 h-4 text-muted transition-transform ${open ? "rotate-180" : ""}`}
               fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
            <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      {open && (
        <div className="border-t border-border px-4 py-3 bg-cream flex flex-col gap-3">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            <div>
              <p className="text-muted mb-0.5">Location</p>
              <p className="font-medium text-ink">{job.city} · {job.region}</p>
            </div>
            <div>
              <p className="text-muted mb-0.5">Experience</p>
              <p className="font-medium text-ink capitalize">{job.experience_level || "—"}</p>
            </div>
            <div>
              <p className="text-muted mb-0.5">Source</p>
              <p className="font-medium text-ink capitalize">{job.source}</p>
            </div>
            {salary && (
              <div>
                <p className="text-muted mb-0.5">Salary</p>
                <p className="font-medium text-amber">{salary}/mo</p>
              </div>
            )}
          </div>

          {job.skills?.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {job.skills.map(s => <span key={s} className="tag text-xs">{s}</span>)}
            </div>
          )}

          {job.apply_urls?.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {job.apply_urls.map((link, i) => (
                <a key={i} href={link.url} target="_blank" rel="noreferrer"
                   className="btn-primary self-start">
                  {applyLabel(link)}
                </a>
              ))}
            </div>
          ) : job.apply_url ? (
            <a href={job.apply_url} target="_blank" rel="noreferrer"
               className="btn-primary self-start">
              Apply now
            </a>
          ) : null}
        </div>
      )}
    </div>
  )
}

export default function JobsTable({ data }) {
  if (!data) return <p className="text-sm text-muted">Loading…</p>
  const { total, results = [] } = data

  if (!results.length) return (
    <p className="text-sm text-muted py-8 text-center">No jobs match the current filters.</p>
  )

  return (
    <div className="flex flex-col gap-2">
      <p className="text-xs text-muted mb-1">{total?.toLocaleString()} jobs found</p>
      {results.map(job => <JobRow key={job.job_id} job={job} />)}
    </div>
  )
}
