import { useEffect, useState, useCallback } from 'react';
import { api } from '../api';
import './InventoryPanel.css';

export default function InventoryPanel({ onSelect, refreshKey }) {
  const [items, setItems] = useState([]);

  const load = useCallback(() => {
    api.getInventory().then(setItems).catch(() => {});
  }, []);

  useEffect(() => {
    load();
  }, [load, refreshKey]);

  const handleRemove = async (id, e) => {
    e.stopPropagation();
    await api.removeFromInventory(id);
    load();
  };

  if (items.length === 0) {
    return <p className="inventory-empty">Nothing in your collection yet &mdash; add fragrances from the search or scan tab.</p>;
  }

  return (
    <ul className="inventory-list">
      {items.map((f) => (
        <li key={f.id}>
          <button className="inventory-item" onClick={() => onSelect(f.id)}>
            <span>
              <span className="inventory-item-name">{f.name}</span>
              <span className="inventory-item-brand">{f.brand}</span>
            </span>
            <span className="inventory-remove" onClick={(e) => handleRemove(f.id, e)}>Remove</span>
          </button>
        </li>
      ))}
    </ul>
  );
}
