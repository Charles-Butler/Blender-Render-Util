import { useState, useEffect } from 'react'
import './App.css'
import Navigation from './components/Navigation'
import ConfigureRender from './pages/ConfigureRender'
import ProgressMonitor from './pages/ProgressMonitor'
import Help from './pages/Help'

function App() {
  const [currentPage, setCurrentPage] = useState('configure')
  const [connected, setConnected] = useState(false)
  const [renderConfig, setRenderConfig] = useState(null)
  const [isStartingRender, setIsStartingRender] = useState(false)
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

  // Redirect from monitor to configure when status becomes idle
  useEffect(() => {
    if (currentPage === 'monitor' && renderState.status === 'idle') {
      console.log('Status is idle, redirecting to configure page')
      setCurrentPage('configure')
    }
  }, [currentPage, renderState.status])

  useEffect(() => {
    let ws = null
    let reconnectTimeout = null

    const connect = () => {
      const wsUrl = `ws://${window.location.host}/ws`
      ws = new WebSocket(wsUrl)

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

  const handleStartRender = async (config) => {
    console.log('Starting render with config:', config)
    setRenderConfig(config)
    setIsStartingRender(true)

    try {
      // Call backend API to start render
      const response = await fetch('/api/render/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      })

      const data = await response.json()

      if (data.status === 'ok') {
        console.log('Render started successfully. Waiting 5 seconds for log file generation...')

        // Wait 5 seconds for the bash script to create the log file
        // before switching to monitor page
        setTimeout(() => {
          setIsStartingRender(false)
          setCurrentPage('monitor')
          console.log('Switched to monitor page')
        }, 5000)
      } else {
        setIsStartingRender(false)
        alert(`Failed to start render: ${data.message}`)
      }
    } catch (error) {
      setIsStartingRender(false)
      console.error('Error starting render:', error)
      alert('Failed to start render. Check console for details.')
    }
  }

  const handleCancelRender = async () => {
    if (!confirm('Are you sure you want to cancel the current render job?')) {
      return
    }

    try {
      const response = await fetch('/api/render/cancel', {
        method: 'POST'
      })

      const data = await response.json()

      if (data.status === 'ok') {
        setRenderConfig(null)
        setCurrentPage('configure')
        alert('Render job cancelled')
      } else {
        alert(`Failed to cancel render: ${data.message}`)
      }
    } catch (error) {
      console.error('Error cancelling render:', error)
      alert('Failed to cancel render. Check console for details.')
    }
  }

  const handleNavigate = (page) => {
    setCurrentPage(page)
  }

  const handleHelp = () => {
    setCurrentPage(currentPage === 'help' ? 'configure' : 'help')
  }

  // Determine if navigation is allowed - allow navigation during rendering too
  const canNavigate = true

  return (
    <div className="app">
      <Navigation
        currentPage={currentPage}
        onNavigate={handleNavigate}
        renderStatus={renderState.status}
        canNavigate={canNavigate}
        onHelp={handleHelp}
      />

      {currentPage === 'configure' && (
        <ConfigureRender
          onStartRender={handleStartRender}
          readOnly={renderState.status === 'rendering'}
          onCancelRender={handleCancelRender}
          renderState={renderState}
          isStartingRender={isStartingRender}
        />
      )}

      {currentPage === 'monitor' && (
        <ProgressMonitor
          renderState={renderState}
          connected={connected}
        />
      )}

      {currentPage === 'help' && <Help />}
    </div>
  )
}

export default App
