import { useEffect, useMemo, useState } from 'react';
import AppShell from './components/layout/AppShell';
import OverviewPage from './pages/OverviewPage';
import CandidateProfilePage from './pages/CandidateProfilePage';
import CandidateChatPage from './pages/CandidateChatPage';
import JobMatchPage from './pages/JobMatchPage';
import ConversationsPage from './pages/ConversationsPage';
import SavedAnalysesPage from './pages/SavedAnalysesPage';
import SettingsPage from './pages/SettingsPage';
import { api } from './services/api';
import './styles/tokens.css';
import './styles/global.css';
import './styles/layout.css';
import './styles/components.css';
import './styles/chat.css';
import './styles/job-match.css';

const initialTheme = () => localStorage.getItem('candidate-ai-theme') || 'system';

export default function App() {
  const [page, setPage] = useState('overview');
  const [theme, setTheme] = useState(initialTheme);
  const [health, setHealth] = useState(null);
  const [profile, setProfile] = useState(null);
  const [config, setConfig] = useState(null);
  const [sessions, setSessions] = useState([]);

  useEffect(() => {
    const resolved = theme === 'system'
      ? (window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
      : theme;
    document.documentElement.dataset.theme = resolved;
    localStorage.setItem('candidate-ai-theme', theme);
  }, [theme]);

  useEffect(() => {
    api.health().then(setHealth).catch(() => setHealth(null));
    api.config().then(setConfig).catch(() => setConfig(null));
    api.profile().then(setProfile).catch(() => setProfile(null));
    api.sessions().then(setSessions).catch(() => setSessions([]));
  }, []);

  const shared = useMemo(() => ({ health, profile, config, sessions, setSessions, navigate: setPage }), [health, profile, config, sessions]);
  const pages = {
    overview: <OverviewPage {...shared} />,
    profile: <CandidateProfilePage profile={profile} />,
    chat: <CandidateChatPage {...shared} />,
    'job-match': <JobMatchPage config={config} />,
    conversations: <ConversationsPage {...shared} />,
    analyses: <SavedAnalysesPage />,
    settings: <SettingsPage health={health} config={config} />,
  };

  return <AppShell page={page} setPage={setPage} health={health} config={config} theme={theme} setTheme={setTheme}>{pages[page]}</AppShell>;
}
