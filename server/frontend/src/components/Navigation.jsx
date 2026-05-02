import { useState } from 'react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faGear, faChartBar, faArrowsRotate, faCaretLeft, faCaretRight, faCircleQuestion } from '@fortawesome/free-solid-svg-icons'
import './Navigation.css'

function Navigation({ currentPage, onNavigate, renderStatus, canNavigate, onHelp }) {
  const [isOpen, setIsOpen] = useState(false)

  const pages = [
    { id: 'configure', label: 'Configure', icon: faGear },
    { id: 'monitor', label: 'Monitor', icon: faChartBar }
  ]

  const getPageStatus = (pageId) => {
    if (pageId === currentPage) return 'active'
    if (!canNavigate) return 'disabled'
    return ''
  }

  const isPageDisabled = (pageId) => {
    return !canNavigate && pageId !== currentPage
  }

  const handleNavigate = (pageId) => {
    if (!isPageDisabled(pageId)) {
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
          <FontAwesomeIcon icon={isOpen ? faCaretLeft : faCaretRight} className="tab-arrow" />
        </button>

        {/* Overlay for mobile */}
        <div className="nav-overlay" onClick={() => setIsOpen(false)}></div>

        <div className="nav-content">
          {/* Brand */}
          <div className="nav-brand">
            <div className="brand-icon">
              <img src="/blender_icon.png" alt="Blender" className="brand-logo" />
            </div>
            <h1 className="brand-title">Blender Render Monitor</h1>
          </div>

          {/* Navigation Items */}
          <div className="nav-items">
            {pages.map(page => (
              <button
                key={page.id}
                className={`nav-item ${getPageStatus(page.id)}`}
                onClick={() => handleNavigate(page.id)}
                disabled={isPageDisabled(page.id)}
                title=""
              >
                <span className="nav-icon">
                  <FontAwesomeIcon icon={page.icon} />
                </span>
                <span className="nav-label">{page.label}</span>
              </button>
            ))}
          </div>

          {/* Status Indicator */}
          {renderStatus && (
            <div className="nav-status">
              <div className="status-label">Status</div>
              <div className={`status-indicator ${renderStatus}`}>
                {renderStatus === 'rendering' ? (
                  <FontAwesomeIcon icon={faArrowsRotate} className="status-icon rotating" />
                ) : (
                  <span className="status-dot"></span>
                )}
                <span className="status-text">
                  {renderStatus === 'idle' && 'Idle'}
                  {renderStatus === 'rendering' && (
                    <>
                      Rendering<span className="pulse-dot"></span>
                    </>
                  )}
                  {renderStatus === 'completed' && 'Completed'}
                  {renderStatus === 'error' && 'Error'}
                </span>
              </div>
            </div>
          )}

          {/* Version Footer */}
          <div className="nav-footer">
            <button
              className={`help-pill ${currentPage === 'help' ? 'active' : ''}`}
              onClick={onHelp}
            >
              <FontAwesomeIcon icon={faCircleQuestion} className="help-pill-icon" />
              <span>Help & Support</span>
            </button>
            <div className="version-info">v5.4.1</div>
          </div>
        </div>
      </nav>
    </>
  )
}

export default Navigation
