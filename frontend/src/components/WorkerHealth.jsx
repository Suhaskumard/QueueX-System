import { useStore } from '../store/useStore';

const typeColor = { cpu: 'var(--blue)', io: 'var(--emerald)', io_cpu: 'var(--violet)' };
const typeLabel = { cpu: 'CPU', io: 'I/O', io_cpu: 'CPU+IO' };

function WorkerCard({ worker }) {
  const load = Math.min(100, Math.round(worker.load_pct ?? 0));
  const busy = worker.status === 'busy';
  const color = typeColor[worker.worker_type] || 'var(--blue)';

  return (
    <div className="card" style={{ padding: '16px', position: 'relative', overflow: 'hidden', transition: 'box-shadow .25s' }}>
      {busy && (
        <div style={{
          position: 'absolute', inset: 0, borderRadius: 'var(--radius-lg)',
          boxShadow: `inset 0 0 0 1px ${color}55`,
          pointerEvents: 'none',
        }} />
      )}

      <div className="flex items-center justify-between" style={{ marginBottom: 10 }}>
        <div className="flex items-center gap-2">
          <div className="dot" style={{
            background: busy ? color : 'var(--text-muted)',
            boxShadow: busy ? `0 0 8px ${color}` : 'none',
            animation: busy ? 'pulse-badge 1.5s ease-in-out infinite' : 'none',
          }} />
          <span style={{ fontWeight: 700, fontSize: 13 }}>{worker.worker_id}</span>
        </div>
        <span className="badge" style={{
          background: `${color}22`, color, border: `1px solid ${color}44`,
          fontSize: 10, padding: '2px 8px',
        }}>
          {typeLabel[worker.worker_type] || worker.worker_type}
        </span>
      </div>

      {/* Load Bar */}
      <div style={{ marginBottom: 8 }}>
        <div className="flex items-center justify-between" style={{ marginBottom: 4 }}>
          <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>Load</span>
          <span style={{ fontSize: 12, fontWeight: 700, color }}>{load}%</span>
        </div>
        <div className="progress-bar">
          <div
            className="progress-fill"
            style={{
              width: `${load}%`,
              background: `linear-gradient(90deg, ${color}bb, ${color})`,
              boxShadow: load > 60 ? `0 0 8px ${color}88` : 'none',
            }}
          />
        </div>
      </div>

      {/* Stats */}
      <div className="flex" style={{ gap: 12, marginTop: 10, fontSize: 11 }}>
        <div>
          <div style={{ color: 'var(--text-muted)' }}>Done</div>
          <div style={{ fontWeight: 700, color: 'var(--emerald)', fontSize: 14 }}>
            {worker.tasks_completed ?? 0}
          </div>
        </div>
        <div>
          <div style={{ color: 'var(--text-muted)' }}>Failed</div>
          <div style={{ fontWeight: 700, color: 'var(--rose)', fontSize: 14 }}>
            {worker.tasks_failed ?? 0}
          </div>
        </div>
        {worker.current_task && (
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ color: 'var(--text-muted)' }}>Current Task</div>
            <div className="truncate" style={{ fontWeight: 500, color: 'var(--amber)', fontFamily: 'monospace', fontSize: 10.5 }}>
              {worker.current_task}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function WorkerHealth() {
  const workersObj = useStore((s) => s.workers);
  const workers = Object.values(workersObj || {});

  const busyCount = workers.filter((w) => w.status === 'busy').length;

  return (
    <div className="card h-full" style={{ display: 'flex', flexDirection: 'column' }}>
      <div className="card-header">
        <div className="card-title">
          <span>⚡</span> Worker Cluster
        </div>
        <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
          <span style={{ color: 'var(--emerald)', fontWeight: 700 }}>{busyCount}</span>/{workers.length} active
        </div>
      </div>

      {workers.length === 0 ? (
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: 13 }}>
          No workers registered
        </div>
      ) : (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))',
          gap: 12,
          overflowY: 'auto',
        }}>
          {workers.map((w) => <WorkerCard key={w.worker_id} worker={w} />)}
        </div>
      )}
    </div>
  );
}
