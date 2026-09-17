// frontend/src/pages/ChatPage.jsx
import { useState, useRef, useEffect } from 'react';
import { Bot, Send, User, Sparkles, Loader2, Plus, MessageSquare, Trash2, Menu, X } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { api } from '../api';

const DEFAULT_MESSAGE = {
  role: 'assistant',
  content: "Hello! I'm NEXUS, your Autonomous Career Intelligence Agent. I can query our live database through 6 specialized tools. Ask me about in-demand skills, analyze your skill gap for a company, search by tech stack, or find highest-paying roles!"
};

export default function ChatPage({ user }) {
  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [messages, setMessages] = useState([DEFAULT_MESSAGE]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (!user) return;
    const fetchSessions = async () => {
      try {
        const list = await api.getChatSessions();
        setSessions(list || []);
        if (list && list.length > 0) {
          selectSession(list[0].id);
        } else {
          handleNewChat();
        }
      } catch (err) {
        console.error("Could not fetch sessions:", err);
      }
    };
    fetchSessions();
  }, [user]);

  const selectSession = async (sessionId) => {
    setCurrentSessionId(sessionId);
    setMobileSidebarOpen(false); // Close mobile drawer when selected
    try {
      const history = await api.getSessionMessages(sessionId);
      if (history && history.length > 0) {
        setMessages([DEFAULT_MESSAGE, ...history]);
      } else {
        setMessages([DEFAULT_MESSAGE]);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleNewChat = async () => {
    setMobileSidebarOpen(false);
    if (!user) {
      setMessages([DEFAULT_MESSAGE]);
      setCurrentSessionId(null);
      return;
    }
    try {
      const newSession = await api.createChatSession();
      setSessions((prev) => [newSession, ...prev]);
      setCurrentSessionId(newSession.id);
      setMessages([DEFAULT_MESSAGE]);
    } catch (err) {
      console.error(err);
    }
  };

  const handleDeleteSession = async (e, sessionId) => {
    e.stopPropagation();
    try {
      await api.deleteChatSession(sessionId);
      const remaining = sessions.filter((s) => s.id !== sessionId);
      setSessions(remaining);
      if (currentSessionId === sessionId) {
        if (remaining.length > 0) {
          selectSession(remaining[0].id);
        } else {
          handleNewChat();
        }
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleSend = async (messageText = input) => {
    const text = messageText.trim();
    if (!text || loading) return;

    const userMessage = { role: 'user', content: text };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const res = await api.chatWithAgent(text, messages, currentSessionId);
      setMessages((prev) => [...prev, { role: 'assistant', content: res.reply }]);
      if (user) {
        api.getChatSessions().then(setSessions);
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: `[!] Error communicating with agent: ${err.message}` }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const quickPrompts = [
    "What are the top 5 most in-demand skills?",
    "What are the highest paying internships available?",
    "I know Python and FastAPI. What skills am I missing for Citadel (Job ID 104)?",
    "Show me remote roles in Backend & Cloud Systems"
  ];

  return (
    <div className="w-full h-[calc(100vh-6.5rem)] flex bg-slate-900/50 border border-slate-800/80 rounded-2xl overflow-hidden backdrop-blur-2xl shadow-2xl relative">

      {/* MOBILE BACKDROP OVERLAY */}
      {mobileSidebarOpen && (
        <div
          onClick={() => setMobileSidebarOpen(false)}
          className="md:hidden fixed inset-0 bg-black/70 backdrop-blur-sm z-40 animate-in fade-in"
        />
      )}

      {/* SESSIONS SIDEBAR: Responsive Drawer on Mobile, Fixed 72 on Desktop */}
      <div className={`
        fixed md:static inset-y-0 left-0 z-50 md:z-auto
        w-72 bg-slate-950/95 md:bg-slate-950/80 border-r border-slate-800/80 
        flex flex-col flex-shrink-0 transition-transform duration-200 ease-in-out
        ${mobileSidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
      `}>

        {/* + New Chat Header */}
        <div className="p-4 border-b border-slate-800/60 flex items-center justify-between gap-2">
          <button
            onClick={handleNewChat}
            className="flex-1 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-xs font-semibold px-4 py-2.5 rounded-xl shadow-lg shadow-blue-500/20 flex items-center justify-center gap-2 transition-all cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            New Conversation
          </button>
          <button
            onClick={() => setMobileSidebarOpen(false)}
            className="md:hidden p-2 text-slate-400 hover:text-white"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Sessions List */}
        <div className="flex-1 overflow-y-auto p-3 space-y-1">
          {!user ? (
            <div className="p-4 text-center text-xs text-slate-500">
              Sign in to save conversation threads.
            </div>
          ) : sessions.length === 0 ? (
            <div className="p-4 text-center text-xs text-slate-500">
              No conversations yet.
            </div>
          ) : (
            sessions.map((s) => {
              const isActive = s.id === currentSessionId;
              return (
                <div
                  key={s.id}
                  onClick={() => selectSession(s.id)}
                  className={`group flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-medium cursor-pointer transition-all ${isActive
                    ? 'bg-blue-600/20 text-blue-300 border border-blue-500/30 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/80 border border-transparent'
                    }`}
                >
                  <div className="flex items-center gap-2.5 truncate">
                    <MessageSquare className={`w-3.5 h-3.5 flex-shrink-0 ${isActive ? 'text-blue-400' : 'text-slate-500'}`} />
                    <span className="truncate max-w-[170px]">{s.title || "New Chat"}</span>
                  </div>

                  <button
                    onClick={(e) => handleDeleteSession(e, s.id)}
                    className="opacity-0 group-hover:opacity-100 hover:text-red-400 p-1 rounded transition-opacity"
                    title="Delete Chat"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              );
            })
          )}
        </div>

        <div className="p-3 border-t border-slate-800/60 text-[11px] text-slate-500 text-center">
          Cloud-Synced Conversations
        </div>
      </div>

      {/* RIGHT MAIN CHAT AREA */}
      <div className="flex-1 flex flex-col min-w-0 bg-transparent">

        {/* Chat Header with Mobile Toggle */}
        <div className="bg-slate-950/60 px-4 md:px-6 py-3 border-b border-slate-800/60 flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* Mobile Hamburger Button */}
            <button
              onClick={() => setMobileSidebarOpen(true)}
              className="md:hidden p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:text-white"
              title="Toggle Conversations"
            >
              <Menu className="w-4 h-4" />
            </button>

            <div className="w-8 h-8 rounded-lg bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 flex-shrink-0">
              <Bot className="w-4 h-4" />
            </div>
            <div className="truncate">
              <h2 className="text-sm font-bold text-white flex items-center gap-2">
                NEXUS Career Intelligence Agent
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse flex-shrink-0" />
              </h2>
              <p className="text-[11px] text-slate-400 truncate">6 Database Tools Active</p>
            </div>
          </div>
        </div>

        {/* Messages Stream */}
        <div className="flex-1 overflow-y-auto p-4 md:p-8 space-y-6">
          <div className="max-w-4xl mx-auto space-y-6">
            {messages.map((m, idx) => {
              const isUser = m.role === 'user';
              return (
                <div key={idx} className={`flex gap-3 md:gap-4 ${isUser ? 'justify-end' : 'justify-start'}`}>
                  {!isUser && (
                    <div className="w-7 h-7 md:w-8 md:h-8 rounded-lg bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 flex-shrink-0 mt-0.5">
                      <Bot className="w-3.5 h-3.5 md:w-4 md:h-4" />
                    </div>
                  )}

                  <div
                    className={`max-w-[90%] md:max-w-[85%] rounded-2xl px-4 md:px-6 py-3.5 text-sm leading-relaxed ${isUser
                      ? 'bg-blue-600 text-white rounded-br-xs shadow-md shadow-blue-500/20'
                      : 'bg-slate-800/80 text-slate-200 border border-slate-700/60 rounded-bl-xs shadow-md'
                      }`}
                  >
                    {isUser ? (
                      m.content
                    ) : (
                      <div className="space-y-3 text-sm leading-relaxed overflow-x-auto">
                        <ReactMarkdown
                          remarkPlugins={[remarkGfm]}
                          components={{
                            table: ({ children }) => (
                              <div className="overflow-x-auto my-3 rounded-lg border border-slate-700">
                                <table className="w-full text-left border-collapse text-xs">{children}</table>
                              </div>
                            ),
                            thead: ({ children }) => (
                              <thead className="bg-slate-900 border-b border-slate-700 text-blue-400 font-semibold">{children}</thead>
                            ),
                            th: ({ children }) => (
                              <th className="px-3 py-2 border-r border-slate-700 last:border-none">{children}</th>
                            ),
                            td: ({ children }) => (
                              <td className="px-3 py-2 border-t border-slate-700/60 border-r border-slate-700/60 last:border-none">{children}</td>
                            ),
                            strong: ({ children }) => (
                              <strong className="font-bold text-blue-300">{children}</strong>
                            ),
                            ul: ({ children }) => (
                              <ul className="list-disc list-inside space-y-1 my-2">{children}</ul>
                            ),
                            ol: ({ children }) => (
                              <ol className="list-decimal list-inside space-y-1 my-2">{children}</ol>
                            ),
                            p: ({ children }) => (
                              <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>
                            ),
                          }}
                        >
                          {m.content}
                        </ReactMarkdown>
                      </div>
                    )}
                  </div>

                  {isUser && (
                    <div className="w-7 h-7 md:w-8 md:h-8 rounded-lg bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400 flex-shrink-0 mt-0.5">
                      <User className="w-3.5 h-3.5 md:w-4 md:h-4" />
                    </div>
                  )}
                </div>
              );
            })}

            {loading && (
              <div className="flex gap-3 justify-start items-center text-slate-400 text-xs pl-2">
                <div className="w-7 h-7 md:w-8 md:h-8 rounded-lg bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                </div>
                <span>Agent reasoning & executing database tools...</span>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Quick Action Chips */}
        <div className="px-4 md:px-6 py-2 bg-slate-950/40 border-t border-slate-800/60 flex gap-2 overflow-x-auto">
          {quickPrompts.map((prompt, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(prompt)}
              className="text-[11px] bg-slate-800/60 hover:bg-slate-800 border border-slate-700/60 hover:border-blue-500/30 text-slate-300 hover:text-white px-3 py-1.5 rounded-full transition-colors whitespace-nowrap flex items-center gap-1.5 cursor-pointer"
            >
              <Sparkles className="w-3 h-3 text-blue-400" />
              {prompt}
            </button>
          ))}
        </div>

        {/* Bottom Input Form */}
        <div className="p-3 md:p-6 bg-slate-950/80 border-t border-slate-800">
          <div className="max-w-4xl mx-auto">
            <form
              onSubmit={(e) => { e.preventDefault(); handleSend(); }}
              className="flex items-center gap-2 md:gap-3"
            >
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask anything about jobs, skills, or specific roles..."
                className="flex-1 bg-slate-900/90 border border-slate-700/80 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 text-white rounded-xl px-4 md:px-5 py-3 md:py-3.5 text-xs md:text-sm outline-none transition-all placeholder:text-slate-500 shadow-inner"
              />
              <button
                type="submit"
                disabled={!input.trim() || loading}
                className="bg-blue-600 hover:bg-blue-500 text-white p-3 md:p-3.5 rounded-xl disabled:opacity-50 shadow-lg shadow-blue-500/25 transition-all cursor-pointer flex-shrink-0"
              >
                <Send className="w-4 h-4" />
              </button>
            </form>
          </div>
        </div>

      </div>

    </div>
  );
}