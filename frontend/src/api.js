// frontend/src/api.js
let API_BASE = "https://nexus-agent-7q8v.onrender.com";

if (typeof window !== "undefined" && (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1")) {
  API_BASE = "http://127.0.0.1:8000";
}
/**
 * Core Request Engine:
 * Handles URL assembly, JWT bearer injection, JSON serialization, and centralized error parsing.
 */
async function request(endpoint, { method = "GET", body, isFormData = false } = {}) {
  const token = localStorage.getItem("nexus_token");
  const headers = {};

  if (!isFormData) {
    headers["Content-Type"] = "application/json";
  }
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const config = {
    method,
    headers,
    body: isFormData ? body : (body ? JSON.stringify(body) : undefined),
  };

  const res = await fetch(`${API_BASE}${endpoint}`, config);

  if (!res.ok) {
    let errorDetail = `Request failed with status ${res.status}`;
    try {
      const errorJson = await res.json();
      errorDetail = errorJson.detail || errorJson.message || errorDetail;
    } catch {
      // Fallback if response body isn't JSON
    }
    throw new Error(errorDetail);
  }

  return res.json();
}

/**
 * Clean, Declarative API Catalog
 * All methods are 100% backward-compatible with your existing React pages.
 */
export const api = {
  // --- 1. Authentication ---
  register: (email, password) => 
    request("/api/auth/register", { method: "POST", body: { email, password } }),

  login: (email, password) => 
    request("/api/auth/login", { method: "POST", body: { email, password } }),

  getProfile: () => 
    request("/api/auth/me"),

  // --- 2. Resume & Matching ---
  matchResume: (file) => {
    const formData = new FormData();
    formData.append("file", file);
    return request("/api/resume/match?top_k=5", { method: "POST", body: formData, isFormData: true });
  },

  // --- 3. Shortlist (Anti-IDOR) ---
  getShortlist: () => 
    request("/api/me/shortlist"),

  saveToShortlist: (job_id, match_score, justification) => 
    request("/api/shortlist", { method: "POST", body: { job_id, match_score, justification } }),

  removeFromShortlist: (shortlistId) => 
    request(`/api/shortlist/${shortlistId}`, { method: "DELETE" }),

  // --- 4. Agent & ChatGPT-Style Sessions ---
  chatWithAgent: (message, history = [], session_id = null) => 
    request("/api/agent/chat", { method: "POST", body: { message, history, session_id } }),

  getChatSessions: () => 
    request("/api/agent/sessions"),

  createChatSession: () => 
    request("/api/agent/sessions", { method: "POST" }),

  getSessionMessages: (sessionId) => 
    request(`/api/agent/sessions/${sessionId}/messages`),

  deleteChatSession: (sessionId) => 
    request(`/api/agent/sessions/${sessionId}`, { method: "DELETE" }),

  getChatHistory: () => 
    request("/api/agent/history"),

  clearChatHistory: () => 
    request("/api/agent/history", { method: "DELETE" }),

  // --- 5. Asynchronous Briefing ---
  generateBriefing: () => 
    request("/api/briefing/generate", { method: "POST" }),

  getMyBriefings: () => 
    request("/api/me/briefings"),

  checkBriefingStatus: (jobId) => 
    request(`/api/briefing/status/${jobId}`),
  deleteBriefing: (jobId) => 
    request(`/api/briefing/${jobId}`, { method: "DELETE" }),

  getCosts: () => 
    request("/api/admin/costs"), 
};