import { useState, useEffect } from 'react'
import './App.css'

function App() {
  const [connected, setConnected] = useState(false)
  const [renderState, setRenderState] = useState({
    project_name: '',
    status: 'idle',
    frames_completed: 0,
    total_frames: 0,
    overall_progress: 0,
    batch_progress: 0,
    current_batch: 0,
    current_frame: 0,
    high_priority_batches: 0,
    low_priority_batches: 0,
    completed_batches: 0,
    high_priority_list: [],
    low_priority_list: [],
    completed_list: [],
    avg_frame_time: 0,
    frame_time: 0,
    batch_eta: '00:00:00',
    overall_eta: '00:00:00',
    elapsed_time: '00:00:00'
  })

  useEffect(() => {
    let ws = null
    let reconnectTimeout = null

    const connect = () => {
      ws = new WebSocket('ws://localhost:8081/ws')

      ws.onopen = () => {
        console.log('WebSocket connected')
        setConnected(true)
      }

      ws.onmessage = (event) => {
        const message = JSON.parse(event.data)
        console.log('Received:', message)
        if (message.data) {
          setRenderState(prev => ({ ...prev, ...message.data }))
        }
      }

      ws.onclose = () => {
        console.log('WebSocket disconnected')
        setConnected(false)
        // Reconnect after 3 seconds
        reconnectTimeout = setTimeout(() => {
          console.log('Attempting to reconnect...')
          connect()
        }, 3000)
      }

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
      }
    }

    connect()

    return () => {
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout)
      }
      if (ws) {
        ws.close()
      }
    }
  }, [])

  const formatSeconds = (seconds) => {
    if (!seconds) return '--:--'
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
  }

  return (
    <div className="app">
      <div className="container">
        {/* Header */}
        <header className="header">
          <h1>🎬 Blender Render Monitor</h1>
          <div className="project-name">{renderState.project_name || 'Loading...'}</div>
          <div className={`status-badge ${renderState.status}`}>
            <span className="status-dot"></span>
            {renderState.status.charAt(0).toUpperCase() + renderState.status.slice(1)}
          </div>
          <div className={`connection-status ${connected ? 'connected' : 'disconnected'}`}>
            {connected ? '🟢 Connected' : '🔴 Disconnected'}
          </div>
        </header>

        {/* 1. Overall Progress - Full Width */}
        <div className="card full-width">
          <div className="card-title">🌍 Overall Progress</div>
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
          <div className="card-title">📊 Current Batch Progress</div>
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
              ⚠️ Frame {renderState.current_frame} outside batch range
            </div>
          )}
        </div>

        {/* 3. Statistics - Full Width */}
        <div className="card full-width">
          <div className="card-title">📈 Statistics</div>
          <div className="stats-grid">
            <div className="stat-item">
              <div className="stat-label">⏱️ Frame Time</div>
              <div className="stat-value">{formatSeconds(renderState.frame_time)}</div>
            </div>
            <div className="stat-item">
              <div className="stat-label">📊 Avg/Frame</div>
              <div className="stat-value">{formatSeconds(renderState.avg_frame_time)}</div>
            </div>
            <div className="stat-item">
              <div className="stat-label">⏳ Batch ETA</div>
              <div className="stat-value">{renderState.batch_eta}</div>
            </div>
            <div className="stat-item">
              <div className="stat-label">🌍 Overall ETA</div>
              <div className="stat-value">{renderState.overall_eta}</div>
            </div>
            <div className="stat-item">
              <div className="stat-label">🕐 Elapsed Time</div>
              <div className="stat-value">{renderState.elapsed_time}</div>
            </div>
            <div className="stat-item">
              <div className="stat-label">✅ Frames Done</div>
              <div className="stat-value">{renderState.frames_completed}</div>
            </div>
          </div>
        </div>

        {/* Priority Cards - 3 Even Columns */}
        <div className="grid-3">
          {/* High Priority */}
          <div className="card priority-card high-priority">
            <div className="priority-header">
              <div className="priority-icon">⚡</div>
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
              <div className="priority-icon">🔵</div>
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
              <div className="priority-icon">✅</div>
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
      </div>
    </div>
  )
}

export default App
