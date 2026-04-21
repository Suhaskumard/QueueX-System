import { useStore } from '../store/useStore';

export default function SystemSummary() {
  const summary = useStore((s) => s.systemSummary);
  const setShow  = useStore((s) => s.setShowSummaryModal);
  const tasksObj = useStore((s) => s.tasks);
  const tasks    = Object.values(tasksObj || {});

  if (!summary) return null;

  const healthColor = summary.system_health === 'stable'   ? 'var(--emerald)'
                    : summary.system_health === 'degraded' ? 'var(--amber)'
                    : 'var(--rose)';

  const statRows = [
    { label: 'Total Tasks',   value: summary.tasks_total,  color: 'var(--text-primary)' },
    { label: 'Completed',     value: summary.completed,    color: 'var(--emerald)' },
    { label: 'Failed',        value: summary.failed,       color: 'var(--rose)' },
    { label: 'Validated',     value: summary.validated,    color: 'var(--violet)' },
    { label: 'Retries',       value: summary.retries,      color: 'var(--amber)' },
    { label: 'Avg Latency',   value: summary.avg_latency,  color: 'var(--cyan)' },
    { label: 'Throughput',    value: summary.throughput,   color: 'var(--blue)' },
    { label: 'Uptime',        value: summary.uptime,       color: 'var(--text-secondary)' },
  ];

  const successRate = summary.tasks_total > 0
    ? Math.round((summary.completed / summary.tasks_total) * 100)
    : 0;

  return (
    <div className="modal-backdrop" onClick={() => setShow(false)}>
      <div className="modal-box" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <div style={{ fontSize: 40, marginBottom: 8 }}>🏆</div>
          <h2 style={{ fontSize: 22, fontWeight: 800, marginBottom: 4 }}>
            <span className="text-gradient-blue">Workload Complete</span>
          </h2>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, fontSize: 13 }}>
            <div className="dot" style={{ background: healthColor, boxShadow: `0 0 8px ${healthColor}` }} />
            <span style={{ color: healthColor, fontWeight: 700, textTransform: 'capitalize' }}>
              System {summary.system_health}
            </span>
          </div>
        </div>

        {/* Success Rate Donut */}
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <div style={{
            position: 'relative', width: 100, height: 100,
            margin: '0 auto',
          }}>
            <svg viewBox="0 0 100 100" style={{ transform: 'rotate(-90deg)' }}>
              <circle cx="50" cy="50" r="40" fill="none" stroke="var(--bg-elevated)" strokeWidth="10" />
              <circle
                cx="50" cy="50" r="40" fill="none"
                stroke={successRate >= 80 ? 'var(--emerald)' : successRate >= 50 ? 'var(--amber)' : 'var(--rose)'}
                strokeWidth="10"
                strokeDasharray={`${(successRate / 100) * 251.2} 251.2`}
                strokeLinecap="round"
                style={{ transition: 'stroke-dasharray 1s ease' }}
              />
            </svg>
            <div style={{
              position: 'absolute', inset: 0,
              display: 'flex', flexDirection: 'column',
              alignItems: 'center', justifyContent: 'center',
            }}>
              <div style={{ fontWeight: 800, fontSize: 20, color: 'var(--text-primary)' }}>{successRate}%</div>
              <div style={{ fontSize: 9, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Success</div>
            </div>
          </div>
        </div>

        {/* Stats Grid */}
        <div style={{
          display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)',
          gap: 10, marginBottom: 20,
        }}>
          {statRows.map(({ label, value, color }) => (
            <div key={label} style={{
              background: 'var(--bg-elevated)', borderRadius: 8,
              padding: '10px 12px', textAlign: 'center',
            }}>
              <div style={{ fontWeight: 800, fontSize: 18, color }}>{value ?? '—'}</div>
              <div style={{ fontSize: 9.5, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginTop: 2 }}>
                {label}
              </div>
            </div>
          ))}
        </div>

        {/* Close */}
        <div style={{ textAlign: 'center' }}>
          <button className="btn btn-primary" onClick={() => setShow(false)} style={{ minWidth: 140 }}>
            ✓ Close
          </button>
        </div>
      </div>
    </div>
  );
}
