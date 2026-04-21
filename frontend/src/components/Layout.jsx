import Sidebar from './Sidebar';
import { useStore } from '../store/useStore';

const VIEW_TITLES = {
  dashboard: 'Dashboard',
  tasks: 'Task Queue',
  workers: 'Worker Cluster',
  logs: 'Live Logs',
  retries: 'Retry Events',
};

export default function Layout({ children }) {
  const activeView = useStore((s) => s.activeView);
  const connStatus = useStore((s) => s.connectionStatus);

  const connColor = connStatus === 'connected' ? 'var(--emerald)'
    : connStatus === 'connecting' ? 'var(--amber)'
    : 'var(--rose)';

  return (
    <div style={{
      display: 'flex',
      height: '100vh',
      overflow: 'hidden',
      background: 'transparent',
    }}>
      <Sidebar />

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', minWidth: 0 }}>
        <header style={{
          height: 56,
          background: 'rgba(11,19,34,0.88)',
          borderBottom: '1px solid var(--border)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 20px',
          flexShrink: 0,
          backdropFilter: 'blur(16px)',
        }}>
          <div>
            <h1 style={{ fontWeight: 800, fontSize: 16, letterSpacing: 0 }}>
              {VIEW_TITLES[activeView] ?? 'QueueMind'}
            </h1>
            <div style={{ color: 'var(--text-muted)', fontSize: 11, marginTop: 1 }}>
              Submit work, monitor progress, inspect completed results.
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12 }}>
              <div className="dot" style={{
                background: connColor,
                boxShadow: `0 0 6px ${connColor}`,
                animation: connStatus === 'connecting' ? 'pulse-badge 1s ease-in-out infinite' : 'none',
              }} />
              <span style={{ color: connColor, fontWeight: 700 }}>
                {connStatus === 'connected' ? 'Live' : connStatus === 'connecting' ? 'Connecting...' : 'Disconnected'}
              </span>
            </div>

            <div style={{
              background: 'rgba(6,182,212,0.12)',
              border: '1px solid rgba(6,182,212,0.30)',
              borderRadius: 999,
              padding: '4px 10px',
              fontSize: 11,
              fontWeight: 800,
              color: 'var(--cyan)',
              letterSpacing: '0.5px',
            }}>
              DEV MODE
            </div>
          </div>
        </header>

        <main style={{
          flex: 1,
          overflow: 'auto',
          padding: '16px 20px 24px',
          minHeight: 0,
        }}>
          {children}
        </main>
      </div>
    </div>
  );
}
