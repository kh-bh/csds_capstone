import { useEffect, useRef, useState } from "react";
import { Bot, ChevronDown, Send, Sparkles, Square, User } from "lucide-react";

import "./RagChatPage.css";

const API_URL =
  import.meta.env.VITE_RAG_API_URL || "http://localhost:8000/api/rag/stream";

// Edit these to match the categories stored in your Pinecone metadata.
const CATEGORY_OPTIONS = [
  "Admin, Billing & Communication",
  "Wait Times & Patient Care",
  "Specialized & Pediatric Care",
  "Facility Amenities & Cleanliness",
  "Critical & Acute Clinical Conditions",
  "ER & Family Treatment Experience",
  "Positive Staff Praise & Gratitude"
];

const SUGGESTIONS = [
  "What complaints do patients have regarding billing and rude staff?",
  "How do patients describe wait times in the emergency room?",
  "What do patients say about communication with doctors?",
];

const EMPTY_FILTERS = {
  googleName: "",
  city: "",
  state: "",
  zip: "",
  minRating: "",
  maxRating: "",
  topK: 4,
  categories: [],
};

// "Cleveland, Akron" -> ["Cleveland", "Akron"]
const splitList = (value) =>
  value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);

function buildPayload(question, filters) {
  const payload = { question, top_k: Number(filters.topK) || 4 };

  const lists = {
    google_name: splitList(filters.googleName),
    city: splitList(filters.city),
    state: splitList(filters.state).map((s) => s.toUpperCase()),
    zip_code: splitList(filters.zip),
    operational_category: filters.categories,
  };
  Object.entries(lists).forEach(([key, list]) => {
    if (list.length) payload[key] = list;
  });

  if (filters.minRating !== "") payload.min_rating = Number(filters.minRating);
  if (filters.maxRating !== "") payload.max_rating = Number(filters.maxRating);

  return payload;
}

function activeFilterCount(filters) {
  return [
    filters.googleName,
    filters.city,
    filters.state,
    filters.zip,
    filters.minRating,
    filters.maxRating,
  ].filter((v) => v !== "").length + (filters.categories.length ? 1 : 0);
}

