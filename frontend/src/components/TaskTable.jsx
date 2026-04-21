import { Fragment, useState } from 'react';
import { ChevronDown, ChevronRight, ClipboardList, Search, Sparkles } from 'lucide-react';
import { useStore } from '../store/useStore';

const STATUS_ORDER = ['created', 'partitioned', 'queued', 'assigned', 'running', 'completed', 'validated', 'failed', 'stored'];

function StatusBadge({ status }) {
  return <span className={`badge badge-${status}`}>{status}</span>;
}

function TypeChip({ type }) {
  const colors = { cpu: 'var(--blue)', io: 'var(--emerald)', io_cpu: 'var(--violet)' };
  const labels = { cpu: 'CPU', io: 'I/O', io_cpu: 'CPU+IO' };
  const c = colors[type] || 'var(--blue)';
  return (
    <span style={{
      background: `${c}22`,
      color: c,
      border: `1px solid ${c}44`,
      borderRadius: 4,
      padding: '1px 7px',
      fontSize: 10,
      fontWeight: 700,
    }}>
      {labels[type] || type}
    </span>
  );
}

export default function TaskTable() {
  const tasksObj = useStore((s) => s.tasks);
  const setActiveView = useStore((s) => s.setActiveView);
  const tasks = Object.values(tasksObj || {});
  const [filter, setFilter] = useState('all');
  const [sortKey, setSortKey] = useState('created_at');
  const [expanded, setExpanded] = useState(null);

  const filtered = (filter === 'all' ? tasks : tasks.filter((t) => t.status === filter))
    .sort((a, b) => {
      if (sortKey === 'priority') return (b.priority ?? 0) - (a.priority ?? 0);
      if (sortKey === 'execution_time') return (b.execution_time ?? 0) - (a.execution_time ?? 0);
      return new Date(b.created_at) - new Date(a.created_at);
    });

  return (
    <div className="card h-full flex-col" style={{ display: 'flex' }}>
      <div className="card-header" style={{ flexShrink: 0, gap: 12 }}>
        <div>
          <div className="card-title">
            <ClipboardList size={16} />
            Task Queue ({tasks.length})
          </div>
          <div style={{ color: 'var(--text-muted)', fontSize: 11, marginTop: 4 }}>
            Click any row to inspect details. Completed tasks show the result payload in the expanded panel.
          </div>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            style={{
              background: 'var(--bg-elevated)',
              color: 'var(--text-secondary)',
              border: '1px solid var(--border)',
              borderRadius: 6,
              padding: '5px 8px',
              fontSize: 11,
              cursor: 'pointer',
              fontFamily: 'inherit',
            }}
          >
            <option value="all">All Status</option>
            {STATUS_ORDER.map((s) => (
              <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
            ))}
          </select>
          <select
            value={sortKey}
            onChange={(e) => setSortKey(e.target.value)}
            style={{
              background: 'var(--bg-elevated)',
              color: 'var(--text-secondary)',
              border: '1px solid var(--border)',
              borderRadius: 6,
              padding: '5px 8px',
              fontSize: 11,
              cursor: 'pointer',
              fontFamily: 'inherit',
            }}
          >
            <option value="created_at">Sort: Newest</option>
            <option value="priority">Sort: Priority</option>
            <option value="execution_time">Sort: Time</option>
          </select>
        </div>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', minHeight: 0 }}>
        {filtered.length === 0 ? (
          <div style={{
            minHeight: 320,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            textAlign: 'center',
            gap: 12,
            color: 'var(--text-muted)',
            fontSize: 13,
          }}>
            <div style={{
              width: 54,
              height: 54,
              display: 'grid',
              placeItems: 'center',
              borderRadius: 8,
              color: 'var(--cyan)',
              background: 'rgba(6,182,212,0.10)',
              border: '1px solid rgba(6,182,212,0.24)',
            }}>
              <Search size={24} />
            </div>
            <div>
              <div style={{ color: 'var(--text-primary)', fontWeight: 800, marginBottom: 3 }}>No tasks to inspect yet</div>
              <div>Go to the dashboard, submit a workload or run the demo, then return here for results.</div>
            </div>
            <button className="btn btn-primary" onClick={() => setActiveView('dashboard')}>
              <Sparkles size={15} />
              Start on Dashboard
            </button>
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th></th>
                <th>ID</th>
                <th>Description</th>
                <th>Type</th>
                <th>Priority</th>
                <th>Status</th>
                <th>Worker</th>
                <th>Time</th>
                <th>Score</th>
                <th>Retries</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((task) => {
                const isExpanded = expanded === task.task_id;
                const hasResult = Boolean(task.result);

                return (
                  <Fragment key={task.task_id}>
                    <tr
                      style={{ cursor: 'pointer' }}
                      onClick={() => setExpanded(isExpanded ? null : task.task_id)}
                    >
                      <td style={{ width: 24, color: 'var(--text-muted)' }}>
                        {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                      </td>
                      <td>
                        <span className="font-mono" style={{ fontSize: 10.5, color: 'var(--text-muted)' }}>
                          {task.task_id?.slice(-16)}
                        </span>
                      </td>
                      <td style={{ maxWidth: 260 }}>
                        <span className="truncate" style={{ display: 'block', maxWidth: 260 }}>{task.description}</span>
                      </td>
                      <td><TypeChip type={task.task_type} /></td>
                      <td>
                        <span style={{ fontWeight: 800, color: task.priority >= 8 ? 'var(--rose)' : task.priority >= 5 ? 'var(--amber)' : 'var(--text-secondary)' }}>
                          P{task.priority}
                        </span>
                      </td>
                      <td><StatusBadge status={task.status} /></td>
                      <td>
                        <span style={{ color: 'var(--cyan)', fontSize: 11 }}>{task.assigned_worker ?? '-'}</span>
                      </td>
                      <td>
                        <span className="font-mono" style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
                          {task.execution_time != null ? `${task.execution_time}s` : '-'}
                        </span>
                      </td>
                      <td>
                        {task.quality_score != null ? (
                          <span style={{
                            fontWeight: 800,
                            fontSize: 12,
                            color: task.quality_score >= 8 ? 'var(--emerald)' : task.quality_score >= 5 ? 'var(--amber)' : 'var(--rose)',
                          }}>
                            {task.quality_score.toFixed(1)}
                          </span>
                        ) : '-'}
                      </td>
                      <td>
                        {(task.retry_count ?? 0) > 0 ? (
                          <span style={{ color: 'var(--amber)', fontWeight: 800 }}>x{task.retry_count}</span>
                        ) : '-'}
                      </td>
                    </tr>

                    {isExpanded && (
                      <tr>
                        <td colSpan={10} style={{ padding: '14px 16px', background: 'var(--bg-elevated)' }}>
                          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(220px,1fr))', gap: 12, fontSize: 12 }}>
                            <div>
                              <span style={{ color: 'var(--text-muted)' }}>Full ID: </span>
                              <span className="font-mono" style={{ fontSize: 10.5 }}>{task.task_id}</span>
                            </div>
                            <div>
                              <span style={{ color: 'var(--text-muted)' }}>Dependencies: </span>
                              <span>{task.dependencies?.length ? task.dependencies.join(', ') : 'none'}</span>
                            </div>
                            <div>
                              <span style={{ color: 'var(--text-muted)' }}>Result status: </span>
                              <span style={{ color: hasResult ? 'var(--emerald)' : 'var(--amber)', fontWeight: 800 }}>
                                {hasResult ? 'ready' : 'waiting for completion'}
                              </span>
                            </div>
                            {task.error_message && (
                              <div style={{ gridColumn: '1/-1' }}>
                                <span style={{ color: 'var(--rose)' }}>Error: </span>
                                <span className="font-mono" style={{ color: 'var(--text-secondary)', fontSize: 11 }}>{task.error_message}</span>
                              </div>
                            )}
                            <div style={{ gridColumn: '1/-1' }}>
                              <div style={{ color: 'var(--text-muted)', marginBottom: 5 }}>Result:</div>
                              <pre style={{
                                margin: 0,
                                padding: 12,
                                borderRadius: 8,
                                background: 'rgba(6,11,20,0.38)',
                                border: '1px solid var(--border)',
                                color: hasResult ? 'var(--emerald)' : 'var(--text-muted)',
                                whiteSpace: 'pre-wrap',
                                overflowWrap: 'anywhere',
                                fontSize: 11,
                              }}>
                                {hasResult ? JSON.stringify(task.result, null, 2) : 'The result will appear here when this task completes.'}
                              </pre>
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </Fragment>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
