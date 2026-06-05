import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

// StrictMode removed — it double-invokes effects in dev, which breaks
// imperative window.Plotly calls (purge runs on first cleanup, leaving
// nothing for the second mount → white page)
createRoot(document.getElementById('root')).render(<App />)
