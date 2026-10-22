import { useEffect, useState } from 'react';
import NotesPyramid from './NotesPyramid';
import { api } from '../api';
import './FragranceDetail.css';
import './LookupDetail.css';

// Details for a fragrance that is NOT in the dataset. Fetched from a web-grounded
// Gemini lookup and always labeled unverified.
export default function LookupDetail({ brand, name }) {
  const [state, setState] = useState({ status: 'loading', data: null, error: null });

  useEffect(() => {
    let cancelled = false;
    setState({ status: 'loading', data: null, error: null });
    api
      .lookup(brand, name)
      .then((data) => !cancelled && setState({ status: 'done', data, error: null }))
      .catch((e) => !cancelled && setState({ status: 'error', data: null, error: e.message }));
    return () => {
      cancelled = true;
    };
  }, [brand, name]);

  const { status, data, error } = state;

  return (
    <div className="detail">
      <div className="detail-header">
        <p className="detail-brand">{data?.brand || brand}</p>
        <h2 className="detail-name">{data?.name || name}</h2>
        {data && (data.year || data.concentration || data.gender) && (
          <p className="detail-meta">
            {[data.year, data.concentration, data.gender].filter(Boolean).join(' · ')}
          </p>
        )}
      </div>

      <div className="lookup-banner">
        Not in the demo dataset. Anything below comes from a live web search and has not been verified.
      </div>

      {status === 'loading' && <p className="detail-loading">Searching the web for notes&hellip;</p>}

      {status === 'error' && <p className="detail-error">{error}</p>}

      {status === 'done' && !data.found && (
        <p className="detail-empty">
          Couldn't find reliable notes for this exact fragrance. Check the spelling on the bottle, or
          try a clearer photo.
        </p>
      )}

      {status === 'done' && data.found && (
        <>
          {data.summary && <p className="lookup-summary">{data.summary}</p>}

          {data.accords.length > 0 && (
            <div className="detail-accords">
              {data.accords.map((a) => (
                <span className="accord-chip" key={a}>{a}</span>
              ))}
            </div>
          )}

          <NotesPyramid notes={data.notes} />

          {data.inspired_by && (
            <div className="relation-block">
              <p className="relation-label">Said to be inspired by</p>
              <p className="relation-name">{data.inspired_by}</p>
            </div>
          )}
        </>
      )}

      {status === 'done' && data.sources?.length > 0 && (
        <div className="relation-block">
          <p className="relation-label">Sources</p>
          <ul className="lookup-sources">
            {data.sources.map((s) => (
              <li key={s.url}>
                <a href={s.url} target="_blank" rel="noreferrer">{s.title}</a>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
