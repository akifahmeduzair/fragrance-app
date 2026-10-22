import { useState } from 'react';
import { api } from '../api';
import './ScanPanel.css';

export default function ScanPanel({ onSelect, onLookup }) {
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [guess, setGuess] = useState(null);
  const [outcome, setOutcome] = useState(null); // 'matched' | 'lookup' | 'unreadable'
  const [error, setError] = useState(null);

  const handleFile = async (file) => {
    if (!file) return;
    setError(null);
    setGuess(null);
    setOutcome(null);
    setPreview(URL.createObjectURL(file));
    setLoading(true);
    try {
      const r = await api.identify(file);
      setGuess(r.ai_guess);

      if (r.grounded_match) {
        // In our dataset: open its full details right away.
        setOutcome('matched');
        onSelect(r.grounded_match.match.id);
      } else if (r.ai_guess.brand && r.ai_guess.name) {
        // Not in our dataset: show web-sourced details, labeled unverified.
        setOutcome('lookup');
        onLookup({ brand: r.ai_guess.brand, name: r.ai_guess.name });
      } else {
        setOutcome('unreadable');
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const guessLabel = guess ? `${guess.brand || '?'} ${guess.name || ''}`.trim() : '';

  return (
    <div className="scan-panel">
      <label className="scan-drop">
        <input
          type="file"
          accept="image/*"
          onChange={(e) => handleFile(e.target.files?.[0])}
          hidden
        />
        {preview ? (
          <img src={preview} alt="Uploaded fragrance" className="scan-preview" />
        ) : (
          <span className="scan-drop-label">Upload or take a photo of a bottle</span>
        )}
      </label>

      {loading && <p className="scan-status">Reading the label&hellip;</p>}
      {error && <p className="scan-error">{error}</p>}

      {guess && (
        <div className="scan-result">
          <p className="scan-result-guess">
            AI read this as: <strong>{guessLabel}</strong>
            {guess.confidence ? ` (${Math.round(guess.confidence * 100)}% confidence)` : ''}
          </p>
          {outcome === 'matched' && (
            <p className="scan-status">Found in the dataset. Details are on the right.</p>
          )}
          {outcome === 'lookup' && (
            <p className="scan-status">Not in the dataset, so details come from a web search (unverified).</p>
          )}
          {outcome === 'unreadable' && (
            <p className="scan-no-match">
              Couldn't read a brand and name from this photo. Try a clearer shot of the front label.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
