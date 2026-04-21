import { useStore } from '../store/useStore';

const STAGES = ['created', 'queued', 'running', 'completed'];
const STAGE_COLOR = {
  created:   'var(--text-muted)',
  queued:    'var(--blue)',
  running:   'var(--amber)',
  completed: 'var(--emerald)',
  validated: 'var(--emerald)',
  failed:    'var(--rose)',
  assigned:  'var(--cyan)',
};

function PipelineStage({ label, count, color, isActive }) {
  return (
    <div style={{ textAlign: 'center', flex: 1 }}>
      <div style={{
        width: 44, height: 44, borderRadius: '50%', margin: '0 auto 8px',
        background: `${color}22`,
        border: `2px solid ${isActive ? color : `${color}44`}`,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        boxShadow: isActive ? `0 0 16px ${color}88` : 'none',
        transition: 'all 0.3s ease',
      }}>
        <span style={{ fontWeight: 800, fontSize: 16, color }}>{count}</span>
      </div>
      <div style={{ fontSize: 10.5, fontWeight: 600, color: isActive ? color : 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.6px' }}>
        {label}
      </div>
    </div>
  );
}

function Connector({ active }) {
  return (
    <div style={{ flex: 0, width: 40, display: 'flex', alignItems: 'center', marginBottom: 22 }}>
      <svg width="40" height="12" viewBox="0 0 40 12">
        <line x1="0" y1="6" x2="34" y2="6"
          stroke={active ? 'var(--blue)' : 'var(--border)'}
          strokeWidth="1.5"
          strokeDasharray={active ? '5 3' : 'none'}
          style={{ animation: active ? 'flow 1s linear infinite' : 'none' }}
        />
        <polygon points="34,2 40,6 34,10" fill={active ? 'var(--blue)' : 'var(--border)'} />
      </svg>
    </div>
  );
}

export default function TaskGraph() {
  const tasksObj = useStore((s) => s.tasks);
  const tasks = Object.values(tasksObj || {});

  const counts = {};
  tasks.forEach((t) => { counts[t.status] = (counts[t.status] || 0) + 1; });

  const pipeline = [
    { key: 'created',   label: 'Created',   color: 'var(--text-secondary)' },
    { key: 'queued',    label: 'Queued',     color: 'var(--blue)' },
    { key: 'running',   label: 'Running',    color: 'var(--amber)' },
    { key: 'completed', label: 'Completed',  color: 'var(--emerald)' },
    { key: 'validated', label: 'Validated',  color: 'var(--violet)' },
  ];

  const failed = counts['failed'] || 0;
  const retried = counts['assigned'] || 0;
  const runningCount = counts['running'] || 0;

  return (
    <div className="card h-full" style={{ display: 'flex', flexDirection: 'column' }}>
      <div className="card-header">
        <div className="card-title"><span>🔄</span> Task Flow Pipeline</div>
        <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{tasks.length} total tasks</div>
      </div>

      {/* Pipeline flow */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '8px 0 16px', overflowX: 'auto' }}>
        {pipeline.map((stage, i) => (
          <div key={stage.key} style={{ display: 'flex', alignItems: 'center', flex: 1, minWidth: 60 }}>
            <PipelineStage
              label={stage.label}
              count={counts[stage.key] || 0}
              color={stage.color}
              isActive={(counts[stage.key] || 0) > 0}
            />
            {i < pipeline.length - 1 && (
              <Connector active={(counts[stage.key] || 0) > 0} />
            )}
          </div>
        ))}
      </div>

      {/* Secondary stats */}
      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)',
        gap: 8, paddingTop: 12, borderTop: '1px solid var(--border)',
      }}>
        <div style={{ textAlign: 'center', padding: '8px', background: 'rgba(244,63,94,0.08)', borderRadius: 8, border: '1px solid rgba(244,63,94,0.2)' }}>
          <div style={{ fontSize: 20, fontWeight: 800, color: 'var(--rose)' }}>{failed}</div>
          <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Failed</div>
        </div>
        <div style={{ textAlign: 'center', padding: '8px', background: 'rgba(245,158,11,0.08)', borderRadius: 8, border: '1px solid rgba(245,158,11,0.2)' }}>
          <div style={{ fontSize: 20, fontWeight: 800, color: 'var(--amber)' }}>{runningCount}</div>
          <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Active</div>
        </div>
        <div style={{ textAlign: 'center', padding: '8px', background: 'rgba(6,182,212,0.08)', borderRadius: 8, border: '1px solid rgba(6,182,212,0.2)' }}>
          <div style={{ fontSize: 20, fontWeight: 800, color: 'var(--cyan)' }}>{retried}</div>
          <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Assigned</div>
        </div>
      </div>
    </div>
  );
}
