import { NavLink } from 'react-router-dom'
import './Navbar.css'

const navItems = [
  { path: '/', label: 'Dashboard' },
  { path: '/simulation', label: 'Simulation' },
  { path: '/map', label: 'Map' },
  { path: '/analysis', label: 'Analysis' },
]

function Navbar() {
  return (
    <nav className="navbar">
      <div className="nav-brand">
        <span className="brand-icon">🌍</span>
        <span className="brand-text">Strategify</span>
      </div>
      <div className="nav-links">
        {navItems.map(item => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          >
            {item.label}
          </NavLink>
        ))}
      </div>
    </nav>
  )
}

export default Navbar
