import { useState, useEffect } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import {
  faFolderOpen, faPlay, faStop, faCheckCircle,
  faClock, faTrash, faFilm, faListAlt, faHistory
} from '@fortawesome/free-solid-svg-icons';
import './ConfigureRender.css';

function ConfigureRender({
  onStartRender,
  readOnly = false,
  onCancelRender,
  renderState,
  isStartingRender = false,
}) {
  const [projectName, setProjectName] = useState('');
  const [blendFile, setBlendFile] = useState('');
  const [recentFiles, setRecentFiles] = useState([]);
  const [batches, setBatches] = useState([]);
  const [showAddBatch, setShowAddBatch] = useState(false);
  const [showFileBrowser, setShowFileBrowser] = useState(false);
  const [availableFiles, setAvailableFiles] = useState([]);

  // New batch form state
  const [newBatch, setNewBatch] = useState({
    start: '',
    end: '',
    name: '',
    priority: 'null',
  });

  useEffect(() => {
    // Load config and recent files
    fetchConfig();
    fetchRecentFiles();
  }, []);

  // Update batches from renderState (passed from App.jsx via WebSocket)
  useEffect(() => {
    if (renderState && renderState.status === 'rendering') {
      // Get batches from render state (high priority, low priority, completed)
      const highPriority = renderState.high_priority_list || [];
      const lowPriority = renderState.low_priority_list || [];
      const completed = renderState.completed_list || [];

      // Combine all lists with status
      const allBatches = [
        ...completed.map((b) => ({ ...b, status: 'completed' })),
        ...highPriority.map((b) => ({
          ...b,
          status: b.number === renderState.current_batch ? 'rendering' : 'pending'
        })),
        ...lowPriority.map((b) => ({
          ...b,
          status: b.number === renderState.current_batch ? 'rendering' : 'pending'
        })),
      ];

      // Only update if we're in read-only mode OR if batches are empty
      if (readOnly || batches.length === 0) {
        setBatches(allBatches);
      }

      // Update project name if in read-only mode
      if (readOnly && renderState.project_name) {
        setProjectName(renderState.project_name);
      }
    }
  }, [renderState, readOnly]);

  const fetchConfig = async () => {
    try {
      const response = await fetch('http://localhost:8081/api/config');
      const data = await response.json();
      if (data.status === 'ok') {
        setProjectName(data.config.render.last_project_name || '');
      }
    } catch (error) {
      console.error('Failed to fetch config:', error);
    }
  };

  const fetchRecentFiles = async () => {
    try {
      const response = await fetch('http://localhost:8081/api/blend-files');
      const data = await response.json();
      if (data.status === 'ok') {
        setRecentFiles(data.recent_files || []);
        setBlendFile(data.last_file || '');
      }
    } catch (error) {
      console.error('Failed to fetch recent files:', error);
    }
  };

  const fetchRenderState = async () => {
    try {
      const response = await fetch('http://localhost:8081/api/status');
      const data = await response.json();
      if (data.status === 'ok' && data.render_state) {
        const state = data.render_state;
        setProjectName(state.project_name || '');

        // Combine all batch lists into one array with status
        const allBatches = [
          ...(state.completed_list || []).map((b) => ({
            ...b,
            status: 'completed',
          })),
          ...(state.high_priority_list || []).map((b) => ({
            ...b,
            status: b.number === state.current_batch ? 'rendering' : 'pending',
          })),
          ...(state.low_priority_list || []).map((b) => ({
            ...b,
            status: b.number === state.current_batch ? 'rendering' : 'pending',
          })),
        ].sort((a, b) => a.number - b.number);

        setBatches(allBatches);
      }
    } catch (error) {
      console.error('Failed to fetch render state:', error);
    }
  };

  const handleBrowseFiles = async () => {
    try {
      const response = await fetch('http://localhost:8081/api/blend-files/browse');
      const data = await response.json();
      if (data.status === 'ok') {
        setAvailableFiles(data.blend_files || []);
        setShowFileBrowser(true);
      }
    } catch (error) {
      console.error('Failed to browse files:', error);
      alert('Failed to browse for blend files. Check console for details.');
    }
  };

  const handleSelectBrowsedFile = async (filepath) => {
    setBlendFile(filepath);
    setShowFileBrowser(false);

    // Add to recent files
    try {
      await fetch('http://localhost:8081/api/blend-files/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filepath })
      });
      // Refresh recent files
      fetchRecentFiles();
    } catch (error) {
      console.error('Failed to add file to recents:', error);
    }
  };

  const handleAddBatch = () => {
    if (!newBatch.start || !newBatch.end) {
      alert('Please enter start and end frames');
      return;
    }

    const start = parseInt(newBatch.start);
    const end = parseInt(newBatch.end);

    if (isNaN(start) || isNaN(end)) {
      alert('Frame numbers must be valid integers');
      return;
    }

    if (end < start) {
      alert('End frame must be >= start frame');
      return;
    }

    const frames = end - start + 1;
    const batchNumber = batches.length + 1;

    const batch = {
      number: batchNumber,
      start,
      end,
      frames,
      name: newBatch.name || `Batch ${batchNumber}`,
      priority: newBatch.priority,
    };

    setBatches([...batches, batch]);
    setNewBatch({ start: '', end: '', name: '', priority: 'null' });
    setShowAddBatch(false);
  };

  const handleRemoveBatch = (index) => {
    const newBatches = batches.filter((_, i) => i !== index);
    // Renumber batches
    const renumbered = newBatches.map((batch, i) => ({
      ...batch,
      number: i + 1,
      name: batch.name.startsWith('Batch ') ? `Batch ${i + 1}` : batch.name,
    }));
    setBatches(renumbered);
  };

  const handleLoadLastProfile = async () => {
    try {
      const response = await fetch('http://localhost:8081/api/batch-profiles/last');
      const data = await response.json();

      if (data.status === 'ok' && data.profile) {
        const loadedBatches = data.profile.batches.map((batch, index) => ({
          number: index + 1,
          start: batch.start,
          end: batch.end,
          frames: batch.end - batch.start + 1,
          name: batch.name || `Batch ${index + 1}`,
          priority: batch.priority || 'null',
        }));

        setBatches(loadedBatches);
        alert(`Loaded ${loadedBatches.length} batches from last profile`);
      } else {
        alert('No previous batch profile found');
      }
    } catch (error) {
      console.error('Failed to load batch profile:', error);
      alert('Failed to load batch profile');
    }
  };

  const getSortedBatches = () => {
    return [...batches].sort((a, b) => {
      // Priority: 1 (High) > null/0 (Low)
      const priorityA = a.priority === '1' ? 2 : 1;
      const priorityB = b.priority === '1' ? 2 : 1;

      if (priorityA !== priorityB) {
        return priorityB - priorityA; // Higher priority first
      }

      // Same priority: sort by frame count (smaller first)
      return a.frames - b.frames;
    });
  };

  const getTotalFrames = () => {
    return batches.reduce((sum, batch) => sum + batch.frames, 0);
  };

  const handleStartRender = () => {
    if (!projectName.trim()) {
      alert('Please enter a project name');
      return;
    }

    if (!blendFile.trim()) {
      alert('Please select a blend file');
      return;
    }

    if (batches.length === 0) {
      alert('Please add at least one batch');
      return;
    }

    const renderConfig = {
      projectName,
      blendFile,
      batches: getSortedBatches(),
      totalBatches: batches.length,
      totalFrames: getTotalFrames(),
    };

    onStartRender(renderConfig);
  };

  const getPriorityLabel = (priority) => {
    if (priority === '1') return 'High';
    return 'Low';
  };

  const getPriorityColor = (priority) => {
    if (priority === '1') return '#fbbf24'; // yellow
    return '#60a5fa'; // blue
  };

  return (
    <div className='configure-render'>
      <div className='configure-container'>
        <h2>
          {readOnly ? 'Active Render Configuration' : 'Configure Batch Render'}
        </h2>

        {/* Two Column Layout */}
        <div className='config-grid'>
          {/* Left: Project Settings */}
          <div className='config-section'>
            <h3>
              <FontAwesomeIcon icon={faFolderOpen} /> Project Settings
            </h3>
            <div className='form-group'>
              <label>Project Name</label>
              <input
                type='text'
                value={projectName}
                onChange={(e) => setProjectName(e.target.value)}
                placeholder='MyAnimation'
                disabled={readOnly}
                className='input-field'
              />
            </div>

            <div className='form-group'>
              <label>Blend File</label>
              {readOnly ? (
                <div className='read-only-value'>{blendFile}</div>
              ) : (
                <>
                  <select
                    value={blendFile}
                    onChange={(e) => setBlendFile(e.target.value)}
                    className='input-field'
                  >
                    <option value=''>Select a blend file...</option>
                    {recentFiles.map((file, idx) => (
                      <option key={idx} value={file}>
                        {file}
                      </option>
                    ))}
                  </select>
                  <button
                    className='btn-secondary'
                    onClick={handleBrowseFiles}
                    style={{ marginTop: '8px', width: '100%' }}
                  >
                    <FontAwesomeIcon icon={faFolderOpen} /> Browse for More Files
                  </button>
                </>
              )}
            </div>

            {/* File Browser Modal */}
            {showFileBrowser && (
              <div className='modal-overlay' onClick={() => setShowFileBrowser(false)}>
                <div className='modal-content' onClick={(e) => e.stopPropagation()}>
                  <h3>Select Blend File</h3>
                  <div className='file-list'>
                    {availableFiles.length === 0 ? (
                      <p>No .blend files found. Scanning common directories...</p>
                    ) : (
                      availableFiles.map((file, idx) => (
                        <div
                          key={idx}
                          className='file-item'
                          onClick={() => handleSelectBrowsedFile(file)}
                        >
                          <FontAwesomeIcon icon={faFilm} />
                          <span className='file-path'>{file}</span>
                        </div>
                      ))
                    )}
                  </div>
                  <button
                    className='btn-secondary'
                    onClick={() => setShowFileBrowser(false)}
                    style={{ marginTop: '16px' }}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}

            {/* Action Buttons inside Project Settings */}
            <div className='action-buttons-inline'>
              <button
                className='btn-start-render'
                onClick={handleStartRender}
                disabled={batches.length === 0 || readOnly || isStartingRender}
              >
                <FontAwesomeIcon icon={isStartingRender ? faClock : faPlay} />
                {isStartingRender ? ' Starting Render...' : ' Start Job'}
              </button>
              <button
                className='btn-danger'
                onClick={onCancelRender}
                disabled={!readOnly || isStartingRender}
              >
                <FontAwesomeIcon icon={faStop} /> Cancel Job
              </button>
            </div>
            {isStartingRender && (
              <div style={{
                marginTop: '10px',
                padding: '10px',
                backgroundColor: 'rgba(255, 193, 7, 0.1)',
                border: '1px solid rgba(255, 193, 7, 0.3)',
                borderRadius: '4px',
                color: '#ffc107'
              }}>
                <FontAwesomeIcon icon={faClock} /> Launching render and waiting for log file generation...
                <br />
                <small>You will be redirected to the monitor page in 5 seconds.</small>
              </div>
            )}
          </div>

          {/* Right: Frame Selection */}
          <div className='config-section'>
            <div className='section-header'>
              <h3>
                <FontAwesomeIcon icon={faFilm} /> Frame Selection
              </h3>
              {!readOnly && (
                <div className='frame-selection-buttons'>
                  <button
                    className='btn-icon'
                    onClick={handleLoadLastProfile}
                    title='Load Last Batch Profile'
                  >
                    <FontAwesomeIcon icon={faHistory} />
                  </button>
                  <button
                    className='btn-icon'
                    onClick={() => setShowAddBatch(true)}
                    title='Add Batch'
                  >
                    +
                  </button>
                  <button
                    className='btn-icon'
                    onClick={() =>
                      batches.length > 0 &&
                      handleRemoveBatch(batches.length - 1)
                    }
                    disabled={batches.length === 0}
                    title='Remove Last Batch'
                  >
                    -
                  </button>
                </div>
              )}
            </div>

            {/* Add Batch Form */}
            {showAddBatch && !readOnly && (
              <div className='add-batch-form'>
                <div className='form-row'>
                  <input
                    type='number'
                    placeholder='Start Frame'
                    value={newBatch.start}
                    onChange={(e) =>
                      setNewBatch({ ...newBatch, start: e.target.value })
                    }
                    className='input-field'
                  />
                  <input
                    type='number'
                    placeholder='End Frame'
                    value={newBatch.end}
                    onChange={(e) =>
                      setNewBatch({ ...newBatch, end: e.target.value })
                    }
                    className='input-field'
                  />
                  <input
                    type='text'
                    placeholder='Batch Name (optional)'
                    value={newBatch.name}
                    onChange={(e) =>
                      setNewBatch({ ...newBatch, name: e.target.value })
                    }
                    className='input-field'
                  />
                  <select
                    value={newBatch.priority}
                    onChange={(e) =>
                      setNewBatch({ ...newBatch, priority: e.target.value })
                    }
                    className='input-field'
                  >
                    <option value='null'>Low Priority</option>
                    <option value='1'>High Priority</option>
                  </select>
                </div>
                <div className='form-actions'>
                  <button className='btn-primary' onClick={handleAddBatch}>
                    Add Batch
                  </button>
                  <button
                    className='btn-secondary'
                    onClick={() => setShowAddBatch(false)}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}

            {/* Render Order Preview */}
            {batches.length > 0 && (
              <div className='render-order-preview'>
                <h4>Render Order</h4>
                <div className='order-list'>
                  {getSortedBatches().map((batch, idx) => (
                    <div key={idx} className='order-item'>
                      <span className='order-number'>{idx + 1}.</span>
                      <span className='order-name'>{batch.name}</span>
                      <span className='order-frames'>
                        ({batch.frames} frames)
                      </span>
                      <span
                        className='priority-badge small'
                        style={{
                          backgroundColor: getPriorityColor(batch.priority),
                        }}
                      >
                        {getPriorityLabel(batch.priority)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {batches.length === 0 && (
              <div className='empty-state'>
                <p>No batches added yet. Click "+" to add a batch.</p>
              </div>
            )}
          </div>
        </div>

        {/* Full Width Batch Queue Below */}
        <div className='config-section full-width-section'>
          <h3>
            <FontAwesomeIcon icon={faListAlt} /> Batch Queue ({batches.length} batches, {getTotalFrames()} frames)
          </h3>

          {batches.length > 0 && (
            <div className='batch-table-container'>
              <table className='batch-table'>
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Name</th>
                    <th>Range</th>
                    <th>Frames</th>
                    <th>Priority</th>
                    {readOnly && <th>Status</th>}
                    {!readOnly && <th>Actions</th>}
                  </tr>
                </thead>
                <tbody>
                  {batches.map((batch, idx) => (
                    <tr key={idx}>
                      <td>{batch.number}</td>
                      <td>{batch.name}</td>
                      <td>
                        {batch.start} - {batch.end}
                      </td>
                      <td>{batch.frames}</td>
                      <td>
                        <span
                          className='priority-badge'
                          style={{
                            backgroundColor: getPriorityColor(batch.priority),
                          }}
                        >
                          {getPriorityLabel(batch.priority)}
                        </span>
                      </td>
                      {readOnly && (
                        <td>
                          <span
                            className={`status-badge status-${batch.status}`}
                          >
                            {batch.status === 'completed' && (
                              <>
                                <FontAwesomeIcon icon={faCheckCircle} /> Completed
                              </>
                            )}
                            {batch.status === 'rendering' && (
                              <>
                                <FontAwesomeIcon icon={faFilm} /> Rendering
                              </>
                            )}
                            {batch.status === 'pending' && (
                              <>
                                <FontAwesomeIcon icon={faClock} /> Pending
                              </>
                            )}
                          </span>
                        </td>
                      )}
                      {!readOnly && (
                        <td>
                          <button
                            className='btn-remove'
                            onClick={() => handleRemoveBatch(idx)}
                          >
                            <FontAwesomeIcon icon={faTrash} />
                          </button>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {batches.length === 0 && (
            <div className='empty-state'>
              <p>
                No batches added yet. Click "+" in Frame Selection to get
                started.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default ConfigureRender;
