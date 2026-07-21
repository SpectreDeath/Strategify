import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Simulation from './pages/Simulation'
import Map from './pages/Map'
import Analysis from './pages/Analysis'
import XAI from './pages/XAI'
import Navbar from './components/Navbar'
import './App.css'

function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <Navbar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/simulation" element={<Simulation />} />
            <Route path="/map" element={<Map />} />
            <Route path="/analysis" element={<Analysis />} />
            <Route path="/xai" element={<XAI />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}

export default App
