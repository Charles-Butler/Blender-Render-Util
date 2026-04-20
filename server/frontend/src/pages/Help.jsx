import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faCircleQuestion,
  faTriangleExclamation,
  faClockRotateLeft,
  faEnvelope,
  faChevronDown,
  faChevronUp,
  faArrowUpRightFromSquare,
  faCheckCircle,
  faBug
} from '@fortawesome/free-solid-svg-icons'
import { useState } from 'react'
import './Help.css'

const CHANGELOG = [
  {
    version: '5.2.1',
    date: '2026-04-19',
    sections: {
      Fixed: [
        'Server restart no longer shows "Frame 0" and blank statistics on the Monitor page',
        'monitor.py now greps Fra: lines on startup to restore current frame, frame time, and avg frame time for the active batch'
      ]
    }
  },
  {
    version: '5.2.0',
    date: '2026-04-18',
    sections: {
      Added: [
        'PyInstaller bundle — produces native RenderManager.app for macOS',
        'app/build.sh — single command builds the full app',
        'Persistent config storage in ~/Library/Application Support/RenderManager/'
      ],
      Fixed: [
        'Render script path now resolves correctly inside .app bundle'
      ]
    }
  },
  {
    version: '5.1.0',
    date: '2026-04-18',
    sections: {
      Added: [
        'Native desktop app launcher via PyWebView — no browser window required',
        'Accepts --blend-file CLI arg from Blender add-on'
      ]
    }
  },
  {
    version: '5.0.0',
    date: '2026-04-17',
    sections: {
      Changed: [
        'FastAPI now serves the pre-built React frontend directly — single server, no Vite dev server at runtime',
        'All API URLs updated to relative paths (/api/...)'
      ]
    }
  }
]

const TROUBLESHOOTING = [
  {
    question: 'Monitor shows "Frame 0" and blank statistics after restarting the server',
    answer: 'The server reads the log file on startup and restores state. Make sure you are running v5.2.1 or later. If the issue persists, check that the log file path in config.json is still valid.'
  },
  {
    question: '"No batch currently rendering" after server restart',
    answer: 'The server parses "Now Rendering" and "Finished" lines from the log to reconstruct batch state. If the log file was moved or deleted, restart the render from the Configure page.'
  },
  {
    question: 'Frontend still shows an old version number',
    answer: 'The React frontend is a static build. After any source change you must run npm run build inside server/frontend/ for the update to take effect. The server serves from the dist/ folder.'
  },
  {
    question: 'Port 8081 already in use on startup',
    answer: 'Another instance of the server is running. Kill it with: pkill -f "python3 app.py" or find the PID with lsof -i :8081 and kill it manually.'
  },
  {
    question: 'Blender not found error when starting a render',
    answer: 'Open the Configure page and verify the Blender executable path. The default is /Applications/Blender.app/Contents/MacOS/Blender. Update it to match your installation.'
  },
  {
    question: 'Elapsed time shows a large negative number',
    answer: 'This can happen if the render state from a previous session was not cleared. Click Cancel Job on the Configure page and start a fresh render.'
  },
  {
    question: 'Overall progress shows 100% before the render starts',
    answer: 'Stale state from a prior render session. Cancel the current job on the Configure page to reset, then reconfigure and start a new render.'
  }
]

function AccordionItem({ question, answer }) {
  const [open, setOpen] = useState(false)
  return (
    <div className={`accordion-item ${open ? 'open' : ''}`}>
      <button className="accordion-header" onClick={() => setOpen(!open)}>
        <span className="accordion-question">{question}</span>
        <FontAwesomeIcon icon={open ? faChevronUp : faChevronDown} className="accordion-icon" />
      </button>
      {open && <div className="accordion-body">{answer}</div>}
    </div>
  )
}

function Help() {
  return (
    <div className="help-page">
      <div className="help-header">
        <FontAwesomeIcon icon={faCircleQuestion} className="help-header-icon" />
        <div>
          <h1 className="help-title">Help & Support</h1>
          <p className="help-subtitle">Troubleshooting, changelog, and contact</p>
        </div>
      </div>

      {/* Troubleshooting */}
      <section className="help-section">
        <div className="section-heading">
          <FontAwesomeIcon icon={faTriangleExclamation} />
          <h2>Troubleshooting</h2>
        </div>
        <div className="accordion">
          {TROUBLESHOOTING.map((item, i) => (
            <AccordionItem key={i} question={item.question} answer={item.answer} />
          ))}
        </div>
      </section>

      {/* Changelog */}
      <section className="help-section">
        <div className="section-heading">
          <FontAwesomeIcon icon={faClockRotateLeft} />
          <h2>Changelog</h2>
        </div>
        <div className="changelog">
          {CHANGELOG.map(entry => (
            <div key={entry.version} className="changelog-entry">
              <div className="changelog-header">
                <span className="changelog-version">v{entry.version}</span>
                <span className="changelog-date">{entry.date}</span>
              </div>
              {Object.entries(entry.sections).map(([type, items]) => (
                <div key={type} className="changelog-section">
                  <span className={`changelog-type type-${type.toLowerCase()}`}>{type}</span>
                  <ul className="changelog-list">
                    {items.map((item, i) => (
                      <li key={i}>
                        <FontAwesomeIcon icon={faCheckCircle} className="changelog-check" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          ))}
        </div>
      </section>

      {/* Contact */}
      <section className="help-section">
        <div className="section-heading">
          <FontAwesomeIcon icon={faEnvelope} />
          <h2>Contact & Support</h2>
        </div>
        <div className="contact-card">
          <div className="contact-icon">
            <FontAwesomeIcon icon={faBug} />
          </div>
          <div className="contact-info">
            <h3>Report a Bug or Request a Feature</h3>
            <p>Found an issue or have an idea? Open an issue on GitHub — include your OS, Blender version, and steps to reproduce.</p>
            <a
              href="https://github.com/Charles-Butler/Blender-Render-Util/issues"
              target="_blank"
              rel="noreferrer"
              className="btn-github"
            >
              Open an Issue on GitHub
              <FontAwesomeIcon icon={faArrowUpRightFromSquare} />
            </a>
          </div>
        </div>
      </section>
    </div>
  )
}

export default Help
