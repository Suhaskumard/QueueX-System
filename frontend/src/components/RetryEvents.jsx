import { useStore } from '../store/useStore';

function RetryEntry({ evt }) {
  const isTransient = evt.failure_type === 'transient';
  const color = isTransient ? 'var(--amber)' : 'var(--rose)';

  return (
    <div className="animate-in" style={{
      background: `${color}0d`, border: `1px solid ${color}33`,
      borderRadius: 8, padding: '10px 14px', fontSize: 12,
      display: 'flex', gap: 12, alignItems: 'flex-start',
    }}>
      <div style={{
        flexShrink: 0, width: 28, height: 28, borderRadius: '50%',
        background: `${color}22`, border: `1px solid ${color}55`,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 14,
      }}>
        {isTransient ? '🔄' : '💀'}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div className="flex items-center justify-between" style={{ marginBottom: 4 }}>
          <span className="font-mono" style={{ color, fontSize: 10.5 }}>
            {evt.task_id ?? '—'}
          </span>
          <span style={{
            fontSize: 10, fontWeight: 700, padding: '1px 8px',
            background: `${color}22`, color, borderRadius: 10,
            border: `1px solid ${color}44`,
          }}>
            {isTransient ? 'TRANSIENT' : 'PERMANENT'}
          </span>
        </div>

        <div style={{ color: 'var(--text-secondary)', marginBottom: 4 }}>
          {evt.reason || evt.error || 'Unknown failure'}
        </div>

        <div className="flex" style={{ gap: 16, fontSize: 11, color: 'var(--text-muted)' }}>
          {evt.retry_count != null && (
            <span>Attempt <strong style={{ color }}>{evt.retry_count}</strong> / {evt.max_retries ?? 3}</span>
          )}
          {evt.next_retry_delay && (
            <span>Next retry in <strong style={{ color: 'var(--cyan)' }}>{evt.next_retry_delay}</strong></span>
          )}
          {evt.action && (
            <span>Action: <strong style={{ color }}>{evt.action}</strong></span>
          )}
        </div>
      </div>
    </div>
  );
}

export default function RetryEvents() {
  const events = useStore((s) => s.retryEvents);

  const transientCount = events.filter((e) => e.failure_type === 'transient').length;
  const permanentCount = events.filter((e) => e.failure_type === 'permanent').length;

  return (
    <div className="card h-full flex-col" style={{ display: 'flex' }}>
      <div className="card-header" style={{ flexShrink: 0 }}>
        <div className="card-title"><span>🔄</span> Retry Timeline</div>
        <div className="flex items-center gap-2" style={{ fontSize: 11 }}>
          <span style={{ color: 'var(--amber)' }}>🔄 {transientCount} retrying</span>
          <span style={{ color: 'var(--rose)' }}>💀 {permanentCount} permanent</span>
        </div>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', minHeight: 0, display: 'flex', flexDirection: 'column', gap: 6 }}>
        {events.length === 0 ? (
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: 13 }}>
            No failures yet — looking good! ✅
          </div>
        ) : (
          events.map((evt) => <RetryEntry key={evt.id} evt={evt} />)
        )}
      </div>
    </div>
  );
}
