import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import {
  faCircleQuestion,
  faTriangleExclamation,
  faClockRotateLeft,
  faEnvelope,
  faChevronDown,
  faChevronUp,
  faArrowUpRightFromSquare,
  faCheckCircle,
  faBug,
} from '@fortawesome/free-solid-svg-icons';
import { useState } from 'react';
import './Help.css';

const CHANGELOG = [
  {
    version: '5.4.2',
    date: '2026-04-19',
    sections: {
      Fixed: [
        'Monitor page no longer shows "Frame 0" and blank statistics after restarting the app',
        'Current frame, frame time, and average frame time are now restored correctly on startup',
      ],
    },
  },
  {
    version: '5.2.0',
    date: '2026-04-18',
    sections: {
      Added: ['Settings are now saved persistently between sessions'],
    },
  },
  {
    version: '5.1.0',
    date: '2026-04-18',
    sections: {
      Added: ['Native app window - no browser required'],
    },
  },
  {
    version: '5.0.0',
    date: '2026-04-17',
    sections: {
      Added: [
        'Real-time render monitoring with WebSocket updates',
        'Batch queue system with priority ordering',
        'High/Low priority batch grouping on the Monitor page',
      ],
    },
  },
];

const TROUBLESHOOTING = [
  {
    question:
      'Monitor shows "Frame 0" and blank statistics after reopening the app',
    answer:
      'The app restores render state from the log file on startup. If this happens, check that the log file for the active render has not been moved or deleted. You can also re-select it on the Monitor page using the log file picker.',
  },
  {
    question: '"No batch currently rendering" after reopening the app',
    answer:
      'The app scans the log file to reconstruct batch state. If the log file was moved or deleted since the render started, go to the Configure page and start a new render session.',
  },
  {
    question: 'Blender not found when starting a render',
    answer:
      'Open the Configure page and verify the Blender executable path. The default is /Applications/Blender.app/Contents/MacOS/Blender. Update it to match your Blender installation location.',
  },
  {
    question: 'Elapsed time shows a large negative number',
    answer:
      'This can happen if render state from a previous session was not cleared. Click Cancel Job on the Configure page to reset, then set up and start a new render.',
  },
  {
    question: 'Overall progress shows 100% before the render starts',
    answer:
      'Stale state from a prior render session. Click Cancel Job on the Configure page to reset, then reconfigure and start a new render.',
  },
];

function AccordionItem({ question, answer }) {
  const [open, setOpen] = useState(false);
  return (
    <div className={`accordion-item ${open ? 'open' : ''}`}>
      <button className='accordion-header' onClick={() => setOpen(!open)}>
        <span className='accordion-question'>{question}</span>
        <FontAwesomeIcon
          icon={open ? faChevronUp : faChevronDown}
          className='accordion-icon'
        />
      </button>
      {open && <div className='accordion-body'>{answer}</div>}
    </div>
  );
}

function Help() {
  return (
    <div className='help-page'>
      <div className='help-header'>
        <FontAwesomeIcon icon={faCircleQuestion} className='help-header-icon' />
        <div>
          <h1 className='help-title'>Help & Support</h1>
          <p className='help-subtitle'>
            Troubleshooting, changelog, and contact
          </p>
        </div>
      </div>

      {/* Troubleshooting */}
      <section className='help-section'>
        <div className='section-heading'>
          <FontAwesomeIcon icon={faTriangleExclamation} />
          <h2>Troubleshooting</h2>
        </div>
        <div className='accordion'>
          {TROUBLESHOOTING.map((item, i) => (
            <AccordionItem
              key={i}
              question={item.question}
              answer={item.answer}
            />
          ))}
        </div>
      </section>

      {/* Changelog */}
      <section className='help-section'>
        <div className='section-heading'>
          <FontAwesomeIcon icon={faClockRotateLeft} />
          <h2>Changelog</h2>
        </div>
        <div className='changelog'>
          {CHANGELOG.map((entry) => (
            <div key={entry.version} className='changelog-entry'>
              <div className='changelog-header'>
                <span className='changelog-version'>v{entry.version}</span>
                <span className='changelog-date'>{entry.date}</span>
              </div>
              {Object.entries(entry.sections).map(([type, items]) => (
                <div key={type} className='changelog-section'>
                  <span className={`changelog-type type-${type.toLowerCase()}`}>
                    {type}
                  </span>
                  <ul className='changelog-list'>
                    {items.map((item, i) => (
                      <li key={i}>
                        <FontAwesomeIcon
                          icon={faCheckCircle}
                          className='changelog-check'
                        />
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
      <section className='help-section'>
        <div className='section-heading'>
          <FontAwesomeIcon icon={faEnvelope} />
          <h2>Contact & Support</h2>
        </div>
        <div className='contact-card'>
          <div className='contact-icon'>
            <FontAwesomeIcon icon={faBug} />
          </div>
          <div className='contact-info'>
            <h3>Report a Bug or Request a Feature</h3>
            <p>
              Found an issue or have an idea? Open an issue on GitHub - include
              your OS, Blender version, and steps to reproduce.
            </p>
            <a
              href='https://github.com/Charles-Butler/Blender-Render-Util/issues'
              target='_blank'
              rel='noreferrer'
              className='btn-github'
            >
              Open an Issue on GitHub
              <FontAwesomeIcon icon={faArrowUpRightFromSquare} />
            </a>
          </div>
        </div>
      </section>
    </div>
  );
}

export default Help;
