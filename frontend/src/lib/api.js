import axios from "axios";

export const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const client = axios.create({ baseURL: API_URL });

client.interceptors.request.use((config) => {
  const token = localStorage.getItem("horizon_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Normalize backend errors -> a single readable message.
client.interceptors.response.use(
  (res) => res,
  (err) => {
    const detail = err?.response?.data?.detail;
    let message = "Something went wrong. Please try again.";
    if (typeof detail === "string") message = detail;
    else if (Array.isArray(detail) && detail[0]?.msg) message = detail[0].msg;
    else if (err?.message === "Network Error") {
      message = `Can't reach the backend at ${API_URL}. Is it running?`;
    }
    return Promise.reject(Object.assign(new Error(message), { original: err }));
  }
);

// ---------- Auth ----------
export const registerUser = (email, password) =>
  client.post("/auth/register", { email, password }).then((r) => r.data);

export const loginUser = (email, password) =>
  client.post("/auth/login", { email, password }).then((r) => r.data);

export const fetchMe = () => client.get("/auth/me").then((r) => r.data);

// ---------- Decks ----------
export const uploadDeck = (title, file, onProgress) => {
  const form = new FormData();
  form.append("title", title);
  form.append("file", file);
  return client
    .post("/decks/upload", form, {
      headers: { "Content-Type": "multipart/form-data" },
      onUploadProgress: (evt) => {
        if (onProgress && evt.total) onProgress(Math.round((evt.loaded / evt.total) * 100));
      },
    })
    .then((r) => r.data);
};

export const listDecks = ({ q, sort } = {}) =>
  client.get("/decks", { params: { q: q || undefined, sort: sort || undefined } }).then((r) => r.data);

export const getDeck = (deckId) => client.get(`/decks/${deckId}`).then((r) => r.data);

export const getDeckProgress = (deckId) =>
  client.get(`/decks/${deckId}/progress`).then((r) => r.data);

export const getDeckBreakdown = (deckId) =>
  client.get(`/decks/${deckId}/breakdown`).then((r) => r.data);

export const getDeckAnalytics = (deckId) =>
  client.get(`/decks/${deckId}/analytics`).then((r) => r.data);

export const searchDeckCards = (deckId, q) =>
  client.get(`/decks/${deckId}/cards/search`, { params: { q } }).then((r) => r.data);

export const deleteDeck = (deckId) => client.delete(`/decks/${deckId}`);

// ---------- Cards ----------
export const getDueCards = (deckId) => client.get(`/decks/${deckId}/due`).then((r) => r.data);

export const submitReview = (cardId, quality) =>
  client.post(`/cards/${cardId}/review`, { quality }).then((r) => r.data);

export const getCardHistory = (cardId) =>
  client.get(`/cards/${cardId}/history`).then((r) => r.data);

// ---------- Analytics ----------
export const getTodayAnalytics = () => client.get("/analytics/today").then((r) => r.data);

export default client;
