import { Link, useLocation } from "react-router-dom"

export default function Header({ lastUpdated, totalJobs }) {
  const { pathname } = useLocation()
  const isDashboard = pathname === "/dashboard"

  return (
    <header className="sticky top-0 z-50 bg-cream border-b border-border">
      <div className="max-w-screen-xl mx-auto px-6 h-14 flex items-center justify-between">

        {/* Logo */}
        <Link to="/" className="flex items-center gap-2 group">
          <div className="w-7 h-7 rounded-md bg-amber flex items-center justify-center">
            <svg viewBox="0 0 24 24" fill="none" className="w-4 h-4 text-white" stroke="currentColor" strokeWidth="2.5">
              <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z" />
              <circle cx="12" cy="9" r="2.5" />
            </svg>
          </div>
          <span className="font-semibold text-ink text-sm tracking-tight">
            HireMap <span className="text-amber">PH</span>
          </span>
        </Link>

        {/* Nav */}
        <nav className="flex items-center gap-1">
          <Link
            to="/"
            className={`px-3 py-1.5 rounded-md text-sm transition-colors ${
              !isDashboard ? "text-ink font-medium" : "text-muted hover:text-ink"
            }`}
          >
            Home
          </Link>
          <Link
            to="/dashboard"
            className={`px-3 py-1.5 rounded-md text-sm transition-colors ${
              isDashboard ? "text-ink font-medium" : "text-muted hover:text-ink"
            }`}
          >
            Dashboard
          </Link>
        </nav>

        {/* Status pill */}
        {isDashboard && totalJobs > 0 && (
          <div className="flex items-center gap-2 text-xs text-muted">
            <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
            <span>{totalJobs.toLocaleString()} listings · updated {lastUpdated}</span>
          </div>
        )}
        {!isDashboard && (
          <Link to="/dashboard" className="btn-primary text-xs px-4 py-1.5">
            Explore the map
          </Link>
        )}
      </div>
    </header>
  )
}
