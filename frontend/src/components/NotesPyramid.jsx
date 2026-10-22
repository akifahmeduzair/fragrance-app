import './NotesPyramid.css';

const TIERS = [
  { key: 'top', label: 'Top', hint: 'first 15 minutes' },
  { key: 'heart', label: 'Heart', hint: 'the main character' },
  { key: 'base', label: 'Base', hint: 'what lingers' },
];

export default function NotesPyramid({ notes }) {
  return (
    <div className="pyramid">
      {TIERS.map(({ key, label, hint }) => {
        const items = notes?.[key] || [];
        if (items.length === 0) return null;
        return (
          <div className="pyramid-tier" key={key} data-tier={key}>
            <div className="pyramid-tier-label">
              <span className="pyramid-tier-name">{label}</span>
              <span className="pyramid-tier-hint">{hint}</span>
            </div>
            <div className="pyramid-tier-notes">
              {items.map((n) => (
                <span className="note-chip" key={n}>{n}</span>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
