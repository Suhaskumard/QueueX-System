import {
  Activity,
  BarChart3,
  ChevronLeft,
  ChevronRight,
  ClipboardList,
  FileText,
  RefreshCw,
  Server,
  Workflow,
} from 'lucide-react';
import { useStore } from '../store/useStore';

const NAV_ITEMS = [
  { id: 'dashboard', icon: BarChart3, label: 'Dashboard' },
  { id: 'tasks', icon: ClipboardList, label: 'Tasks' },
  { id: 'workers', icon: Server, label: 'Workers' },
  { id: 'logs', icon: FileText, label: 'Logs' },
  { id: 'retries', icon: RefreshCw, label: 'Retries' },
];

export default function Sidebar() {
  const collapsed = useStore((s) => s.sidebarCollapsed);
  const toggleSidebar = useStore((s) => s.toggleSidebar);
  const activeView = useStore((s) => s.activeView);
  const setActiveView = useStore((s) => s.setActiveView);
  const systemHealth = useStore((s) => s.metrics?.system_health ?? 'stable');
  const connStatus = useStore((s) => s.connectionStatus);
  const tasksObj = useStore((s) => s.tasks);

  const tasks = Object.values(tasksObj || {});
  const healthColor = systemHealth === 'stable' ? 'var(--emerald)' : systemHealth === 'degraded' ? 'var(--amber)' : 'var(--rose)';
  const connColor = connStatus === 'connected' ? 'var(--emerald)' : connStatus === 'connecting' ? 'var(--amber)' : 'var(--rose)';

  const running = tasks.filter((t) => t.status === 'running').length;
  const completed = tasks.filter((t) => ['completed', 'validated', 'stored'].includes(t.status)).length;
  const failed = tasks.filter((t) => t.status === 'failed').length;

  return (
    <aside style={{
      width: collapsed ? 64 : 230,
      minWidth: collapsed ? 64 : 230,
      background: 'rgba(11,19,34,0.92)',
      borderRight: '1px solid var(--border)',
      display: 'flex',
      flexDirection: 'column',
      transition: 'width 0.28s cubic-bezier(.4,0,.2,1), min-width 0.28s cubic-bezier(.4,0,.2,1)',
      overflow: 'hidden',
      zIndex: 10,
      backdropFilter: 'blur(16px)',
    }}>
      <div style={{
        padding: '20px 16px 16px',
        borderBottom: '1px solid var(--border)',
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        flexShrink: 0,
      }}>
        <div style={{
          width: 34,
          height: 34,
          borderRadius: 8,
          flexShrink: 0,
          background: 'linear-gradient(135deg, var(--blue), var(--cyan))',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#fff',
          boxShadow: '0 0 20px rgba(6,182,212,0.34)',
        }}>
          <Workflow size={19} />
        </div>
        {!collapsed && (
          <div>
            <div style={{ fontWeight: 800, fontSize: 15, letterSpacing: 0 }}>QueueMind</div>
            <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 1 }}>Distributed Task Engine</div>
          </div>
        )}
      </div>

      {!collapsed && (
        <div style={{
          margin: '12px 14px 0',
          background: `${connColor}0f`,
          border: `1px solid ${connColor}33`,
          borderRadius: 8,
          padding: '8px 12px',
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          fontSize: 11,
          flexShrink: 0,
        }}>
          <div className="dot" style={{
            background: connColor,
            boxShadow: `0 0 6px ${connColor}`,
            animation: connStatus === 'connecting' ? 'pulse-badge 1s ease-in-out infinite' : 'none',
          }} />
          <span style={{ color: connColor, fontWeight: 700, textTransform: 'capitalize' }}>{connStatus}</span>
        </div>
      )}

      <nav style={{ flex: 1, padding: '14px 8px', display: 'flex', flexDirection: 'column', gap: 4 }}>
        {NAV_ITEMS.map((item) => {
          const active = activeView === item.id;
          const Icon = item.icon;
          return (
            <button
              key={item.id}
              title={collapsed ? item.label : undefined}
              onClick={() => setActiveView(item.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                padding: collapsed ? '11px 0' : '11px 12px',
                justifyContent: collapsed ? 'center' : 'flex-start',
                borderRadius: 8,
                border: 'none',
                cursor: 'pointer',
                fontFamily: 'inherit',
                fontSize: 13,
                fontWeight: active ? 800 : 600,
                color: active ? 'var(--text-primary)' : 'var(--text-muted)',
                background: active
                  ? 'linear-gradient(135deg, rgba(59,130,246,0.20), rgba(6,182,212,0.10))'
                  : 'transparent',
                boxShadow: active ? 'inset 0 0 0 1px rgba(6,182,212,0.24)' : 'none',
                transition: 'all 0.15s ease',
                width: '100%',
              }}
              onMouseEnter={(e) => {
                if (!active) e.currentTarget.style.background = 'var(--bg-hover)';
                e.currentTarget.style.color = 'var(--text-primary)';
              }}
              onMouseLeave={(e) => {
                if (!active) {
                  e.currentTarget.style.background = 'transparent';
                  e.currentTarget.style.color = 'var(--text-muted)';
                }
              }}
            >
              <Icon size={17} strokeWidth={2.2} />
              {!collapsed && <span>{item.label}</span>}
            </button>
          );
        })}
      </nav>

      {!collapsed && (
        <div style={{
          padding: '12px 14px',
          borderTop: '1px solid var(--border)',
          flexShrink: 0,
        }}>
          <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.7px', marginBottom: 8 }}>
            System Health
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 10 }}>
            <div className="dot" style={{ background: healthColor, boxShadow: `0 0 6px ${healthColor}` }} />
            <span style={{ color: healthColor, fontSize: 12, fontWeight: 800, textTransform: 'capitalize' }}>{systemHealth}</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {[
              { label: 'Running', value: running, color: 'var(--amber)' },
              { label: 'Done', value: completed, color: 'var(--emerald)' },
              { label: 'Failed', value: failed, color: 'var(--rose)' },
            ].map(({ label, value, color }) => (
              <div key={label} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11 }}>
                <span style={{ color: 'var(--text-muted)' }}>{label}</span>
                <span style={{ color, fontWeight: 800 }}>{value}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <button
        onClick={toggleSidebar}
        title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        style={{
          padding: '12px',
          borderTop: '1px solid var(--border)',
          background: 'none',
          borderLeft: 'none',
          borderRight: 'none',
          borderBottom: 'none',
          cursor: 'pointer',
          color: 'var(--text-muted)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: collapsed ? 'center' : 'flex-start',
          gap: 8,
          transition: 'color 0.15s',
          flexShrink: 0,
          fontFamily: 'inherit',
        }}
        onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--text-primary)')}
        onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-muted)')}
      >
        {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        {!collapsed && <span style={{ fontSize: 12 }}>Collapse</span>}
      </button>
    </aside>
  );
}
