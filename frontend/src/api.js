const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function handle(res) {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${res.status})`);
  }
  return res.json();
}

export const api = {
  search: (q) => fetch(`${BASE_URL}/api/fragrances/search?q=${encodeURIComponent(q)}`).then(handle),
  getFragrance: (id) => fetch(`${BASE_URL}/api/fragrances/${id}`).then(handle),
  identify: (file) => {
    const form = new FormData();
    form.append('image', file);
    return fetch(`${BASE_URL}/api/identify`, { method: 'POST', body: form }).then(handle);
  },
  lookup: (brand, name) =>
    fetch(`${BASE_URL}/api/lookup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ brand, name }),
    }).then(handle),
  getInventory: () => fetch(`${BASE_URL}/api/inventory`).then(handle),
  addToInventory: (fragrance_id) =>
    fetch(`${BASE_URL}/api/inventory`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ fragrance_id }),
    }).then(handle),
  removeFromInventory: (id) => fetch(`${BASE_URL}/api/inventory/${id}`, { method: 'DELETE' }).then(handle),
  checkDuplicate: (id) => fetch(`${BASE_URL}/api/check/${id}`).then(handle),
};
