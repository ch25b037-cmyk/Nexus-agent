// frontend/src/components/Navbar.jsx
import { useState, useEffect } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  Sparkles,
  Bot,
  Bookmark,
  LogIn,
  LogOut,
  Coins,
  X,
  Volume2,
  CheckCircle2,
  TrendingUp
} from 'lucide-react';
import { api } from '../api';

export default function Navbar({ user, onLogout }) {
  const navigate = useNavigate();
  const [costs, setCosts] = useState(null);
  const [showCostModal, setShowCostModal] = useState(false);

  useEffect(() => {
    if (!user) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setCosts(null);
      return;
    }

    let isMounted = true;

    const loadCosts = () => {
      api.getCosts()
        .then((data) => {
          if (isMounted) setCosts(data);
        })
        .catch(() => { });
    };

    loadCosts();
    const interval = setInterval(loadCosts, 8000);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [user]);

  const linkClass = ({ isActive }) =>
    `flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${isActive
      ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/25'
      : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
    }`;

  const getFeatureIcon = (feature) => {
    switch ((feature || '').toLowerCase()) {
      case 'matching':
        return <Sparkles className="w-4 h-4 text-blue-400" />;
      case 'briefing':
        return <Volume2 className="w-4 h-4 text-purple-400" />;
      case 'agent':
        return <Bot className="w-4 h-4 text-indigo-400" />;
      default:
        return <CheckCircle2 className="w-4 h-4 text-amber-400" />;
    }
  };

  const formatFeatureName = (f) => {
    switch ((f || '').toLowerCase()) {
      case 'matching':
        return 'Resume Semantic Matching';
      case 'briefing':
        return 'Executive Audio Briefing';
      case 'agent':
        return 'Agent Tool Calling & Chat';
      default:
        return (f || '').toUpperCase();
    }
  };

  return (
    <>
      <nav className="bg-slate-950/80 backdrop-blur-md border-b border-slate-800 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          {/* Brand Logo */}
          <div
            onClick={() => navigate('/')}
            className="flex items-center gap-3 cursor-pointer group"
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center font-black text-xl text-white shadow-lg shadow-blue-500/30 group-hover:scale-105 transition-transform">
              N
            </div>
            <div>
              <span className="font-bold text-lg tracking-wider text-white">NEXUS</span>
              <span className="block text-[10px] text-blue-400 font-semibold -mt-1 tracking-widest uppercase">
                Career Intelligence
              </span>
            </div>
          </div>

          {/* Navigation Routes */}
          <div className="flex items-center gap-2">
            <NavLink to="/" className={linkClass}>
              <Sparkles className="w-4 h-4 text-blue-400" />
              Resume Matches
            </NavLink>
            <NavLink to="/chat" className={linkClass}>
              <Bot className="w-4 h-4 text-indigo-400" />
              Agent Chat
            </NavLink>
            <NavLink to="/shortlist" className={linkClass}>
              <Bookmark className="w-4 h-4 text-amber-400" />
              Shortlist & Briefing
            </NavLink>
          </div>

          {/* Right Section */}
          <div className="flex items-center gap-4">
            {/* Badge (Only when user is logged in) */}
            {user && costs && (
              <button
                onClick={() => setShowCostModal(true)}
                className="hidden lg:flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/25 text-emerald-400 text-xs font-mono transition-all cursor-pointer shadow-sm group"
                title="View personal token and cost breakdown"
              >
                <Coins className="w-3.5 h-3.5 text-emerald-400 group-hover:rotate-12 transition-transform" />
                <span>{(costs.total_tokens || 0).toLocaleString()} tokens</span>
                <span className="text-emerald-300/30">|</span>
                <span className="font-bold">{costs.total_cost_inr || '₹0.00'}</span>
              </button>
            )}

            {user ? (
              <div className="flex items-center gap-3">
                <span className="text-xs text-slate-300 bg-slate-900 px-3 py-1.5 rounded-full border border-slate-800">
                  {user.email}
                </span>
                <button
                  onClick={onLogout}
                  className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-red-400 px-3 py-1.5 rounded-lg border border-slate-800 hover:border-red-500/30 transition-colors cursor-pointer"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  Logout
                </button>
              </div>
            ) : (
              <NavLink
                to="/login"
                className="flex items-center gap-2 bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-sm px-4 py-2 rounded-lg font-medium shadow-md shadow-blue-500/20 hover:from-blue-500 hover:to-indigo-500 transition-all"
              >
                <LogIn className="w-4 h-4" />
                Sign In
              </NavLink>
            )}
          </div>
        </div>
      </nav>

      {/* User-Scoped Modal */}
      {showCostModal && costs && user && (
        <div className="fixed inset-0 bg-black/75 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 w-full max-w-xl rounded-2xl p-6 shadow-2xl space-y-6 relative animate-in fade-in zoom-in-95 duration-150">
            {/* Modal Header */}
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-emerald-500/10 border border-emerald-500/25 flex items-center justify-center text-emerald-400">
                  <Coins className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white flex items-center gap-2">
                    Token & Cost Intelligence
                  </h3>
                  <p className="text-xs text-slate-400">
                    Account: <strong className="text-emerald-400">{user.email}</strong>
                  </p>
                </div>
              </div>
              <button
                onClick={() => setShowCostModal(false)}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Metric Summary */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-4">
                <span className="text-xs text-slate-400 block font-medium">Your Tokens Consumed</span>
                <span className="text-2xl font-black text-white font-mono mt-1 block">
                  {(costs.total_tokens || 0).toLocaleString()}
                </span>
                <span className="text-[11px] text-slate-500 mt-0.5 block">Isolated to your account</span>
              </div>

              <div className="bg-emerald-950/20 border border-emerald-500/30 rounded-xl p-4">
                <span className="text-xs text-emerald-400 block font-medium">Your Cost in INR (₹)</span>
                <span className="text-2xl font-black text-emerald-300 font-mono mt-1 block">
                  {costs.total_cost_inr || '₹0.00'}
                </span>
                <span className="text-[11px] text-emerald-400/60 mt-0.5 block">USD to INR @ ₹83.50 / $</span>
              </div>
            </div>

            {/* Feature Breakdown */}
            <div className="space-y-2.5">
              <span className="text-xs font-bold text-slate-300 uppercase tracking-wider block">
                Your Spend Per Feature
              </span>

              {costs.features && costs.features.length > 0 ? (
                <div className="space-y-2">
                  {costs.features.map((f, idx) => (
                    <div
                      key={idx}
                      className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-3.5 flex items-center justify-between text-xs"
                    >
                      <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-slate-900 border border-slate-800">
                          {getFeatureIcon(f.feature)}
                        </div>
                        <div>
                          <span className="font-semibold text-white block">
                            {formatFeatureName(f.feature)}
                          </span>
                          <span className="text-[11px] text-slate-400 font-mono">
                            {(f.tokens || 0).toLocaleString()} tokens
                          </span>
                        </div>
                      </div>

                      <div className="text-right">
                        <span className="font-bold text-emerald-400 font-mono block text-sm">
                          {f.cost_inr}
                        </span>
                        <span className="text-[10px] text-slate-500 uppercase tracking-wider">
                          Incurred Cost
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-500 text-center py-4">
                  No API calls recorded for this account yet.
                </p>
              )}
            </div>

            {/* Modal Footer */}
            <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-500">
              <span className="flex items-center gap-1">
                <TrendingUp className="w-3.5 h-3.5 text-blue-400" />
                Multi-tenant session isolation in PostgreSQL (`token_usage`)
              </span>
              <button
                onClick={() => setShowCostModal(false)}
                className="bg-slate-800 hover:bg-slate-700 text-white px-4 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}