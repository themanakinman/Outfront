import React, { useState, useEffect } from 'react';
import Map, { Marker } from 'react-map-gl/maplibre';
import 'maplibre-gl/dist/maplibre-gl.css';
import './App.css';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCar } from '@fortawesome/free-solid-svg-icons';

function App() {
  const [query, setQuery] = useState('');
  const [wordIndex, setWordIndex] = useState(0);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [spots, setSpots] = useState([]);
  const [messages, setMessages] = useState([]);
  const [viewState, setViewState] = useState({
    longitude: -118.4011,
    latitude: 34.0689,
    zoom: 15
  });

  const locations = ['Rodeo Dr', 'Sunset Blvd', 'Melrose Ave', 'Figueroa St', 'Alameda St', 'Hollywood Blvd', 'Mulholland Dr', 'Wilshire St', 'Main St', 'Olympic Blvd', 'Spring St', 'Broadway', 'Exposition Blvd'];

  useEffect(() => {
    if (isSubmitted) return;
    const interval = setInterval(() => {
      setWordIndex((prev) => (prev + 1) % locations.length);
    }, 2000);
    return () => clearInterval(interval);
  }, [isSubmitted]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    
    setLoading(true);
    setSpots([]); // clear existing points while loading
    
    setMessages(prev => [...prev, { role: 'user', content: query }]);
    
    const currentQuery = query;
    setQuery('');

    if (!isSubmitted) {
      setIsSubmitted(true);
    }

    try {
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: currentQuery })
      });
      const data = await response.json();
      
      setSpots(data.spots || []);
      setMessages(prev => [...prev, { 
        role: 'ai', 
        content: data.insightful_response || "I couldn't find any spots matching that description."
      }]);
      
      if (data.spots && data.spots.length > 0) {
        setViewState({
          longitude: parseFloat(data.spots[0].lng),
          latitude: parseFloat(data.spots[0].lat),
          zoom: 15
        });
      }
    } catch (e) {
      console.error(e);
      setMessages(prev => [...prev, { 
        role: 'ai', 
        content: "Error communicating with AI backend. Is the FastAPI server running?"
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`app-container ${isSubmitted ? 'submitted' : ''}`}>
      {isSubmitted && (
        <>
          <div className="map-container">
            <Map
              {...viewState}
              onMove={evt => setViewState(evt.viewState)}
              mapStyle="https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json"
            >
              {spots.map(spot => (
                <Marker key={spot.id} longitude={spot.lng} latitude={spot.lat}>
                  <div className="marker-icon">
                    <FontAwesomeIcon icon={faCar} />
                  </div>
                </Marker>
              ))}
            </Map>
            
            {loading && (
              <div className="loading-overlay">
                <div className="spinner"></div>
                <span>Finding vacant meters...</span>
              </div>
            )}
          </div>
          
          <div className="chat-history">
            {messages.map((msg, idx) => (
              <div key={idx} className={`message ${msg.role}`}>
                <div className="message-content">{msg.content}</div>
              </div>
            ))}
          </div>
        </>
      )}

      <div className={`chat-wrapper ${isSubmitted ? 'docked' : ''}`}>
        {!isSubmitted && (
          <div className="chat-header">
            <span className="light">Find parking, </span>
            <span className="bold">Outfront</span>
          </div>
        )}
        <form className="chat-form" onSubmit={handleSubmit}>
          {!query && !isSubmitted && (
            <div className="placeholder-container">
              Ask about street parking on{' '}
              <span key={wordIndex} className="placeholder-text">
                {locations[wordIndex]}
              </span>
            </div>
          )}
          <input
            type="text"
            className="chat-input"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={isSubmitted ? "Ask a follow up" : ""}
            autoFocus
          />
          <button type="submit" className="send-button" disabled={!query.trim()} aria-label="Send message">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="send-icon">
              <path fillRule="evenodd" d="M11.47 2.47a.75.75 0 0 1 1.06 0l6.75 6.75a.75.75 0 1 1-1.06 1.06l-5.47-5.47V21a.75.75 0 0 1-1.5 0V4.81L5.78 10.28a.75.75 0 0 1-1.06-1.06l6.75-6.75Z" clipRule="evenodd" />
            </svg>
          </button>
        </form>
      </div>
    </div>
  );
}

export default App;
