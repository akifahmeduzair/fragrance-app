import { useState } from 'react';
import { api } from '../api';
import './SearchPanel.css';

export default function SearchPanel({ onSelect }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [searched, setSearched] = useState(false);

  const runSearch = async (value) => {
    setQuery(value);
    if (value.trim().length < 2) {
      setResults([]);
      setSearched(false);
      return;
    }
    const r = await api.search(value);
    setResults(r);
    setSearched(true);
  };

  return (
    <div className="search-panel">
      <input
        className="search-input"
        type="text"
        placeholder="Search a fragrance by name or brand&hellip;"
        value={query}
        onChange={(e) => runSearch(e.target.value)}
      />
      {searched && results.length === 0 && (
        <p className="search-empty">Nothing in the demo dataset matches that yet.</p>
      )}
      <ul className="search-results">
        {results.map((f) => (
          <li key={f.id}>
            <button className="search-result" onClick={() => onSelect(f.id)}>
              <span className="search-result-name">{f.name}</span>
              <span className="search-result-brand">{f.brand}</span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
