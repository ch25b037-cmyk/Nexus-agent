// frontend/src/pages/ShortlistPage.jsx
import { useState, useEffect } from 'react';
import { Bookmark, Volume2, Trash2, ExternalLink, Loader2, Clock, History, Mic } from 'lucide-react';
import { api } from '../api';

export default function ShortlistPage({ user }) {
  const [shortlist, setShortlist] = useState([]);
  const [loading, setLoading] = useState(true);

  // Briefing state
  const [generatingBriefing, setGeneratingBriefing] = useState(false);
  const [briefingStatus, setBriefingStatus] = useState('');
  const [briefingData, setBriefingData] = useState(() => {
    try {
      const cached = localStorage.getItem('nexus_latest_briefing');
      return cached ? JSON.parse(cached) : null;
    } catch {
      return null;
    }
  });
  const [pastBriefings, setPastBriefings] = useState([]);

  // Fetch Shortlist and Past Briefings on mount / user change (0 ESLint errors!)
  useEffect(() => {
    let isMounted = true;

    const loadUserData = async () => {
      if (!user) {
        setLoading(false);
        return;
      }
      try {
        const [shortlistItems, briefingsList] = await Promise.all([
          api.getShortlist(),
          api.getMyBriefings()
        ]);

        if (isMounted) {
          setShortlist(shortlistItems || []);
          setPastBriefings(briefingsList || []);

          // Pick the latest completed briefing if none is active
          if (!briefingData && briefingsList && briefingsList.length > 0) {
            const latest = briefingsList.find(b => b.status === 'completed');
            if (latest) {
              setBriefingData(latest);
              localStorage.setItem('nexus_latest_briefing', JSON.stringify(latest));
            }
          }
        }
      } catch (err) {
        console.error("Failed to load user data:", err);
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    loadUserData();

    return () => {
      isMounted = false;
    };
  }, [user]);

  const handleRemove = async (id) => {
    try {
      await api.removeFromShortlist(id);
      setShortlist((prev) => prev.filter((item) => item.id !== id));
    } catch (err) {
      alert(err.message);
    }
  };

  const handleGenerateBriefing = async () => {
    if (!user) {
      alert('Please sign in to generate a personalized briefing.');
      return;
    }

    setGeneratingBriefing(true);
    setBriefingStatus('queued');

    try {
      const res = await api.generateBriefing();
      const jobId = res.job_id;

      // Poll every 3 seconds
      const interval = setInterval(async () => {
        try {
          const pollRes = await api.checkBriefingStatus(jobId);
          setBriefingStatus(pollRes.status);

          if (pollRes.status === 'completed' || pollRes.status === 'failed') {
            clearInterval(interval);
            setGeneratingBriefing(false);

            if (pollRes.status === 'completed') {
              setBriefingData(pollRes);
              localStorage.setItem('nexus_latest_briefing', JSON.stringify(pollRes));
              api.getMyBriefings().then(setPastBriefings);
            }
          }
        } catch (pollErr) {
          console.error(pollErr);
          clearInterval(interval);
          setGeneratingBriefing(false);
        }
      }, 3000);

    } catch (err) {
      alert(err.message);
      setGeneratingBriefing(false);
    }
  };

  if (!user) {
    return (
      <div className="text-center py-20 bg-slate-900/40 border border-slate-800 rounded-2xl p-8">
        <Bookmark className="w-12 h-12 text-slate-600 mx-auto mb-4" />
        <h2 className="text-xl font-bold text-white">Private Shortlist & Briefings</h2>
        <p className="text-sm text-slate-400 mt-2">Sign in to save opportunities and generate your personalized morning briefing.</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">

      {/* Briefing Generator Card */}
      <div className="bg-gradient-to-br from-blue-950/60 via-slate-900 to-indigo-950/40 border border-blue-800/40 rounded-2xl p-8 shadow-2xl relative overflow-hidden">
        <div className="max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-semibold uppercase tracking-wider mb-4">
            <Volume2 className="w-3.5 h-3.5" />
            Asynchronous Non-Blocking Briefing
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold text-white">
            Your Executive Career Briefing
          </h2>
          <p className="mt-2 text-slate-300 text-sm leading-relaxed">
            Generate an AI-spoken audio briefing summarizing your top matches, compensation, and deadlines. Powered by neural voice synthesis.
          </p>

          {/* Glowing Studio Mic Action Button */}
          <div className="mt-7 flex flex-col sm:flex-row items-start sm:items-center gap-4">
            <div className="relative group">
              {/* Outer Ambient Glow Halo */}
              <div className={`absolute -inset-1 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl blur-md transition duration-300 ${generatingBriefing
                  ? 'opacity-100 animate-pulse'
                  : 'opacity-50 group-hover:opacity-100'
                }`} />

              {/* The Glowing Button */}
              <button
                onClick={handleGenerateBriefing}
                disabled={generatingBriefing}
                className="relative bg-gradient-to-r from-blue-600 via-indigo-600 to-blue-500 text-white font-bold text-xs md:text-sm px-6 py-3.5 rounded-2xl shadow-xl shadow-blue-500/30 hover:shadow-blue-500/50 hover:scale-[1.02] active:scale-[0.98] transition-all duration-200 disabled:opacity-60 flex items-center gap-3 cursor-pointer border border-blue-400/40"
              >
                {/* Glowing Mic Icon Badge */}
                <div className={`w-8 h-8 rounded-xl bg-blue-500/20 border border-blue-300/40 flex items-center justify-center text-blue-200 shadow-inner group-hover:bg-blue-400 group-hover:text-slate-950 transition-all ${generatingBriefing ? 'animate-bounce' : ''
                  }`}>
                  <Mic className="w-4 h-4" />
                </div>

                {generatingBriefing ? (
                  <span className="flex items-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin text-blue-200" />
                    <span>Broadcasting: {briefingStatus.toUpperCase()}...</span>
                  </span>
                ) : (
                  <span>{briefingData ? "Regenerate Voice Briefing" : "Generate Voice Briefing"}</span>
                )}
              </button>
            </div>

            {generatingBriefing && (
              <div className="flex items-center gap-2 text-xs text-blue-400 font-medium animate-pulse bg-blue-950/40 border border-blue-800/40 px-3.5 py-2 rounded-xl">
                <span className="w-2 h-2 rounded-full bg-blue-400 animate-ping" />
                <span>AI Presenter synthesizing audio...</span>
              </div>
            )}
          </div>
          {/* Active Audio Player */}
          {briefingData && briefingData.media_url && (
            <div className="mt-6 bg-slate-900/80 border border-blue-500/30 rounded-xl p-5 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-blue-400 uppercase tracking-wider flex items-center gap-1.5">
                  <Volume2 className="w-4 h-4" /> Latest Briefing
                </span>
                <span className="text-[11px] text-slate-400">Audio Briefing (MP3)</span>
              </div>

              <audio
                controls
                src={`http://127.0.0.1:8000${briefingData.media_url}`}
                className="w-full h-10 rounded-lg outline-none"
              />

              {briefingData.script && (
                <p className="text-xs text-slate-300 italic bg-slate-950/60 p-3 rounded-lg border border-slate-800">
                  "{briefingData.script}"
                </p>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Past Briefings History */}
      {pastBriefings.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-bold text-slate-300 flex items-center gap-2">
            <History className="w-4 h-4 text-blue-400" />
            Past Briefings History ({pastBriefings.length})
          </h3>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {pastBriefings.map((b) => (
              <div
                key={b.job_id}
                onClick={() => {
                  setBriefingData(b);
                  localStorage.setItem('nexus_latest_briefing', JSON.stringify(b));
                }}
                className={`p-3.5 rounded-xl border transition-all cursor-pointer flex items-center justify-between ${briefingData?.job_id === b.job_id
                    ? 'bg-blue-600/15 border-blue-500/40 shadow-sm'
                    : 'bg-slate-900/40 border-slate-800 hover:border-slate-700'
                  }`}
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center text-blue-400">
                    <Volume2 className="w-4 h-4" />
                  </div>
                  <div>
                    <span className="text-xs font-semibold text-white block truncate max-w-[140px]">
                      Briefing #{b.job_id.slice(0, 8)}
                    </span>
                    <span className="text-[10px] text-slate-400 flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {new Date(b.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
                <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
                  {b.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Shortlist Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-xl font-bold text-white flex items-center gap-2">
            <Bookmark className="w-5 h-5 text-amber-400" />
            My Saved Listings ({shortlist.length})
          </h3>
          <span className="text-xs text-slate-400">Strictly Isolated to User Session</span>
        </div>

        {loading ? (
          <div className="text-center py-12 text-slate-500">Loading shortlist...</div>
        ) : shortlist.length === 0 ? (
          <div className="text-center py-12 bg-slate-900/40 border border-slate-800 rounded-xl text-slate-400 text-sm">
            No saved listings yet. Go to <strong className="text-white">Resume Matches</strong> and click Shortlist on roles you like!
          </div>
        ) : (
          <div className="grid gap-4">
            {shortlist.map((item) => (
              <div
                key={item.id}
                className="bg-slate-900/50 border border-slate-800/80 rounded-xl p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <h4 className="font-bold text-white">{item.job?.title || "Untitled Role"}</h4>
                    <span className="text-sm text-slate-400">@ {item.job?.company || "Unknown"}</span>
                    {item.match_score && (
                      <span className="text-xs bg-blue-500/10 border border-blue-500/20 text-blue-400 px-2 py-0.5 rounded font-mono font-semibold">
                        {item.match_score}
                      </span>
                    )}
                  </div>
                  {item.justification && (
                    <p className="text-xs text-slate-400 italic">"{item.justification}"</p>
                  )}
                  <p className="text-xs text-slate-500">
                    Location: {item.job?.location || 'Remote'} | Stipend: {item.job?.stipend || 'Competitive'}
                  </p>
                </div>

                <div className="flex items-center gap-2 flex-shrink-0">
                  {item.job?.source_url && (
                    <a
                      href={item.job.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 transition-colors"
                      title="Open External URL"
                    >
                      <ExternalLink className="w-4 h-4" />
                    </a>
                  )}
                  <button
                    onClick={() => handleRemove(item.id)}
                    className="p-2 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30 transition-colors cursor-pointer"
                    title="Remove from shortlist"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

    </div>
  );
}