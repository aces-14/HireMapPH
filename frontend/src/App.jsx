import { BrowserRouter, Routes, Route } from "react-router-dom"
import { Analytics } from "@vercel/analytics/react"
import Landing from "./pages/Landing"
import Dashboard from "./pages/Dashboard"

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/dashboard" element={<Dashboard />} />
      </Routes>
      <Analytics />
    </BrowserRouter>
  )
}
