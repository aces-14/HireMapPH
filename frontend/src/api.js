const BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000"

async function get(path, params = {}) {
  const url = new URL(BASE + path)
  Object.entries(params).forEach(([k, v]) => {
    if (v !== null && v !== undefined && v !== "") url.searchParams.set(k, v)
  })
  const res = await fetch(url)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json()
}

export const api = {
  health:   ()       => get("/health"),
  mapData:  (p = {}) => get("/map-data", p),
  jobs:     (p = {}) => get("/jobs", p),
  trending: ()       => get("/trending"),
  salary:   (p = {}) => get("/salary", p),
  insights: ()       => get("/insights"),
  skillGap: (p = {}) => get("/skill-gap", p),
}
