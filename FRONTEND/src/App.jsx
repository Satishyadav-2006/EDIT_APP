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
  const [videoFile, setVideoFile] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [selectedApp, setSelectedApp] = useState('');
  const [chatMessages, setChatMessages] = useState([]);
  const [userInput, setUserInput] = useState('');
  const [isSharing, setIsSharing] = useState(false);
  const [stream, setStream] = useState(null);

  const handleShareScreen = async () => {
    try {
      if (isSharing) {
        // Stop sharing
        if (stream) {
          stream.getTracks().forEach(track => track.stop());
        }
        setStream(null);
        setIsSharing(false);
      } else {
        // Start sharing
        const captureStream = await navigator.mediaDevices.getDisplayMedia({
          video: true
        });
        setStream(captureStream);
        setIsSharing(true);

        // Handle stop sharing from browser UI
        captureStream.getVideoTracks()[0].onended = () => {
          setIsSharing(false);
          setStream(null);
        };
      }
    } catch (err) {
      console.error("Error sharing screen: ", err);
      alert("Could not share screen. Please check permissions.");
    }
  };

  // State to hold the final summary for chat context
  const [analysisSummary, setAnalysisSummary] = useState(null);

  // REAL Analysis call
  const handleAnalyze = async () => {
    if (!videoFile) return;
    setScreen('loading');

    const formData = new FormData();
    formData.append('video', videoFile);

    try {
      const response = await fetch('http://localhost:8888/analyze', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('Analysis failed');

      const data = await response.json();

      // Map API response to UI state
      setAnalysisResult({
        language: data.summary.detected_language,
        duration: 'Detected', // AI returns duration, but UI expects string
        highlightsCount: data.summary.total_highlights,
        silenceCount: data.summary.total_silences,
        suggestionsCount: data.summary.total_suggestions,
        suggestions: data.suggestions.map(s => ({
          type: s.type.charAt(0).toUpperCase() + s.type.slice(1),
          start: s.start.toFixed(1),
          end: s.end.toFixed(1),
          reason: s.reason,
          confidence: Math.round(s.confidence * 100)
        }))
      });
      setAnalysisSummary(data.summary);
      setScreen('results');
    } catch (err) {
      console.error(err);
      alert("Error during analysis: " + err.message);
      setScreen('upload');
    }
  };

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (file && (file.type === 'video/mp4' || file.name.endsWith('.mp4'))) {
      setVideoFile(file);
    } else {
      alert('Please upload a valid MP4 video.');
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
          analysis_summary: analysisSummary
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
        {screen !== 'upload' && (
          <button className="btn-secondary" onClick={() => setScreen('upload')}>
            <RotateCcw size={16} style={{ marginRight: '8px' }} />
            New Upload
          </button>
        )}
      </nav>

      <main className="content">
        <AnimatePresence mode="wait">
          {screen === 'upload' && (
            <motion.div
              key="upload"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="upload-screen"
            >
              <div className="hero-text">
                <h1>AI Video Editing Assistant</h1>
                <p>Upload a video and get smart editing suggestions in seconds.</p>
                <div className="team-badge">Built by Data Diggers</div>
              </div>

              <div className="glass-card upload-card">
                <input
                  type="file"
                  accept="video/mp4"
                  id="video-upload"
                  hidden
                  onChange={handleFileUpload}
                />
                <label htmlFor="video-upload" className="upload-label">
                  {videoFile ? (
                    <div className="file-info">
                      <CheckCircle2 color="var(--success-color)" size={48} />
                      <h3>{videoFile.name}</h3>
                      <p>{(videoFile.size / (1024 * 1024)).toFixed(2)} MB</p>
                    </div>
                  ) : (
                    <div className="upload-placeholder">
                      <Upload size={48} color="var(--accent-color)" />
                      <h3>Drop your MP4 here</h3>
                      <p>or click to browse your files</p>
                    </div>
                  )}
                </label>

                {videoFile && (
                  <button className="btn-primary analyze-btn" onClick={handleAnalyze}>
                    Analyze Video
                  </button>
                )}
              </div>
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
              <div className="loader-container">
                <div className="pulse-circle"></div>
                <h2>AI is analyzing your video...</h2>
                <p>Detecting silence, audio energy, and key moments.</p>
                <div className="progress-bar-container">
                  <div className="progress-bar loading-gradient"></div>
                </div>
              </div>
            </motion.div>
          )}

          {screen === 'results' && (
            <motion.div
              key="results"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0 }}
              className="results-screen"
            >
              <div className="results-header">
                <h2>Analysis Results</h2>
                <div className="stats-row">
                  <div className="stat-item"><Star size={16} /> Language: <span>{analysisResult.language}</span></div>
                  <div className="stat-item"><Clock size={16} /> Duration: <span>{analysisResult.duration}</span></div>
                  <div className="stat-item">Highlights: <span>{analysisResult.highlightsCount}</span></div>
                  <div className="stat-item">Silences: <span>{analysisResult.silenceCount}</span></div>
                </div>
              </div>

              <div className="suggestions-list">
                <h3>Editing Suggestions</h3>
                {analysisResult.suggestions.map((item, idx) => (
                  <div key={idx} className="glass-card suggestion-card">
                    <div className="sug-icon">
                      {item.type === 'Highlight' ? <Star color="var(--warning-color)" /> : <Scissors color="var(--accent-color)" />}
                    </div>
                    <div className="sug-details">
                      <div className="sug-meta">
                        <span className={`tag ${item.type.toLowerCase()}`}>{item.type}</span>
                        <span className="timestamp">{item.start} - {item.end}</span>
                      </div>
                      <p className="reason">{item.reason}</p>
                    </div>
                    <div className="sug-confidence">
                      <span className="conf-label">Confidence</span>
                      <div className="conf-bar-bg">
                        <div className="conf-bar-fill" style={{ width: `${item.confidence}%` }}></div>
                      </div>
                      <span className="conf-val">{item.confidence}%</span>
                    </div>
                  </div>
                ))}
              </div>

              <div className="actions-row">
                <button className="btn-secondary" onClick={() => window.print()}>
                  Edit on my own
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
                      <option value="Other">Other</option>
                    </select>
                  </div>

                  <div className="screen-share-section">
                    <div className="share-info">
                      <Monitor size={20} />
                      <h4>Share Screen (Optional)</h4>
                    </div>
                    <p>Screen sharing is only for guidance and confidence. The app does NOT see or control the screen.</p>
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
                </div>

                <div className="chat-container glass-card">
                  <div className="chat-messages">
                    <div className="msg assistant">
                      <p>Hello! I can guide you through the edits. What would you like to know?</p>
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
