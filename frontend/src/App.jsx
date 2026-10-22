import { useState } from 'react';
import SearchPanel from './components/SearchPanel';
import ScanPanel from './components/ScanPanel';
import InventoryPanel from './components/InventoryPanel';
import FragranceDetail from './components/FragranceDetail';
import LookupDetail from './components/LookupDetail';
import './App.css';

const TABS = [
  { key: 'search', label: 'Search' },
  { key: 'scan', label: 'Scan a bottle' },
  { key: 'inventory', label: 'My collection' },
];

export default function App() {
  const [tab, setTab] = useState('search');
  const [selectedId, setSelectedId] = useState(null);
  const [lookup, setLookup] = useState(null); // { brand, name } for a fragrance outside the dataset
  const [inventoryVersion, setInventoryVersion] = useState(0);

  const select = (id) => {
    setLookup(null);
    setSelectedId(id);
  };
  const showLookup = (item) => {
    setSelectedId(null);
    setLookup(item);
  };

  return (
    <div className="app-shell">
      <header className="app-header">
        <h1 className="app-title">Fragrance?</h1>
        <p className="app-subtitle">Know what's in the bottle before you buy another one.</p>
      </header>

      <main className="app-main">
        <section className="panel panel-left">
          <nav className="tabs">
            {TABS.map((t) => (
              <button
                key={t.key}
                className={`tab ${tab === t.key ? 'tab-active' : ''}`}
                onClick={() => setTab(t.key)}
              >
                {t.label}
              </button>
            ))}
          </nav>

          {tab === 'search' && <SearchPanel onSelect={select} />}
          {tab === 'scan' && <ScanPanel onSelect={select} onLookup={showLookup} />}
          {tab === 'inventory' && <InventoryPanel onSelect={select} refreshKey={inventoryVersion} />}
        </section>

        <section className="panel panel-right">
          {lookup ? (
            <LookupDetail brand={lookup.brand} name={lookup.name} />
          ) : (
            <FragranceDetail
              fragranceId={selectedId}
              onInventoryChange={() => setInventoryVersion((v) => v + 1)}
            />
          )}
        </section>
      </main>

      <footer className="app-footer">
        <p>Demo dataset of ~20 fragrances &middot; dataset notes are fixed data, not AI recall &middot; fragrances outside it show web-sourced details marked unverified &middot; built for a grad seminar project</p>
      </footer>
    </div>
  );
}
