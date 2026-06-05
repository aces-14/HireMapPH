/**
 * Thin wrapper around the global Plotly object loaded via CDN.
 * Avoids importing plotly.js-dist-min, which stalls Vite's optimizer.
 */
import { useEffect, useRef } from "react"

export default function PlotlyChart({ data, layout, config, style }) {
  const ref = useRef(null)

  useEffect(() => {
    const el = ref.current
    if (!el || !window.Plotly) return
    window.Plotly.newPlot(el, data, {
      paper_bgcolor: "#FAFAF8",
      plot_bgcolor:  "#FAFAF8",
      font: { color: "#2C2416", size: 11 },
      margin: { l: 10, r: 10, t: 10, b: 10 },
      ...layout,
    }, { displayModeBar: false, responsive: true, ...config })

    // Capture el before cleanup so React's nulling of ref.current doesn't break purge
    return () => { if (el && window.Plotly) window.Plotly.purge(el) }
  }, [data, layout, config])

  return <div ref={ref} style={{ width: "100%", ...style }} />
}
