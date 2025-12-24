import React, { useState } from 'react';
import {
  Upload,
  Video,
  RotateCcw,
  MessageSquare,
  Scissors,
  Star,
  Clock,
  Monitor,
  ChevronRight,
  ExternalLink,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const App = () => {
  const [screen, setScreen] = useState('upload'); // upload, loading, results, guide
  const [videoFiles, setVideoFiles] = useState([]); // Array of files
  const [currentAnalyzing, setCurrentAnalyzing] = useState(""); // Name of video being analyzed

  // NEW: Support multiple results
  const [allResults, setAllResults] = useState([]);
  const [selectedResultIndex, setSelectedResultIndex] = useState(0);

  const [selectedApp, setSelectedApp] = useState('');
  const [chatMessages, setChatMessages] = useState([]);
  const [userInput, setUserInput] = useState('');
  const [isSharing, setIsSharing] = useState(false);
  const [stream, setStream] = useState(null);

  // Helper to format seconds to MM:SS
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleShareScreen = async () => {
    // ... (rest of share screen logic)
    try {
      if (isSharing) {
        if (stream) { stream.getTracks().forEach(track => track.stop()); }
        setStream(null); setIsSharing(false);
      } else {
        const captureStream = await navigator.mediaDevices.getDisplayMedia({ video: true });
        setStream(captureStream); setIsSharing(true);
        captureStream.getVideoTracks()[0].onended = () => { setIsSharing(false); setStream(null); };
      }
    } catch (err) { console.error(err); alert("Permission denied."); }
  };

  // REAL Analysis call
  const handleAnalyze = async () => {
    if (videoFiles.length === 0) return;
    setScreen('loading');

    let newResultsBatch = [];

    for (const file of videoFiles) {
      setCurrentAnalyzing(file.name);
      const formData = new FormData();
      formData.append('video', file);

      try {
        const response = await fetch('http://localhost:8888/analyze', {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) throw new Error(`Analysis failed for ${file.name}`);

        const data = await response.json();

        // Map API response to our rich state
        const newResult = {
          name: file.name,
          id: data.analysis_id,
          time: data.timestamp,
          language: data.summary.detected_language,
          duration: formatTime(data.summary.duration || 0),
          highlightsCount: data.summary.total_highlights,
          silenceCount: data.summary.total_silences,
          suggestionsCount: data.summary.total_suggestions,
          summary: data.summary, // store for chat context
          suggestions: data.suggestions.map(s => ({
            type: s.type.charAt(0).toUpperCase() + s.type.slice(1),
            start: formatTime(s.start),
            end: formatTime(s.end),
            reason: s.reason,
            confidence: Math.round(s.confidence * 100)
          }))
        };
        newResultsBatch.push(newResult);
      } catch (err) {
        console.error(err);
        alert("Error analyzing " + file.name + ": " + err.message);
      }
    }

    if (newResultsBatch.length > 0) {
      setAllResults(current => [...newResultsBatch, ...current]);
      setSelectedResultIndex(0);
      setVideoFiles([]); // Clear selection
      setScreen('results');
    } else {
      setScreen('upload');
    }
  };

  const handleFileUpload = (e) => {
    const files = Array.from(e.target.files);
    const validFiles = files.filter(f =>
      f.type === 'video/mp4' ||
      f.name.toLowerCase().endsWith('.mp4')
    );

    if (validFiles.length > 0) {
      setVideoFiles(validFiles);
    } else {
      alert('Please upload valid MP4 videos.');
    }
  };

  // REAL Chat call
  const sendChatMessage = async (e) => {
    e.preventDefault();
    if (!userInput.trim()) return;

    const newMessages = [...chatMessages, { role: 'user', text: userInput }];
    setChatMessages(newMessages);
    setUserInput('');

    try {
      const response = await fetch('http://localhost:8888/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userInput,
          analysis_summary: allResults[selectedResultIndex]?.summary,
          selected_app: selectedApp,
          is_sharing: isSharing
        }),
      });

      if (!response.ok) throw new Error('Chat failed');

      const data = await response.json();
      setChatMessages([...newMessages, { role: 'assistant', text: data.reply }]);
    } catch (err) {
      console.error(err);
      setChatMessages([...newMessages, { role: 'assistant', text: "Error: Could not connect to AI." }]);
    }
  };

  return (
    <div className="app-container">
      {/* Navbar */}
      <nav className="navbar">
        <div className="logo">
          <Video className="logo-icon" size={24} />
          <span>AI Video Assistant</span>
        </div>
        <div className="nav-actions">
          {screen !== 'upload' && (
            <button className="btn-secondary" onClick={() => setScreen('upload')}>
              <Upload size={16} style={{ marginRight: '8px' }} />
              Add Another Video
            </button>
          )}
        </div>
      </nav>

      <main className="main-content">
        <AnimatePresence mode="wait">
          {screen === 'upload' && (
            <motion.div
              key="upload"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="upload-card"
            >
              <div className="upload-header">
                <Upload className="upload-icon" size={48} />
                <h1>Analyze New Video</h1>
                <p>Upload a video to get AI-powered editing suggestions and highlights.</p>
              </div>

              {allResults.length > 0 && (
                <div className="history-section">
                  <h4>Previous Analyses:</h4>
                  <div className="history-list">
                    {allResults.map((res, idx) => (
                      <button
                        key={res.id}
                        onClick={() => { setSelectedResultIndex(idx); setScreen('results'); }}
                        className="history-item"
                      >
                        {res.name}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              <label className="file-input-label" htmlFor="video-upload">
                <input
                  id="video-upload"
                  type="file"
                  accept="video/mp4"
                  multiple
                  onChange={handleFileUpload}
                />
                <span>{videoFiles.length > 0 ? `${videoFiles.length} videos selected` : 'Choose MP4 videos...'}</span>
              </label>

              <button
                className={`btn-primary ${videoFiles.length === 0 ? 'disabled' : ''}`}
                onClick={handleAnalyze}
                disabled={videoFiles.length === 0}
              >
                Analyze {videoFiles.length > 1 ? `${videoFiles.length} Videos` : 'Video'}
              </button>
            </motion.div>
          )}

          {screen === 'loading' && (
            <motion.div
              key="loading"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="loading-screen"
            >
              <div className="loader"></div>
              <h2>Analyzing Video...</h2>
              <p style={{ color: 'var(--accent-color)', fontWeight: '600', marginBottom: '8px' }}>
                Currently: {currentAnalyzing}
              </p>
              <p>Extracting audio, detecting highlights, and generating suggestions.</p>
            </motion.div>
          )}

          {screen === 'results' && allResults[selectedResultIndex] && (
            <motion.div
              key="results"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0 }}
              className="results-screen"
            >
              <div className="results-header">
                <div className="title-row">
                  <div className="title-group">
                    <h2>Analysis: {allResults[selectedResultIndex].name}</h2>
                    {allResults.length > 1 && (
                      <select
                        className="result-switcher"
                        value={selectedResultIndex}
                        onChange={(e) => setSelectedResultIndex(parseInt(e.target.value))}
                      >
                        {allResults.map((res, idx) => (
                          <option key={res.id} value={idx}>{res.name}</option>
                        ))}
                      </select>
                    )}
                  </div>
                  <span className="metadata">ID: {allResults[selectedResultIndex].id} | {allResults[selectedResultIndex].time}</span>
                </div>
                <div className="stats-row">
                  <div className="stat-item"><Star size={16} /> Language: <span>{allResults[selectedResultIndex].language}</span></div>
                  <div className="stat-item"><Clock size={16} /> Duration: <span>{allResults[selectedResultIndex].duration}</span></div>
                  <div className="stat-item"><Scissors size={16} /> Suggestions: <span>{allResults[selectedResultIndex].suggestionsCount}</span></div>
                </div>
              </div>

              <div className="suggestions-list">
                {allResults[selectedResultIndex].suggestions.map((suggestion, index) => (
                  <div key={index} className="suggestion-card">
                    <div className="suggestion-icon">
                      {suggestion.type === 'Highlight' ? <Star size={18} /> :
                        suggestion.type === 'Transition' ? <RotateCcw size={18} /> : <Scissors size={18} />}
                    </div>
                    <div className="suggestion-content">
                      <div className="suggestion-meta">
                        <span className={`tag ${suggestion.type.toLowerCase()}`}>{suggestion.type.toUpperCase()}</span>
                        <span className="timestamp">{suggestion.start} - {suggestion.end}</span>
                      </div>
                      <p className="reason">{suggestion.reason}</p>
                    </div>
                    <div className="confidence-score">
                      <div className="score-label">Confidence</div>
                      <div className="score-bar">
                        <div className="score-fill" style={{ width: `${suggestion.confidence}%` }}></div>
                      </div>
                      <div className="score-value">{suggestion.confidence}%</div>
                    </div>
                  </div>
                ))}
              </div>

              <div className="actions-row">
                <button className="btn-secondary" onClick={() => setScreen('upload')}>
                  <Upload size={16} style={{ marginRight: '8px' }} /> Add Another
                </button>
                <button className="btn-primary" onClick={() => setScreen('guide')}>
                  Guide Me <ChevronRight size={18} />
                </button>
              </div>
            </motion.div>
          )}

          {screen === 'guide' && (
            <motion.div
              key="guide"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="guide-screen"
            >
              <div className="chat-layout">
                <div className="chat-sidebar glass-card">
                  <h3>Guidance Setup</h3>
                  <div className="input-group">
                    <label>Which editing app are you using?</label>
                    <select value={selectedApp} onChange={(e) => setSelectedApp(e.target.value)}>
                      <option value="">Select an app...</option>
                      <option value="CapCut">CapCut</option>
                      <option value="Canva">Canva</option>
                      <option value="InShot">InShot</option>
                      <option value="DaVinci Resolve">DaVinci Resolve</option>
                      <option value="Premiere Pro">Premiere Pro</option>
                      <option value="Final Cut Pro">Final Cut Pro</option>
                      <option value="Other">Other</option>
                    </select>
                  </div>

                  <div className="screen-share-section">
                    <div className="share-info">
                      <Monitor size={20} />
                      <h4>Share Screen (Optional)</h4>
                    </div>
                    <p className="share-note">For real-time guidance context.</p>
                    <button
                      className={`btn-secondary share-btn ${isSharing ? 'active' : ''}`}
                      onClick={handleShareScreen}
                    >
                      {isSharing ? 'Stop Sharing' : 'Share Screen'}
                    </button>
                    {isSharing && stream && (
                      <div className="share-preview glass-card">
                        <video
                          autoPlay
                          muted
                          ref={(video) => video && (video.srcObject = stream)}
                        />
                      </div>
                    )}
                  </div>

                  <button className="btn-secondary" style={{ width: '100%', marginTop: 'auto' }} onClick={() => setScreen('results')}>
                    <RotateCcw size={16} style={{ marginRight: '8px' }} /> Back to Results
                  </button>
                </div>

                <div className="chat-container glass-card">
                  <div className="chat-messages">
                    <div className="msg assistant">
                      <p>Hello! I can guide you through the edits for "<strong>{allResults[selectedResultIndex]?.name}</strong>". What would you like to know?</p>
                    </div>
                    {chatMessages.map((msg, idx) => (
                      <div key={idx} className={`msg ${msg.role}`}>
                        <p>{msg.text}</p>
                      </div>
                    ))}
                  </div>
                  <form className="chat-input" onSubmit={sendChatMessage}>
                    <input
                      type="text"
                      placeholder="Ask how to cut, split, or improve..."
                      value={userInput}
                      onChange={(e) => setUserInput(e.target.value)}
                    />
                    <button type="submit" className="btn-primary">
                      <MessageSquare size={18} />
                    </button>
                  </form>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      <footer className="footer">
        <p>&copy; 2025 AI Video Assistant. Focus on Analysis & Guidance.</p>
      </footer>
    </div>
  );
};

export default App;
