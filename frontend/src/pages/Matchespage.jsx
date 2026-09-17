/* eslint-disable react-hooks/set-state-in-effect */
// frontend/src/pages/MatchesPage.jsx
import { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import {
  Upload, Sparkles, MapPin, ExternalLink, Bookmark, Check,
  Loader2, RotateCcw, Filter, Briefcase, ArrowUpRight, LogIn
} from 'lucide-react';
import { api } from '../api';

const CATEGORIES = [
  "All",
  "Software Engineering (SDE)",
  "AI & Machine Learning",
  "Quantitative & HFT",
  "Backend & Systems"
];

const categoryBadgeColor = (cat) => {
  switch (cat) {
    case 'Software Engineering (SDE)':
      return 'bg-blue-500/10 text-blue-400 border-blue-500/25';
    case 'AI & Machine Learning':
      return 'bg-purple-500/10 text-purple-400 border-purple-500/25';
    case 'Quantitative & HFT':
      return 'bg-amber-500/10 text-amber-400 border-amber-500/25';
    case 'Backend & Systems':
      return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/25';
    default:
      return 'bg-slate-800 text-slate-300 border-slate-700';
  }
};

export default function MatchesPage({ user }) {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [savedJobIds, setSavedJobIds] = useState(new Set());
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [browseJobs, setBrowseJobs] = useState([]);
  const [viewMode, setViewMode] = useState("matches");

  const [matches, setMatches] = useState([]);
  const [activeResumeName, setActiveResumeName] = useState('');

  useEffect(() => {
    if (!user) {
      setMatches([]);
      setActiveResumeName('');
      setFile(null);
      return;
    }

    try {
      const userKey = `nexus_matches_${user.email}`;
      const nameKey = `nexus_resume_name_${user.email}`;
      const cached = localStorage.getItem(userKey);
      setMatches(cached ? JSON.parse(cached) : []);
      setActiveResumeName(localStorage.getItem(nameKey) || '');
    } catch {
      setMatches([]);
      setActiveResumeName('');
    }
  }, [user]);

  // 2. Fetch all jobs for the browse tab
  useEffect(() => {
    let isMounted = true;
    const fetchBrowseJobs = async () => {
      try {
        const url = selectedCategory === "All"
          ? "http://127.0.0.1:8000/api/jobs?limit=102"
          : `http://127.0.0.1:8000/api/jobs?category=${encodeURIComponent(selectedCategory)}&limit=102`;
        const res = await fetch(url);
        if (res.ok) {
          const data = await res.json();
          if (isMounted) setBrowseJobs(data);
        }
      } catch (err) {
        console.error(err);
      }
    };

    fetchBrowseJobs();
    return () => { isMounted = false; };
  }, [selectedCategory]);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError('');
    }
  };

  const handleAnalyze = async () => {
    if (!file) {
      setError('Please select a PDF resume file first.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const res = await api.matchResume(file);
      const newMatches = res.matches || [];
      setMatches(newMatches);
      setActiveResumeName(file.name);
      setViewMode("matches");

      if (user) {
        localStorage.setItem(`nexus_matches_${user.email}`, JSON.stringify(newMatches));
        localStorage.setItem(`nexus_resume_name_${user.email}`, file.name);
      }
    } catch (err) {
      setError(err.message || 'Failed to analyze resume.');
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setMatches([]);
    setFile(null);
    setActiveResumeName('');
    if (user) {
      localStorage.removeItem(`nexus_matches_${user.email}`);
      localStorage.removeItem(`nexus_resume_name_${user.email}`);
    }
  };

  const handleShortlist = async (job) => {
    if (!user) {
      alert('Please sign in to save jobs to your private shortlist!');
      return;
    }
    try {
      const jobId = job.job_id || job.id;
      await api.saveToShortlist(jobId, job.match_score || null, job.justification || "Saved from browse");
      setSavedJobIds((prev) => new Set(prev).add(jobId));
    } catch (err) {
      alert(err.message);
    }
  };

  const filteredMatches = selectedCategory === "All"
    ? matches
    : matches.filter(m => m.category === selectedCategory);

  return (
    <div className="space-y-8 max-w-7xl mx-auto">

      {/* Hero Command Bar */}
      <div className="relative rounded-2xl bg-gradient-to-b from-slate-900/90 via-slate-900/70 to-slate-950/90 border border-slate-800/80 p-6 md:p-8 backdrop-blur-xl shadow-2xl overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2 max-w-xl">
            <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-[11px] font-semibold tracking-wide uppercase">
              <Sparkles className="w-3 h-3" />
              Dense Vector Retrieval & 4 Consolidated Sectors
            </div>
            <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
              Autonomous Career Intelligence
            </h1>
            <p className="text-slate-400 text-xs md:text-sm leading-relaxed">
              Match your resume against 102 verified tech opportunities or explore the categorized database below.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 flex-shrink-0">
            {user ? (
              <>
                <label className="cursor-pointer border border-slate-800 hover:border-slate-700 bg-slate-950/80 hover:bg-slate-900/60 rounded-xl px-4 py-3 flex items-center justify-between gap-3 transition-all group">
                  <Upload className="w-4 h-4 text-blue-400 group-hover:scale-110 transition-transform flex-shrink-0" />
                  <span className="text-xs text-slate-300 font-medium truncate max-w-[160px]">
                    {file ? file.name : activeResumeName ? activeResumeName : "Upload Resume PDF"}
                  </span>
                  <input type="file" accept="application/pdf" onChange={handleFileChange} className="hidden" />
                </label>

                <button
                  onClick={handleAnalyze}
                  disabled={loading}
                  className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-semibold text-xs px-5 py-3 rounded-xl shadow-lg shadow-blue-500/25 disabled:opacity-50 flex items-center justify-center gap-2 transition-all cursor-pointer"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      Analyzing...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-3.5 h-3.5" />
                      {matches.length > 0 ? "Re-Match" : "Run Match"}
                    </>
                  )}
                </button>

                {matches.length > 0 && (
                  <button
                    onClick={handleClear}
                    className="p-3 rounded-xl border border-slate-800 hover:border-red-500/30 text-slate-400 hover:text-red-400 transition-colors cursor-pointer"
                    title="Reset matches"
                  >
                    <RotateCcw className="w-4 h-4" />
                  </button>
                )}
              </>
            ) : (
              <NavLink
                to="/login"
                className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-semibold text-xs px-6 py-3.5 rounded-xl shadow-lg shadow-blue-500/20 flex items-center justify-center gap-2 transition-all cursor-pointer"
              >
                <LogIn className="w-4 h-4" />
                Sign in to Upload Resume & Match
              </NavLink>
            )}
          </div>
        </div>

        {error && (
          <p className="mt-4 text-red-400 text-xs bg-red-500/10 border border-red-500/20 px-3 py-2 rounded-lg">
            {error}
          </p>
        )}
      </div>

      {/* Filter Bar & View Toggle */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
        <div className="flex items-center gap-1.5 bg-slate-950 p-1 rounded-xl border border-slate-800/80">
          <button
            onClick={() => setViewMode("matches")}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${viewMode === "matches"
              ? "bg-slate-800 text-white shadow-sm"
              : "text-slate-400 hover:text-white"
              }`}
          >
            My Ranked Matches {matches.length > 0 && `(${matches.length})`}
          </button>
          <button
            onClick={() => setViewMode("browse")}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${viewMode === "browse"
              ? "bg-slate-800 text-white shadow-sm"
              : "text-slate-400 hover:text-white"
              }`}
          >
            Browse All ({browseJobs.length})
          </button>
        </div>

        <div className="flex flex-wrap items-center gap-1.5">
          <Filter className="w-3 h-3 text-slate-500 mr-1 flex-shrink-0" />
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`text-xs px-3 py-1.5 rounded-lg transition-all border ${selectedCategory === cat
                ? "bg-blue-600/15 text-blue-400 border-blue-500/40 shadow-sm font-semibold"
                : "bg-slate-950/40 text-slate-400 border-slate-800/60 hover:text-slate-200 hover:border-slate-700"
                }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* TWO CARDS PER ROW GRID (grid-cols-1 lg:grid-cols-2) */}
      {viewMode === "matches" ? (
        matches.length === 0 ? (
          <div className="text-center py-20 bg-slate-950/40 border border-slate-800/60 rounded-2xl p-8">
            <Briefcase className="w-10 h-10 text-slate-600 mx-auto mb-3" />
            <h3 className="text-sm font-bold text-white">No Active Match Session</h3>
            <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
              Upload your PDF resume above to see opportunities ranked by pgvector cosine similarity, or switch to "Browse All"!
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {filteredMatches.map((job, idx) => {
              const isSaved = savedJobIds.has(job.job_id);
              return (
                <div
                  key={job.job_id}
                  className="rounded-2xl bg-slate-900/40 hover:bg-slate-900/80 border border-slate-800/80 hover:border-blue-500/50 p-5 transition-all duration-200 hover:-translate-y-1 hover:shadow-xl hover:shadow-blue-500/10 flex flex-col justify-between group cursor-pointer"
                >
                  <div className="space-y-3">
                    {/* Top Row: Category, Rank, Score */}
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                          #{idx + 1}
                        </span>
                        {job.category && (
                          <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full border ${categoryBadgeColor(job.category)}`}>
                            {job.category}
                          </span>
                        )}
                      </div>

                      <div className="flex items-center gap-1 bg-gradient-to-r from-blue-600/20 to-indigo-600/20 border border-blue-500/30 px-2.5 py-0.5 rounded-lg">
                        <Sparkles className="w-3 h-3 text-blue-400" />
                        <span className="font-bold text-xs text-blue-300 font-mono">{job.match_score}</span>
                      </div>
                    </div>

                    {/* Title with Reactive Glow & Slide Effect on Hover */}
                    <div>
                      <h3 className="text-base font-bold text-white group-hover:text-blue-400 group-hover:translate-x-0.5 transition-all duration-200 line-clamp-1 flex items-center gap-1.5">
                        {job.title}
                        <ArrowUpRight className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 transition-opacity text-blue-400" />
                      </h3>
                      <span className="text-xs font-semibold text-slate-300">
                        @ {job.company}
                      </span>
                    </div>

                    {/* Metadata Badges */}
                    <div className="flex items-center gap-2 text-xs text-slate-400 flex-wrap">
                      {job.location && (
                        <span className="flex items-center gap-1 text-[11px]">
                          <MapPin className="w-3 h-3 text-slate-500" />
                          {job.location}
                        </span>
                      )}
                      {job.stipend && (
                        <span className="font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20 text-[11px]">
                          {job.stipend}
                        </span>
                      )}
                      {job.remote_ok && (
                        <span className="text-blue-400 text-[11px] font-medium bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20">
                          Remote
                        </span>
                      )}
                    </div>

                    {/* 1-Line Justification */}
                    <div className="bg-blue-950/20 border border-blue-800/30 rounded-lg p-2.5 text-xs text-blue-200/90 leading-relaxed italic">
                      <span className="font-semibold text-blue-400 not-italic mr-1.5">Why it fits:</span>
                      "{job.justification}"
                    </div>

                    {/* Skills */}
                    {job.required_skills && job.required_skills.length > 0 && (
                      <div className="flex flex-wrap gap-1 pt-1">
                        {job.required_skills.slice(0, 5).map((skill, sIdx) => (
                          <span
                            key={sIdx}
                            className="text-[10px] px-2 py-0.5 rounded bg-slate-950/60 text-slate-300 border border-slate-800"
                          >
                            {skill}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Actions Footer */}
                  <div className="flex items-center justify-between pt-4 mt-3 border-t border-slate-800/60">
                    <button
                      onClick={(e) => { e.stopPropagation(); handleShortlist(job); }}
                      disabled={isSaved}
                      className={`px-3 py-1.5 rounded-lg border text-xs font-medium flex items-center gap-1.5 transition-colors cursor-pointer ${isSaved
                        ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                        : 'border-slate-800 hover:border-amber-500/50 hover:bg-amber-500/10 text-slate-300'
                        }`}
                    >
                      {isSaved ? <Check className="w-3.5 h-3.5" /> : <Bookmark className="w-3.5 h-3.5" />}
                      <span>{isSaved ? "Saved" : "Shortlist"}</span>
                    </button>

                    <a
                      href={job.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={(e) => e.stopPropagation()}
                      className="px-3 py-1.5 rounded-lg bg-slate-800/60 hover:bg-slate-700 border border-slate-700/60 text-slate-300 hover:text-white text-xs font-medium flex items-center gap-1.5 transition-colors"
                    >
                      <span>Apply</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>

                </div>
              );
            })}
          </div>
        )
      ) : (
        // View Mode 2: Browse All
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {browseJobs.map((job) => {
            const isSaved = savedJobIds.has(job.id);
            return (
              <div
                key={job.id}
                className="rounded-2xl bg-slate-900/30 hover:bg-slate-900/70 border border-slate-800/80 hover:border-blue-500/50 p-5 transition-all duration-200 hover:-translate-y-1 hover:shadow-xl hover:shadow-blue-500/10 flex flex-col justify-between group cursor-pointer"
              >
                <div className="space-y-2.5">
                  <div className="flex items-center justify-between gap-2">
                    {job.category && (
                      <span className={`text-[10px] font-medium px-2.5 py-0.5 rounded-full border ${categoryBadgeColor(job.category)}`}>
                        {job.category}
                      </span>
                    )}
                    {job.stipend && (
                      <span className="font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20 text-[11px]">
                        {job.stipend}
                      </span>
                    )}
                  </div>

                  <div>
                    <h4 className="text-base font-bold text-white group-hover:text-blue-400 group-hover:translate-x-0.5 transition-all duration-200 line-clamp-1 flex items-center gap-1.5">
                      {job.title}
                      <ArrowUpRight className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 transition-opacity text-blue-400" />
                    </h4>
                    <span className="text-xs text-slate-400 font-medium">@ {job.company}</span>
                  </div>

                  <div className="flex items-center gap-3 text-xs text-slate-400">
                    {job.location && <span className="text-[11px] flex items-center gap-1"><MapPin className="w-3 h-3 text-slate-500" />{job.location}</span>}
                    {job.remote_ok && <span className="text-blue-400 text-[11px]">Remote</span>}
                  </div>

                  {job.required_skills && job.required_skills.length > 0 && (
                    <div className="flex flex-wrap gap-1 pt-1">
                      {job.required_skills.slice(0, 5).map((s, idx) => (
                        <span key={idx} className="text-[10px] bg-slate-950/60 text-slate-300 px-2 py-0.5 rounded border border-slate-800">
                          {s}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                <div className="flex items-center justify-between pt-4 mt-3 border-t border-slate-800/60">
                  <button
                    onClick={(e) => { e.stopPropagation(); handleShortlist(job); }}
                    disabled={isSaved}
                    className={`px-3 py-1.5 rounded-lg border text-xs font-medium flex items-center gap-1.5 transition-colors cursor-pointer ${isSaved
                      ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                      : 'border-slate-800 hover:border-amber-500/50 hover:bg-amber-500/10 text-slate-300'
                      }`}
                  >
                    {isSaved ? <Check className="w-3.5 h-3.5" /> : <Bookmark className="w-3.5 h-3.5" />}
                    <span>{isSaved ? "Saved" : "Shortlist"}</span>
                  </button>
                  <a
                    href={job.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={(e) => e.stopPropagation()}
                    className="px-3 py-1.5 rounded-lg bg-slate-800/60 hover:bg-slate-700 border border-slate-700/60 text-slate-300 hover:text-white text-xs font-medium flex items-center gap-1.5 transition-colors"
                  >
                    <span>Apply</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              </div>
            );
          })}
        </div>
      )}

    </div>
  );
}