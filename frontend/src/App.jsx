
import { useState } from "react";
import "./App.css";

const API_BASE = "https://citeverify-e20u.onrender.com";

async function readResponse(response) {
  const text = await response.text();
  let data;
  try {
    data = text ? JSON.parse(text) : {};
  } catch {
    throw new Error(`Server returned an invalid response (HTTP ${response.status}).`);
  }
  if (!response.ok) {
    const detail = data?.detail;
    const message = typeof detail === "string" ? detail : JSON.stringify(detail || data);
    throw new Error(message || `HTTP ${response.status}`);
  }
  return data;
}

function normalizeResults(payload) {
  const raw = Array.isArray(payload)
    ? payload
    : payload?.verification_results || payload?.results || payload?.verifications || [];

  if (!Array.isArray(raw)) return [];
  return raw.map((entry, index) => {
    const status = String(entry.status || entry.verdict || entry.verification_status || "Needs review");
    const evidence = entry.evidence || entry.supporting_evidence || entry.paper_abstract || "";
    const explanation =
  entry.explanation ||
  entry.verification_results?.[0]?.explanation ||
  entry.reason ||
  entry.message ||
  "No explanation was returned by the backend.";
    return {
      claim: typeof entry.claim === "string" ? entry.claim : entry.claim?.text || entry.claim_text || `Claim ${index + 1}`,
      status,
      evidence: typeof evidence === "string" ? evidence : JSON.stringify(evidence),
      highlight: typeof entry.highlight === "string" ? entry.highlight : "",
      explanation: typeof explanation === "string" ? explanation : JSON.stringify(explanation),
      citation: entry.citation_key || entry.citation || entry.doi || ""
    };
  });
}

function HighlightEvidence({ text, highlight }) {
  if (!highlight || !text.includes(highlight)) {
    return <p>{text || "Evidence unavailable. Independent review required."}</p>;
  }
  const index = text.indexOf(highlight);
  return (
    <p>
      {text.slice(0, index)}
      <mark>{highlight}</mark>
      {text.slice(index + highlight.length)}
    </p>
  );
}

function App() {
  const [file, setFile] = useState(null);
  const [showResults, setShowResults] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [stage, setStage] = useState("");
  const [results, setResults] = useState([]);
  const [documentId, setDocumentId] = useState("");
  const [uploadInfo, setUploadInfo] = useState(null);
  const [verificationData, setVerificationData] = useState(null);

  function handleFileChange(event) {
    const selected = event.target.files?.[0];
    setShowResults(false);
    setError("");
    setFile(null);
    setResults([]);
    setDocumentId("");
    setUploadInfo(null);
    setVerificationData(null);

    if (!selected) return;
    if (selected.type !== "application/pdf" && !selected.name.toLowerCase().endsWith(".pdf")) {
      setError("Please upload a PDF file only.");
      event.target.value = "";
      return;
    }
    if (selected.size > 10 * 1024 * 1024) {
      setError("PDF must be smaller than 10 MB.");
      event.target.value = "";
      return;
    }
    setFile(selected);
  }

  async function handleVerify() {
    if (!file || loading) return;
    setShowResults(false);
    setError("");
    setLoading(true);
    setResults([]);
    setStage("Uploading PDF and extracting citations...");

    try {
      const form = new FormData();
      form.append("file", file);

      const upload = await readResponse(
        await fetch(`${API_BASE}/upload-pdf`, {
          method: "POST",
          body: form
        })
      );
      const id = upload.document_id;
      if (!id) throw new Error("Backend did not return a document ID.");
      setDocumentId(id);
      setUploadInfo(upload);

      setStage("Verifying extracted claims against citations...");
      const verification = await readResponse(
        await fetch(`${API_BASE}/verify-document/${encodeURIComponent(id)}`, {
          method: "POST"
        })
      );
      setVerificationData(verification);

      let normalized = normalizeResults(verification);
      if (!normalized.length) {
        setStage("Loading saved verification results...");
        const documentData = await readResponse(
          await fetch(`${API_BASE}/documents/${encodeURIComponent(id)}`)
        );
        normalized = normalizeResults(documentData);
      }

      setResults(normalized);
      setShowResults(true);
    } catch (err) {
      setError(`Verification failed: ${err.message}`);
    } finally {
      setLoading(false);
      setStage("");
    }
  }

  function downloadReport() {
    const report = {
      project: "CiteVerify",
      note: "Results returned by CiteVerify backend; automated checks require independent review.",
      generatedAt: new Date().toISOString(),
      filename: file?.name,
      document_id: documentId,
      extraction: uploadInfo,
      verification: verificationData,
      results
    };
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "citeverify-verification-report.json";
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }

  const supportedCount = results.filter((result) =>
    ["supported", "verified"].includes(result.status.trim().toLowerCase())
  ).length;

  return (
    <div className="app">
      <h1>🔍 CiteVerify</h1>
      <h2>Don't Just Cite It. Prove It.</h2>
      <p>AI-Powered Scientific Claim and Citation Verification System</p>

      <section className="upload-section">
        <h3>📄 Upload Research Paper</h3>
        <input type="file" accept=".pdf,application/pdf" onChange={handleFileChange} />
        {error && <p className="error-message" role="alert">{error}</p>}
        {file && <p>Selected: <strong>{file.name}</strong></p>}
        <button disabled={!file || loading} onClick={handleVerify}>
          {loading ? "Analyzing..." : "Verify Research Paper"}
        </button>
        {loading && (
          <div className="loading-container" role="status">
            <div className="spinner"></div>
            <h3>🔍 Analyzing Research Paper...</h3>
            <p>{stage}</p>
          </div>
        )}
      </section>

      {showResults && (
        <section className="results">
          <h2>📊 Verification Results</h2>
          <p className="demo-notice">
            Results from your backend. Automated evidence checks may need independent review.
          </p>

          <div className="stats">
            <div>{results.length} Claims Checked</div>
            <div>{supportedCount} Supported</div>
            <div>{results.length - supportedCount} Need Attention</div>
          </div>
          {results.length === 0 && (
            <p>No individual verification results were returned. Check the backend response.</p>
          )}
          {results.map((result, index) => (
            <div className="result-card" key={index}>
              <h3>Claim {index + 1}</h3>
              <p>{result.claim}</p>
              <span className={`status ${result.status.toLowerCase().replaceAll(/[^a-z0-9]+/g, "-")}`}>
                {result.status}
              </span>
              {result.citation && <p><strong>Citation:</strong> {result.citation}</p>}
              <h4>📌 Evidence</h4>
              <HighlightEvidence text={result.evidence} highlight={result.highlight} />
              <p><strong>Explanation:</strong> {result.explanation}</p>
            </div>
          ))}
          <div className="download-section">
            <h3>📥 Verification Report</h3>
            <p>Download the results returned by your CiteVerify backend.</p>
            <button onClick={downloadReport}>⬇ Download Verification Report</button>
          </div>
        </section>
      )}

      <section className="story-section">
        <div className="story-animation" aria-hidden="true">
          <div className="story-halo"></div>
          <div className="story-paper">
            <div className="story-paper-lines"></div>
            <div className="story-check">✓</div>
          </div>
        </div>
        <h2>Every claim has a story.</h2>
        <p>Explore the relationship between scientific claims and their evidence.</p>
      </section>
    </div>
  );
}

export default App;
