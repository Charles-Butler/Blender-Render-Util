import { useState, useEffect } from 'react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faFolderOpen, faGlobe, faChartBar, faTriangleExclamation,
  faChartLine, faStopwatch, faClock, faBolt, faLevelDown,
  faCheckCircle, faFileLines
} from '@fortawesome/free-solid-svg-icons'
import '../App.css'

function LogFilePicker({ onSelect, onClose }) {
  const [logFiles, setLogFiles] = useState([])
  const [loading, setLoading] = useState(true)
  const fileInputRef = useState(null)[0]

  useEffect(() => {
    fetchLogFiles()
  }, [])

  const fetchLogFiles = async () => {
    try {
      const response = await fetch('http://localhost:8081/api/browse-log-files')
      const data = await response.json()

      if (data.status === 'ok') {
        setLogFiles(data.log_files || [])
      }
    } catch (error) {
      console.error('Error fetching log files:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleExternalFileSelect = () => {
    const path = prompt('Enter the full path to the external log file:', '/Users/me/path/to/logfile.txt')
    if (path && path.trim()) {
      onSelect(path.trim())
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Select Render to Monitor</h3>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>
        <div className="modal-body">
          {loading ? (
            <div className="loading">Loading log files...</div>
          ) : logFiles.length > 0 ? (
            <div className="log-file-list">
              {logFiles.map((file, idx) => (
                <div
                  key={idx}
                  className="log-file-item"
                  onClick={() => onSelect(file.path)}
                >
                  <div className="log-file-name">{file.project_name}</div>
                  <div className="log-file-date">{file.date}</div>
                  <div className="log-file-path">{file.path}</div>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state">No log files found in renders directory</div>
          )}
        </div>
        <div className="modal-footer">
          <button className="btn-external" onClick={handleExternalFileSelect}>
            <FontAwesomeIcon icon={faFolderOpen} /> Select External Log File
          </button>
        </div>
      </div>
    </div>
  )
}

function ProgressMonitor({ renderState, connected }) {
  const [elapsedTime, setElapsedTime] = useState('00:00:00')
  const [currentLogFile, setCurrentLogFile] = useState('')
  const [showFilePicker, setShowFilePicker] = useState(false)

  const formatSeconds = (seconds) => {
    if (!seconds) return '--:--'
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
  }

  const formatElapsedTime = (startTime) => {
    if (!startTime) return '00:00:00'
    const elapsed = Math.floor(Date.now() / 1000 - startTime)
    const hours = Math.floor(elapsed / 3600)
    const mins = Math.floor((elapsed % 3600) / 60)
    const secs = elapsed % 60
    return `${String(hours).padStart(2, '0')}:${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
  }

  // Update elapsed time every second
  useEffect(() => {
    const interval = setInterval(() => {
      if (renderState.start_time && !renderState.end_time) {
        // Only update if render is still active (no end_time)
        setElapsedTime(formatElapsedTime(renderState.start_time))
      } else if (renderState.start_time && renderState.end_time) {
        // Render completed, show final elapsed time
        const finalElapsed = renderState.end_time - renderState.start_time
        const hours = Math.floor(finalElapsed / 3600)
        const mins = Math.floor((finalElapsed % 3600) / 60)
        const secs = Math.floor(finalElapsed % 60)
        setElapsedTime(`${String(hours).padStart(2, '0')}:${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`)
      }
    }, 1000)
    return () => clearInterval(interval)
  }, [renderState.start_time, renderState.end_time])

  // Fetch current log file info
  useEffect(() => {
    fetchLogInfo()
  }, [])

  const fetchLogInfo = async () => {
    try {
      const response = await fetch('http://localhost:8081/api/status')
      const data = await response.json()
      if (data.status === 'ok' && data.render_state) {
        // Try to get log file from render state or config
        if (data.render_state.log_file) {
          setCurrentLogFile(data.render_state.log_file)
        } else {
          // Fallback to config
          const configResponse = await fetch('http://localhost:8081/api/config')
          const configData = await configResponse.json()
          if (configData.status === 'ok') {
            setCurrentLogFile(configData.config?.monitoring?.current_log_file || 'Not monitoring')
          }
        }
      }
    } catch (error) {
      console.error('Failed to fetch log info:', error)
      setCurrentLogFile('Not monitoring')
    }
  }

  const handleSwitchLogFile = async (logFilePath) => {
    try {
      const response = await fetch('http://localhost:8081/api/monitor/override', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ logfile: logFilePath })
      })

      const data = await response.json()

      if (data.status === 'ok') {
        setCurrentLogFile(logFilePath)
        setShowFilePicker(false)
      } else {
        alert(`Failed to switch log file: ${data.message}`)
      }
    } catch (error) {
      console.error('Error switching log file:', error)
      alert('Failed to switch log file. Check console for details.')
    }
  }

  return (
    <div className="progress-monitor">
      <div className="container">
        {/* 1. Overall Progress - Full Width */}
        <div className="card full-width">
          <div className="card-title">
            <FontAwesomeIcon icon={faGlobe} /> {renderState.project_name || 'Loading...'} - Overall Progress
          </div>
          <div className="card-subtitle">
            {renderState.frames_completed} / {renderState.total_frames} frames
          </div>
          <div className="progress-bar">
            <div
              className="progress-fill overall"
              style={{ width: `${renderState.overall_progress}%` }}
            >
              {renderState.overall_progress}%
            </div>
          </div>
        </div>

        {/* 2. Current Batch Progress - Full Width */}
        <div className="card full-width">
          <div className="card-title">
            <FontAwesomeIcon icon={faChartBar} /> Current Batch Progress
          </div>
          <div className="card-subtitle">
            {renderState.current_batch > 0 ? (
              <>
                Batch #{renderState.current_batch}: Frame {renderState.current_frame}
                {renderState.batch_start_frame && renderState.batch_end_frame &&
                  ` (${renderState.batch_start_frame}-${renderState.batch_end_frame})`}
              </>
            ) : (
              'No batch currently rendering'
            )}
          </div>
          <div className="progress-bar">
            <div
              className="progress-fill batch"
              style={{ width: `${Math.max(0, Math.min(100, renderState.batch_progress))}%` }}
            >
              {Math.max(0, Math.min(100, renderState.batch_progress))}%
            </div>
          </div>
          {renderState.batch_progress < 0 && (
            <div style={{ fontSize: '0.8rem', color: '#ef4444', marginTop: '8px' }}>
              <FontAwesomeIcon icon={faTriangleExclamation} /> Frame {renderState.current_frame} outside batch range
            </div>
          )}
        </div>

        {/* 3. Statistics - Full Width */}
        <div className="card full-width">
          <div className="card-title">
            <FontAwesomeIcon icon={faChartLine} /> Statistics
          </div>
          <div className="stats-grid">
            <div className="stat-item">
              <div className="stat-label">
                <FontAwesomeIcon icon={faStopwatch} /> Frame Time
              </div>
              <div className="stat-value">{formatSeconds(renderState.frame_time)}</div>
            </div>
            <div className="stat-item">
              <div className="stat-label">
                <FontAwesomeIcon icon={faChartBar} /> Avg/Frame
              </div>
              <div className="stat-value">{formatSeconds(renderState.avg_frame_time)}</div>
            </div>
            <div className="stat-item">
              <div className="stat-label">
                <FontAwesomeIcon icon={faClock} /> Batch ETA
              </div>
              <div className="stat-value">{renderState.batch_eta}</div>
            </div>
            <div className="stat-item">
              <div className="stat-label">
                <FontAwesomeIcon icon={faGlobe} /> Overall ETA
              </div>
              <div className="stat-value">{renderState.overall_eta}</div>
            </div>
            <div className="stat-item">
              <div className="stat-label">
                <FontAwesomeIcon icon={faClock} /> Elapsed Time
              </div>
              <div className="stat-value">{elapsedTime}</div>
            </div>
            <div className="stat-item">
              <div className="stat-label">
                <FontAwesomeIcon icon={faCheckCircle} /> Frames Done
              </div>
              <div className="stat-value">{renderState.frames_completed}</div>
            </div>
          </div>
        </div>

        {/* Priority Cards - 3 Even Columns */}
        <div className="grid-3">
          {/* High Priority */}
          <div className="card priority-card high-priority">
            <div className="priority-header">
              <div className="priority-icon">
                <FontAwesomeIcon icon={faBolt} />
              </div>
              <div className="priority-header-text">
                <div className="priority-label">High Priority</div>
                <div className="priority-count">{renderState.high_priority_batches} batches</div>
              </div>
            </div>
            <ul className="batch-list">
              {renderState.high_priority_list && renderState.high_priority_list.length > 0 ? (
                renderState.high_priority_list.map((batch, idx) => (
                  <li key={idx} className="batch-item">
                    <div className="batch-name">{batch.name}</div>
                    <div className="batch-details">
                      {String(batch.start).padStart(4, '0')} - {String(batch.end).padStart(4, '0')} • {batch.frames} frames
                    </div>
                  </li>
                ))
              ) : (
                <li className="batch-empty">No high priority batches</li>
              )}
            </ul>
          </div>

          {/* Low Priority */}
          <div className="card priority-card low-priority">
            <div className="priority-header">
              <div className="priority-icon">
                <FontAwesomeIcon icon={faLevelDown} />
              </div>
              <div className="priority-header-text">
                <div className="priority-label">Low Priority</div>
                <div className="priority-count">{renderState.low_priority_batches} batches</div>
              </div>
            </div>
            <ul className="batch-list">
              {renderState.low_priority_list && renderState.low_priority_list.length > 0 ? (
                renderState.low_priority_list.map((batch, idx) => (
                  <li key={idx} className="batch-item">
                    <div className="batch-name">{batch.name}</div>
                    <div className="batch-details">
                      {String(batch.start).padStart(4, '0')} - {String(batch.end).padStart(4, '0')} • {batch.frames} frames
                    </div>
                  </li>
                ))
              ) : (
                <li className="batch-empty">No low priority batches</li>
              )}
            </ul>
          </div>

          {/* Completed */}
          <div className="card priority-card completed">
            <div className="priority-header">
              <div className="priority-icon">
                <FontAwesomeIcon icon={faCheckCircle} />
              </div>
              <div className="priority-header-text">
                <div className="priority-label">Completed</div>
                <div className="priority-count">{renderState.completed_batches} batches</div>
              </div>
            </div>
            <ul className="batch-list">
              {renderState.completed_list && renderState.completed_list.length > 0 ? (
                renderState.completed_list.map((batch, idx) => (
                  <li key={idx} className="batch-item">
                    <div className="batch-name">{batch.name}</div>
                    <div className="batch-details">
                      {String(batch.start).padStart(4, '0')} - {String(batch.end).padStart(4, '0')} • {batch.frames} frames
                    </div>
                  </li>
                ))
              ) : (
                <li className="batch-empty">No completed batches</li>
              )}
            </ul>
          </div>
        </div>

        {/* Log File Info Section */}
        <div className="card full-width log-info-section">
          <div className="log-info-header">
            <div className="log-label">
              <FontAwesomeIcon icon={faFileLines} /> Currently Monitoring:
            </div>
            <div className="log-path">
              {currentLogFile}
            </div>
            <button
              className="btn-override"
              onClick={() => setShowFilePicker(true)}
            >
              Switch Render
            </button>
          </div>
        </div>
      </div>

      {showFilePicker && (
        <LogFilePicker
          onSelect={handleSwitchLogFile}
          onClose={() => setShowFilePicker(false)}
        />
      )}
    </div>
  )
}

export default ProgressMonitor
