import { useEffect, useState } from 'react';
import NotesPyramid from './NotesPyramid';
import { api } from '../api';
import './FragranceDetail.css';

export default function FragranceDetail({ fragranceId, onInventoryChange }) {
  const [data, setData] = useState(null);
  const [flags, setFlags] = useState([]);
  const [error, setError] = useState(null);
  const [added, setAdded] = useState(false);

  useEffect(() => {
    setData(null);
    setFlags([]);
    setAdded(false);
    setError(null);
    if (!fragranceId) return;

    api.getFragrance(fragranceId).then(setData).catch((e) => setError(e.message));
    api.checkDuplicate(fragranceId).then((r) => setFlags(r.flags)).catch(() => {});
  }, [fragranceId]);

  if (!fragranceId) {
    return (
      <div className="detail-empty">
        <p>Search a fragrance or scan a bottle to see its notes, what it's inspired by, and whether it overlaps with anything you already own.</p>
      </div>
    );
  }

  if (error) return <p className="detail-error">{error}</p>;
  if (!data) return <p className="detail-loading">Loading&hellip;</p>;

  const handleAdd = async () => {
    await api.addToInventory(data.id);
    setAdded(true);
    onInventoryChange?.();
  };

  return (
    <div className="detail">
      <div className="detail-header">
        <p className="detail-brand">{data.brand}</p>
        <h2 className="detail-name">{data.name}</h2>
        <p className="detail-meta">{data.year} &middot; {data.concentration} &middot; {data.gender}</p>
      </div>

      <div className="detail-accords">
        {data.accords.map((a) => (
          <span className="accord-chip" key={a}>{a}</span>
        ))}
      </div>

      {flags.length > 0 && (
        <div className="duplicate-warning">
          <p className="duplicate-warning-title">Possible overlap with your collection</p>
          {flags.map((f) => (
            <p key={f.fragrance.id} className="duplicate-warning-item">
              {Math.round(f.score * 100)}% similar to <strong>{f.fragrance.name}</strong>, which you already own.
            </p>
          ))}
        </div>
      )}

      <NotesPyramid notes={data.notes} />

      {data.inspired_by && (
        <div className="relation-block">
          <p className="relation-label">Inspired by</p>
          <p className="relation-name">{data.inspired_by.brand} &mdash; {data.inspired_by.name}</p>
        </div>
      )}

      {data.dupes?.length > 0 && (
        <div className="relation-block">
          <p className="relation-label">Fragrances inspired by this</p>
          {data.dupes.map((d) => (
            <p className="relation-name" key={d.id}>{d.brand} &mdash; {d.name}</p>
          ))}
        </div>
      )}

      {data.similar?.length > 0 && (
        <div className="relation-block">
          <p className="relation-label">Closest scent matches in our data</p>
          {data.similar.slice(0, 3).map((s) => (
            <p className="relation-name" key={s.fragrance.id}>
              {s.fragrance.brand} &mdash; {s.fragrance.name} <span className="relation-score">{Math.round(s.score * 100)}%</span>
            </p>
          ))}
        </div>
      )}

      <button className="add-button" onClick={handleAdd} disabled={added}>
        {added ? 'Added to your collection' : 'Add to my collection'}
      </button>
    </div>
  );
}
