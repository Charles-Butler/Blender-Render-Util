import { useState } from 'react'
import './Navigation.css'

function Navigation({ currentPage, onNavigate, renderStatus, canNavigate }) {
  const [isOpen, setIsOpen] = useState(false)

  const pages = [
    { id: 'configure', label: 'Configure', icon: '⚙️' },
    { id: 'monitor', label: 'Monitor', icon: '📊' }
  ]

  const getPageStatus = (pageId) => {
    if (pageId === currentPage) return 'active'
    if (!canNavigate) return 'disabled'
    return ''
  }

  const handleNavigate = (pageId) => {
    if (canNavigate) {
      onNavigate(pageId)
      setIsOpen(false) // Close mobile menu after navigation
    }
  }

  const toggleMenu = () => {
    setIsOpen(!isOpen)
  }

  return (
    <>
      {/* Sidebar Navigation */}
      <nav className={`navigation ${isOpen ? 'open' : ''}`}>
        {/* Mobile Side Tab Toggle */}
        <button className="side-tab-toggle" onClick={toggleMenu} aria-label="Toggle menu">
          <span className="tab-arrow">{isOpen ? '<' : '>'}</span>
        </button>

        {/* Overlay for mobile */}
        <div className="nav-overlay" onClick={() => setIsOpen(false)}></div>

        <div className="nav-content">
          {/* Brand */}
          <div className="nav-brand">
            <div className="brand-icon">🎬</div>
            <h1 className="brand-title">Blender Render Monitor</h1>
          </div>

          {/* Navigation Items */}
          <div className="nav-items">
            {pages.map(page => (
              <button
                key={page.id}
                className={`nav-item ${getPageStatus(page.id)}`}
                onClick={() => handleNavigate(page.id)}
                disabled={!canNavigate && page.id !== currentPage}
              >
                <span className="nav-icon">{page.icon}</span>
                <span className="nav-label">{page.label}</span>
              </button>
            ))}
          </div>

          {/* Status Indicator */}
          {renderStatus && (
            <div className="nav-status">
              <div className="status-label">Status</div>
              <div className={`status-indicator ${renderStatus}`}>
                <span className="status-dot"></span>
                <span className="status-text">
                  {renderStatus === 'idle' && 'Idle'}
                  {renderStatus === 'rendering' && 'Rendering'}
                  {renderStatus === 'completed' && 'Completed'}
                  {renderStatus === 'error' && 'Error'}
                </span>
              </div>
            </div>
          )}

          {/* Version Footer */}
          <div className="nav-footer">
            <div className="version-info">v3.1.0</div>
          </div>
        </div>
      </nav>
    </>
  )
}

export default Navigation
