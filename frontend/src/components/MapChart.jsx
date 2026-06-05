import { useEffect, useRef, useState, useCallback } from "react"

const ALL_REGIONS = [
  "NCR","Region I","Region II","Region III","Region IV-A","Region IV-B",
  "Region V","Region VI","Region VII","Region VIII","Region IX","Region X",
  "Region XI","Region XII","Region XIII","CAR","BARMM",
]

const AMBER_SCALE = [
  [0,   "#F5ECD7"],
  [0.01,"#FDE68A"],
  [0.3, "#FCD34D"],
  [0.6, "#F59E0B"],
  [0.8, "#D97706"],
  [1,   "#92400E"],
]

async function loadGeoJson() {
  const res = await fetch("/ph_regions_simple.geojson")
  return res.json()
}

export default function MapChart({ mapData = [] }) {
  const wrapRef        = useRef(null)
  const plotRef        = useRef(null)
  const prevData       = useRef([])
  const hoveredCityRef = useRef(null)   // tracks hovered city for native click handler
  const [geojson,  setGeojson]  = useState(null)
  const [height,   setHeight]   = useState(500)
  const [zoomed,   setZoomed]   = useState(false)

  useEffect(() => { loadGeoJson().then(setGeojson) }, [])

  useEffect(() => {
    const el = wrapRef.current
    if (!el) return
    const measure = () => {
      const h = el.clientHeight
      if (h > 100) setHeight(h)
    }
    measure()
    const ro = new ResizeObserver(measure)
    ro.observe(el)
    return () => ro.disconnect()
  }, [])

  useEffect(() => {
    if (mapData.length > 0) prevData.current = mapData
  }, [mapData])

  useEffect(() => {
    const el = plotRef.current
    if (!el || !geojson || !window.Plotly) return

    const display = mapData.length > 0 ? mapData : prevData.current
    if (!display.length) return

    const regionJobs  = {}
    const regionHover = {}
    for (const d of display) {
      const r = d.region
      if (!r || ["Remote","Nationwide","Unknown"].includes(r)) continue
      regionJobs[r]  = (regionJobs[r]  || 0) + d.job_count
      const roles    = d.top_roles.slice(0,3).join(", ") || "—"
      const skills   = d.top_skills.slice(0,4).join(", ") || "—"
      regionHover[r] = (regionHover[r] || "")
        + `${d.city}: ${d.job_count} jobs<br>`
        + (regionHover[r] ? "" : `Roles: ${roles}<br>Skills: ${skills}`)
    }

    const maxCount = Math.max(...Object.values(regionJobs), 1)
    const ids    = ALL_REGIONS
    const counts = ALL_REGIONS.map(id => regionJobs[id] || 0)
    const hover  = ALL_REGIONS.map(id =>
      regionJobs[id]
        ? `<b>${id}</b><br>${regionHover[id]}`
        : `<b>${id}</b><br>No listings`
    )

    const cities = display.filter(d =>
      d.lat && d.lng && !["Remote","Nationwide","Unknown"].includes(d.region)
    )

    const sqrtMax    = Math.sqrt(maxCount) || 1
    const bubbleSize = cities.map(d => 8 + (Math.sqrt(d.job_count) / sqrtMax) * 14)

    const sorted       = [...cities].sort((a, b) => b.job_count - a.job_count)
    const topCityNames = new Set(sorted.slice(0, 3).map(d => d.city))
    const cityLabels   = cities.map(d => topCityNames.has(d.city) ? d.city : "")

    window.Plotly.newPlot(el, [
      {
        type: "choropleth",
        geojson,
        locations: ids,
        z: counts,
        featureidkey: "id",
        colorscale: AMBER_SCALE,
        zmin: 0,
        zmax: maxCount,
        colorbar: {
          title: "Jobs",
          thickness: 10, len: 0.55, x: 1.01,
          bgcolor: "rgba(250,246,240,0.9)",
          bordercolor: "#E0D9CC", borderwidth: 1,
          tickfont: { color: "#2C2416", size: 10 },
          titlefont: { color: "#2C2416", size: 11 },
        },
        hovertemplate: "%{customdata}<extra></extra>",
        customdata: hover,
        marker: { line: { color: "#B8A898", width: 0.8 } },
      },
      {
        type: "scattergeo",
        lat: cities.map(d => d.lat),
        lon: cities.map(d => d.lng),
        mode: "markers+text",
        text: cityLabels,
        textposition: "top center",
        textfont: { size: 9, color: "#2C2416" },
        marker: {
          size: bubbleSize,
          color: cities.map(d => d.job_count),
          colorscale: AMBER_SCALE, cmin: 0, cmax: maxCount,
          showscale: false, opacity: 0.75,
          line: { width: 1, color: "#92400E" },
        },
        hovertemplate: "%{customdata}<extra></extra>",
        customdata: cities.map(d =>
          `<b>${d.city}</b><br>${d.job_count} jobs<br>` +
          (d.top_skills.length ? `Skills: ${d.top_skills.slice(0,4).join(", ")}` : "")
        ),
      },
    ], {
      geo: {
        visible: false,
        fitbounds: "locations",
        resolution: 50,
        bgcolor: "#FAFAF8",
        showframe: false,
        showcoastlines: false,
      },
      margin: { l: 0, r: 44, t: 0, b: 0 },
      paper_bgcolor: "#FAFAF8",
      height,
    }, { displayModeBar: false, responsive: true, scrollZoom: true })
    .then((gd) => {
      // Track hovered city in a ref so native DOM event handlers can read it
      gd.on("plotly_hover", (data) => {
        const pt = data.points?.[0]
        hoveredCityRef.current = (pt?.lat != null && pt?.lon != null)
          ? { lat: pt.lat, lon: pt.lon }
          : null
      })
      gd.on("plotly_unhover", () => {
        hoveredCityRef.current = null
      })

      // Native click detection: zoom if mouseup is < 5px from mousedown (not a drag)
      // plotly_click is swallowed by the geo pan handler — native events bypass that
      let mdx = 0, mdy = 0
      const doZoom = () => {
        if (!hoveredCityRef.current) return
        const { lat, lon } = hoveredCityRef.current
        window.Plotly.relayout(el, {
          "geo.fitbounds": false,
          "geo.lataxis.range": [lat - 2, lat + 2],
          "geo.lonaxis.range": [lon - 3, lon + 3],
        })
        setZoomed(true)
      }
      el.addEventListener("mousedown", (e) => { mdx = e.clientX; mdy = e.clientY })
      el.addEventListener("mouseup", (e) => {
        if (Math.abs(e.clientX - mdx) < 5 && Math.abs(e.clientY - mdy) < 5) doZoom()
      })
      // Touch support — touchstart/touchend for mobile tap-to-zoom
      el.addEventListener("touchstart", (e) => {
        if (e.touches.length === 1) { mdx = e.touches[0].clientX; mdy = e.touches[0].clientY }
      }, { passive: true })
      el.addEventListener("touchend", (e) => {
        if (e.changedTouches.length === 1) {
          const dx = Math.abs(e.changedTouches[0].clientX - mdx)
          const dy = Math.abs(e.changedTouches[0].clientY - mdy)
          if (dx < 10 && dy < 10) doZoom()
        }
      })
    })

    return () => { if (el && window.Plotly) window.Plotly.purge(el) }
  }, [geojson, mapData, height])

  const resetZoom = useCallback(() => {
    if (!plotRef.current) return
    window.Plotly.relayout(plotRef.current, { "geo.fitbounds": "locations" })
    setZoomed(false)
  }, [])

  if (!geojson) {
    return (
      <div ref={wrapRef} className="flex items-center justify-center w-full h-full text-muted text-sm">
        Loading map…
      </div>
    )
  }

  return (
    <div ref={wrapRef} style={{ width: "100%", height: "100%", position: "relative" }}>
      <div ref={plotRef} style={{ width: "100%" }} />

      {/* Reset button — top-right corner, visible when zoomed */}
      {zoomed && (
        <button onClick={resetZoom}
                className="absolute top-3 right-3 z-10
                           bg-white border border-border text-ink text-xs font-medium
                           px-3 py-1.5 rounded-lg shadow-md hover:bg-cream-dark
                           active:scale-95 transition-all flex items-center gap-1.5">
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24"
               stroke="currentColor" strokeWidth="2">
            <path d="M3 12a9 9 0 1 0 18 0 9 9 0 0 0-18 0M3 12h4m10 0h4M12 3v4m0 10v4"/>
          </svg>
          Reset view
        </button>
      )}

      {/* Hint — visible when not zoomed */}
      {!zoomed && (
        <div style={{ pointerEvents: "none" }}
             className="absolute bottom-3 left-1/2 -translate-x-1/2 z-10
                        bg-white/80 backdrop-blur-sm border border-border
                        text-xs text-muted px-3 py-1.5 rounded-full whitespace-nowrap">
          Tap a city bubble to zoom in
        </div>
      )}
    </div>
  )
}