function Sources({ sources }) {
  const [open, setOpen] = useState(false);
  if (!sources?.length) return null;

  return (
    <div className="rag-sources">
      <button
        type="button"
        className="rag-sources-toggle"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
      >
        <ChevronDown size={15} className={open ? "rotated" : ""} />
        {sources.length} source review{sources.length === 1 ? "" : "s"}
      </button>

      {open && (
        <ul>
          {sources.map((s) => (
            <li key={s.id}>
              <div className="rag-source-head">
                <strong>{s.hospital || "Unknown hospital"}</strong>
                <span>
                  {[s.city, s.state].filter(Boolean).join(", ")}
                  {s.rating != null && ` · ${s.rating}★`}
                </span>
              </div>
              {s.category && <span className="rag-tag">{s.category}</span>}
              <p>{s.text}</p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function Message({ message }) {
  const isUser = message.role === "user";
  const waiting = !isUser && message.streaming && !message.content;

  return (
    <div className={`rag-message ${isUser ? "user" : "assistant"}`}>
      <div className="rag-avatar">
        {isUser ? <User size={18} /> : <Bot size={18} />}
      </div>

      <div className="rag-bubble">
        {waiting ? (
          <span className="rag-typing" aria-label="Thinking">
            <i />
            <i />
            <i />
          </span>
        ) : (
          <p className="rag-text">
            {message.content}
            {message.streaming && <span className="rag-cursor" />}
          </p>
        )}

        {message.error && <p className="rag-error">{message.error}</p>}
        {!isUser && <Sources sources={message.sources} />}
      </div>
    </div>
  );
}

export default function RagChatPage() {
  const [filters, setFilters] = useState(EMPTY_FILTERS);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const abortRef = useRef(null);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages]);

  useEffect(() => () => abortRef.current?.abort(), []);

  const setField = (field) => (event) =>
    setFilters((f) => ({ ...f, [field]: event.target.value }));

  const toggleCategory = (category) =>
    setFilters((f) => ({
      ...f,
      categories: f.categories.includes(category)
        ? f.categories.filter((c) => c !== category)
        : [...f.categories, category],
    }));

  // Updates the last (assistant) message in place.
  const patchAssistant = (updater) =>
    setMessages((prev) => {
      const next = [...prev];
      const last = next[next.length - 1];
      next[next.length - 1] = { ...last, ...updater(last) };
      return next;
    });

  async function sendQuestion(rawQuestion) {
    const question = rawQuestion.trim();
    if (!question || loading) return;

    setInput("");
    setLoading(true);
    setMessages((prev) => [
      ...prev,
      { role: "user", content: question },
      { role: "assistant", content: "", streaming: true, sources: [] },
    ]);

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const response = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(buildPayload(question, filters)),
        signal: controller.signal,
      });
      if (!response.ok || !response.body) {
        throw new Error(`Server responded with ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      const handleEvent = (event) => {
        if (event.type === "sources") {
          patchAssistant(() => ({ sources: event.sources }));
        } else if (event.type === "token") {
          patchAssistant((m) => ({ content: m.content + event.text }));
        } else if (event.type === "error") {
          patchAssistant(() => ({ error: event.message }));
        }
      };

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop(); // keep any partial line for the next chunk

        for (const line of lines) {
          if (line.trim()) handleEvent(JSON.parse(line));
        }
      }
      if (buffer.trim()) handleEvent(JSON.parse(buffer));
    } catch (err) {
      if (err.name !== "AbortError") {
        patchAssistant(() => ({
          error: `Couldn't reach the review assistant. Is the backend running? (${err.message})`,
        }));
      }
    } finally {
      patchAssistant(() => ({ streaming: false }));
      setLoading(false);
      abortRef.current = null;
    }
  }

  const handleSubmit = (event) => {
    event.preventDefault();
    sendQuestion(input);
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendQuestion(input);
    }
  };

  const filterCount = activeFilterCount(filters);

  return (
    <main className="rag-page">
      <section className="rag-header">
        <p className="eyebrow">REVIEW INSIGHTS</p>
        <h1>Ask about patient experiences</h1>
        <p>
          Narrow down the reviews with filters, then ask a question. Answers are
          generated only from the matching patient reviews.
        </p>
      </section>

      <section className="rag-filters" aria-label="Review filters">
        <div className="rag-filters-title">
          <h2>Filters</h2>
          {filterCount > 0 && (
            <>
              <span className="rag-badge">{filterCount} active</span>
              <button
                type="button"
                className="rag-link-button"
                onClick={() => setFilters(EMPTY_FILTERS)}
              >
                Clear all
              </button>
            </>
          )}
        </div>

        <div className="rag-filter-grid">
          <label>
            Hospital name(s)
            <input
              value={filters.googleName}
              onChange={setField("googleName")}
              placeholder="e.g. Cleveland Clinic"
            />
          </label>
          <label>
            City
            <input
              value={filters.city}
              onChange={setField("city")}
              placeholder="e.g. Cleveland, Akron"
            />
          </label>
          <label>
            State
            <input
              value={filters.state}
              onChange={setField("state")}
              placeholder="e.g. OH"
            />
          </label>
          <label>
            ZIP code(s)
            <input
              value={filters.zip}
              onChange={setField("zip")}
              placeholder="e.g. 44106"
            />
          </label>
          <label>
            Min rating
            <select value={filters.minRating} onChange={setField("minRating")}>
              <option value="">Any</option>
              {[1, 2, 3, 4, 5].map((n) => (
                <option key={n} value={n}>
                  {n} ★
                </option>
              ))}
            </select>
          </label>
          <label>
            Max rating
            <select value={filters.maxRating} onChange={setField("maxRating")}>
              <option value="">Any</option>
              {[1, 2, 3, 4, 5].map((n) => (
                <option key={n} value={n}>
                  {n} ★
                </option>
              ))}
            </select>
          </label>
          <label>
            Reviews to retrieve
            <input
              type="number"
              min={1}
              max={10}
              value={filters.topK}
              onChange={setField("topK")}
            />
          </label>
        </div>

        <div className="rag-categories">
          <span>Category</span>
          <div>
            {CATEGORY_OPTIONS.map((category) => (
              <button
                key={category}
                type="button"
                className={`rag-chip ${
                  filters.categories.includes(category) ? "selected" : ""
                }`}
                onClick={() => toggleCategory(category)}
                aria-pressed={filters.categories.includes(category)}
              >
                {category}
              </button>
            ))}
          </div>
        </div>

        <p className="rag-hint">
          Separate multiple values with commas. Leave a field blank to ignore it.
        </p>
      </section>

      <section className="rag-chat">
        <div className="rag-thread" aria-live="polite">
          {messages.length === 0 ? (
            <div className="rag-empty">
              <Sparkles size={28} />
              <h2>What would you like to know?</h2>
              <div className="rag-suggestions">
                {SUGGESTIONS.map((s) => (
                  <button key={s} type="button" onClick={() => sendQuestion(s)}>
                    {s}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((m, i) => <Message key={i} message={m} />)
          )}
          <div ref={bottomRef} />
        </div>

        <form className="rag-composer" onSubmit={handleSubmit}>
          <textarea
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about hospital reviews…"
            aria-label="Your question"
          />
          {loading ? (
            <button
              type="button"
              className="rag-send stop"
              onClick={() => abortRef.current?.abort()}
              aria-label="Stop generating"
            >
              <Square size={16} />
            </button>
          ) : (
            <button
              type="submit"
              className="rag-send"
              disabled={!input.trim()}
              aria-label="Send"
            >
              <Send size={18} />
            </button>
          )}
        </form>
      </section>
    </main>
  );
}
