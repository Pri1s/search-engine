import { useState } from "react";

const API_URL = "http://localhost:8000/search";

function previewOf(content) {
  const snippet = content.slice(0, 200);
  return snippet.length < content.length ? snippet + "…" : snippet;
}

export default function App() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [status, setStatus] = useState("");

  async function handleSearch(e) {
    e.preventDefault();
    const q = query.trim();
    if (!q) return;

    setStatus("Searching…");
    setResults([]);
    try {
      const res = await fetch(`${API_URL}?q=${encodeURIComponent(q)}`);
      if (!res.ok) throw new Error(`Request failed: ${res.status}`);
      const docs = await res.json();
      setResults(docs);
      setStatus(docs.length === 0 ? "No results found." : "");
    } catch (err) {
      setStatus(`Error: ${err.message}`);
    }
  }

  return (
    <div className="page">
      <h1>Basketball Search</h1>
      <form onSubmit={handleSearch}>
        <input
          type="text"
          placeholder="Search basketball articles..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          autoFocus
        />
        <button type="submit">Search</button>
      </form>

      {status && <p className="status">{status}</p>}

      <div className="results">
        {results.map((doc) => (
          <div className="result" key={doc.id}>
            <a href={doc.url} target="_blank" rel="noopener noreferrer">
              {doc.title}
            </a>
            <span className="url">{doc.url}</span>
            <p className="preview">{previewOf(doc.content)}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
