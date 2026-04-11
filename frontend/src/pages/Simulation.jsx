import { useState } from 'react'
import './Simulation.css'

const scenarios = [
  { id: 'ukraine', name: 'Ukraine Crisis', description: 'Current Russia-Ukraine conflict simulation' },
  { id: 'middle_east', name: 'Middle East', description: 'Iran-Saudi Arabia regional dynamics' },
  { id: 'south_china', name: 'South China Sea', description: 'China-Taiwan-US naval tensions' },
]

const personalities = ['Aggressor', 'Pacifist', 'Tit-for-Tat', 'Neutral', 'Grudger']

const scenariosData = {
  ukraine: { agents: 5, steps: 100 },
  middle_east: { agents: 8, steps: 50 },
  south_china: { agents: 6, steps: 75 },
}

function Simulation() {
  const [selectedScenario, setSelectedScenario] = useState(null)
  const [running, setRunning] = useState(false)
  const [step, setStep] = useState(0)

  const startSimulation = (scenarioId) => {
    setSelectedScenario(scenarioId)
    setRunning(true)
    setStep(0)
  }

  const stopSimulation = () => {
    setRunning(false)
  }

  return (
    <div className="simulation">
      <header className="page-header">
        <h1>Simulation Control</h1>
        <p className="subtitle">Run agent-based geopolitical simulations</p>
      </header>

      <div className="scenario-grid">
        {scenarios.map(s => (
          <div key={s.id} className="scenario-card">
            <h3>{s.name}</h3>
            <p>{s.description}</p>
            <div className="scenario-meta">
              <span>Agents: {scenariosData[s.id].agents}</span>
              <span>Steps: {scenariosData[s.id].steps}</span>
            </div>
            {selectedScenario === s.id ? (
              <div className="sim-controls">
                <div className="sim-progress">
                  <div className="progress-bar">
                    <div className="progress-fill" style={{ width: `${(step / scenariosData[s.id].steps) * 100}%` }} />
                  </div>
                  <span>Step {step} / {scenariosData[s.id].steps}</span>
                </div>
                <button className="btn btn-stop" onClick={stopSimulation}>Stop</button>
              </div>
            ) : (
              <button className="btn btn-start" onClick={() => startSimulation(s.id)}>Start</button>
            )}
          </div>
        ))}
      </div>

      <div className="agent-config">
        <h2>Agent Personalities</h2>
        <div className="personality-list">
          {personalities.map(p => (
            <div key={p} className="personality-chip">{p}</div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default Simulation
