// frontend/src/App.jsx
import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import MatchesPage from './pages/Matchespage';
import ChatPage from './pages/chatpage';
import ShortlistPage from './pages/Shortlistpage';
import LoginPage from './pages/loginPage';
import { api } from './api';

export default function App() {
  const [user, setUser] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem('nexus_token');
    if (token) {
      api.getProfile()
        .then(setUser)
        .catch(() => {
          localStorage.removeItem('nexus_token');
          setUser(null);
        });
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('nexus_token');
    localStorage.removeItem('nexus_chat_history');
    localStorage.removeItem('nexus_latest_briefing')
    localStorage.removeItem('resume_name');
    localStorage.removeItem('nexus_resume_name')
    setUser(null);
  };

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-[#0b0f19] text-slate-100 flex flex-col font-sans selection:bg-blue-600 selection:text-white">
        <Navbar user={user} onLogout={handleLogout} />

        <main className="flex-1 w-full mx-auto p-4 md:p-6 flex flex-col">
          <Routes>
            <Route path="/" element={<MatchesPage user={user} />} />
            <Route path="/chat" element={<ChatPage user={user} />} />
            <Route path="/shortlist" element={<ShortlistPage user={user} />} />
            <Route path="/login" element={<LoginPage onLoginSuccess={setUser} />} />
            <Route path="*" element={<Navigate to="/" />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}