import { useRef, useEffect, useState } from 'react';
import { useStore } from '../store/useStore';

const LEVEL_COLOR = {
  info:    'var(--blue)',
  success: 'var(--emerald)',
  warn:    'var(--amber)',
  error:   'var(--rose)',
};
const LEVEL_BG = {
  info:    'rgba(59,130,246,0.08)',
  success: 'rgba(16,185,129,0.08)',
  warn:    'rgba(245,158,11,0.08)',
  error:   'rgba(244,63,94,0.08)',
};

function LogEntry({ log }) {
  const color = LEVEL_COLOR[log.level] || LEVEL_COLOR.info;
  const bg    = LEVEL_BG[log.level]   || LEVEL_BG.info;

  return (
    <div className="animate-in" style={{
      display: 'flex', gap: 10, padding: '5px 8px', borderRadius: 6,
      background: bg, borderLeft: `2px solid ${color}88`, fontSize: 12,
      marginBottom: 2, alignItems: 'flex-start',
    }}>
      <span className="font-mono" style={{ color: 'var(--text-muted)', flexShrink: 0, fontSize: 10.5, marginTop: 1 }}>
        {log.time ?? '--'}
      </span>
      <span style={{ color, fontWeight: 600, flexShrink: 0, fontSize: 10.5, marginTop: 1 }}>
        [{(log.level ?? 'info').toUpperCase()}]
      </span>
      <span style={{ color: 'var(--text-primary)', flex: 1 }}>
        <span style={{ color, fontWeight: 600 }}>{log.event}</span>
        {log.task_id && (
          <span className="font-mono" style={{ color: 'var(--text-muted)', marginLeft: 6, fontSize: 10.5 }}>
            {log.task_id}
          </span>
        )}
        {log.worker && (
          <span style={{ color: 'var(--cyan)', marginLeft: 6 }}>@{log.worker}</span>
        )}
        {log.details && (
          <span style={{ color: 'var(--text-muted)', marginLeft: 6, fontSize: 10.5 }}>
            {Object.entries(log.details).map(([k, v]) => `${k}=${JSON.stringify(v)}`).join(' ')}
          </span>
        )}
      </span>
    </div>
  );
}

export default function LogStream() {
  const logs = useStore((s) => s.logs);
  const clearLogs = useStore((s) => s.clearLogs);
  const bottomRef = useRef(null);
  const containerRef = useRef(null);
  const [paused, setPaused] = useState(false);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    if (!paused && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, paused]);

  const filtered = filter === 'all' ? logs : logs.filter((l) => l.level === filter);

  return (
    <div className="card h-full flex-col" style={{ display: 'flex' }}>
      <div className="card-header" style={{ flexShrink: 0 }}>
        <div className="card-title"><span>📋</span> Live Log Stream</div>
        <div className="flex items-center gap-2">
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            style={{
              background: 'var(--bg-elevated)', color: 'var(--text-secondary)',
              border: '1px solid var(--border)', borderRadius: 6,
              padding: '4px 8px', fontSize: 11, cursor: 'pointer', fontFamily: 'inherit',
            }}
          >
            <option value="all">All</option>
            <option value="info">Info</option>
            <option value="success">Success</option>
            <option value="warn">Warn</option>
            <option value="error">Error</option>
          </select>
          <button
            className={`btn ${paused ? 'btn-primary' : 'btn-ghost'}`}
            style={{ padding: '4px 10px', fontSize: 11 }}
            onClick={() => setPaused((p) => !p)}
          >
            {paused ? '▶ Resume' : '⏸ Pause'}
          </button>
          <button className="btn btn-ghost" style={{ padding: '4px 10px', fontSize: 11 }} onClick={clearLogs}>
            Clear
          </button>
        </div>
      </div>

      <div
        ref={containerRef}
        style={{ flex: 1, overflowY: 'auto', minHeight: 0, padding: '4px 0' }}
      >
        {filtered.length === 0 ? (
          <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '32px 0', fontSize: 13 }}>
            Waiting for events…
          </div>
        ) : (
          <>
            {filtered.map((log) => <LogEntry key={log.id} log={log} />)}
            <div ref={bottomRef} />
          </>
        )}
      </div>

      <div style={{ flexShrink: 0, paddingTop: 8, borderTop: '1px solid var(--border)', fontSize: 11, color: 'var(--text-muted)' }}>
        {filtered.length} entries {paused && '(paused)'}
      </div>
    </div>
  );
}
