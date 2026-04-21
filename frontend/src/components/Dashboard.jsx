import { useState } from 'react';
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  BarChart3,
  CheckCircle2,
  ClipboardList,
  Clock3,
  Layers3,
  Play,
  Radio,
  Send,
  Server,
  Sparkles,
  Target,
  XCircle,
} from 'lucide-react';
import { useStore } from '../store/useStore';

const API = 'http://localhost:8000';

const pipelineSteps = [
  'Extract IPs',
  'Deduplicate',
  'Classify',
  'Check blacklists',
  'Geolocate',
  'Detect patterns',
  'Generate report',
];

function StatTile({ label, value, color, icon: Icon }) {
  return (
    <div className="metric-tile">
      <div className="metric-icon" style={{ color, background: `${color}17`, borderColor: `${color}33` }}>
        <Icon size={18} strokeWidth={2.3} />
      </div>
      <div>
        <div className="metric-number" style={{ color }}>{value}</div>
        <div className="metric-caption">{label}</div>
      </div>
    </div>
  );
}

function StepPill({ number, title, detail, active }) {
  return (
    <div className={`guide-step ${active ? 'guide-step-active' : ''}`}>
      <div className="guide-step-number">{number}</div>
      <div>
        <div className="guide-step-title">{title}</div>
        <div className="guide-step-detail">{detail}</div>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const metrics = useStore((s) => s.metrics);
  const tasksObj = useStore((s) => s.tasks);
  const setActiveView = useStore((s) => s.setActiveView);
  const tasks = Object.values(tasksObj || {});

  const [chunks, setChunks] = useState(3);
  const [priority, setPriority] = useState(5);
  const [loading, setLoading] = useState(false);
  const [demoLoading, setDemoLoading] = useState(false);
  const [toast, setToast] = useState(null);

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3500);
  };

  const submitWorkload = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/workloads`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: 'Log Processing Pipeline',
          description: 'Process system logs: extract IPs, deduplicate, classify, check blacklists, geolocate, detect patterns, generate reports',
          total_chunks: chunks,
          priority,
        }),
      });
      if (!res.ok) throw new Error(await res.text());
      showToast(`Workload accepted: ${chunks} chunks at priority P${priority}. Watch Task Queue for results.`);
    } catch (e) {
      showToast(e.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const runDemo = async () => {
    setDemoLoading(true);
    try {
      const res = await fetch(`${API}/api/demo`, { method: 'POST' });
      if (!res.ok) throw new Error(await res.text());
      showToast('Demo workload launched. The dashboard will update as tasks move through the pipeline.');
    } catch (e) {
      showToast(e.message, 'error');
    } finally {
      setDemoLoading(false);
    }
  };

  const completed = tasks.filter((t) => ['completed', 'validated', 'stored'].includes(t.status)).length;
  const failed = tasks.filter((t) => t.status === 'failed').length;
  const running = tasks.filter((t) => t.status === 'running').length;
  const queued = tasks.filter((t) => t.status === 'queued').length;
  const readyResults = tasks.filter((t) => t.result || ['completed', 'validated', 'stored'].includes(t.status)).length;
  const progressPct = tasks.length ? Math.round(((completed + failed) / tasks.length) * 100) : 0;

  const healthColor = metrics.system_health === 'stable' ? 'var(--emerald)'
    : metrics.system_health === 'degraded' ? 'var(--amber)'
    : 'var(--rose)';

  return (
    <div className="dashboard-shell">
      {toast && (
        <div className={`toast ${toast.type === 'error' ? 'toast-error' : 'toast-success'}`}>
          {toast.type === 'error' ? <AlertTriangle size={16} /> : <CheckCircle2 size={16} />}
          <span>{toast.msg}</span>
        </div>
      )}

      <section className="dashboard-hero">
        <div className="hero-copy">
          <div className="hero-kicker">
            <Sparkles size={14} />
            Guided workload runner
          </div>
          <h2>Start a workload, track every stage, open the final results.</h2>
          <p>
            Pick a chunk count and priority, submit the pipeline, then follow the queue until completed tasks expose their result payload.
          </p>
        </div>
        <div className="hero-progress" aria-label="Workload progress summary">
          <div className="progress-ring" style={{ '--progress': `${progressPct}%` }}>
            <div>
              <strong>{progressPct}%</strong>
              <span>complete</span>
            </div>
          </div>
          <div>
            <div className="hero-progress-label">Results ready</div>
            <div className="hero-progress-value">{readyResults}</div>
            <button className="link-button" type="button" onClick={() => setActiveView('tasks')}>
              Open Task Queue <ArrowRight size={14} />
            </button>
          </div>
        </div>
      </section>

      <div className="kpi-grid">
        <StatTile label="Total Tasks" value={tasks.length} color="var(--text-primary)" icon={ClipboardList} />
        <StatTile label="Running" value={running} color="var(--amber)" icon={Activity} />
        <StatTile label="Completed" value={completed} color="var(--emerald)" icon={CheckCircle2} />
        <StatTile label="Failed" value={failed} color="var(--rose)" icon={XCircle} />
        <StatTile label="Queued" value={queued} color="var(--blue)" icon={Clock3} />
      </div>

      <div className="dashboard-main-grid">
        <div className="card workload-card">
          <div className="card-title">
            <Send size={16} />
            Submit Workload
          </div>

          <div className="control-block">
            <div className="control-label">
              <span>Log chunks</span>
              <strong style={{ color: 'var(--blue)' }}>{chunks}</strong>
            </div>
            <input
              type="range"
              min={1}
              max={10}
              value={chunks}
              onChange={(e) => setChunks(Number(e.target.value))}
              style={{ width: '100%', accentColor: 'var(--blue)' }}
            />
          </div>

          <div className="control-block">
            <div className="control-label">
              <span>Priority</span>
              <strong style={{ color: priority >= 8 ? 'var(--rose)' : priority >= 5 ? 'var(--amber)' : 'var(--emerald)' }}>
                P{priority}
              </strong>
            </div>
            <input
              type="range"
              min={1}
              max={10}
              value={priority}
              onChange={(e) => setPriority(Number(e.target.value))}
              style={{ width: '100%', accentColor: priority >= 8 ? 'var(--rose)' : priority >= 5 ? 'var(--amber)' : 'var(--emerald)' }}
            />
          </div>

          <div className="pipeline-strip">
            {pipelineSteps.map((step, index) => (
              <span key={step}>
                {step}
                {index < pipelineSteps.length - 1 && <ArrowRight size={11} />}
              </span>
            ))}
          </div>

          <div className="button-row">
            <button className="btn btn-primary" onClick={submitWorkload} disabled={loading || demoLoading}>
              {loading ? <Activity size={15} className="spin-icon" /> : <Play size={15} />}
              {loading ? 'Submitting' : 'Submit'}
            </button>
            <button className="btn btn-emerald" onClick={runDemo} disabled={loading || demoLoading}>
              {demoLoading ? <Activity size={15} className="spin-icon" /> : <Target size={15} />}
              {demoLoading ? 'Starting' : 'Run Demo'}
            </button>
          </div>
        </div>

        <div className="card guide-card">
          <div className="card-header" style={{ marginBottom: 0 }}>
            <div className="card-title">
              <Layers3 size={16} />
              How to get results
            </div>
            <div className="health-pill" style={{ color: healthColor, borderColor: `${healthColor}44`, background: `${healthColor}14` }}>
              <span className="dot" style={{ background: healthColor, boxShadow: `0 0 6px ${healthColor}` }} />
              {metrics.system_health ?? 'stable'}
            </div>
          </div>

          <div className="guide-grid">
            <StepPill
              number="1"
              title="Submit or run demo"
              detail="Use the controls on the left to create work."
              active={tasks.length === 0}
            />
            <StepPill
              number="2"
              title="Watch task flow"
              detail="Running, queued, and failed counts update live."
              active={tasks.length > 0 && readyResults === 0}
            />
            <StepPill
              number="3"
              title="Open Task Queue"
              detail="Click a completed task row to view its result."
              active={readyResults > 0}
            />
          </div>

          <div className="system-metrics-grid">
            {[
              { label: 'Throughput', value: `${metrics.throughput?.toFixed(1) ?? 0}`, unit: 't/min', color: 'var(--blue)', icon: BarChart3 },
              { label: 'Avg Latency', value: `${metrics.avg_latency?.toFixed(2) ?? 0}`, unit: 's', color: 'var(--cyan)', icon: Clock3 },
              { label: 'Failure Rate', value: `${metrics.failure_rate?.toFixed(1) ?? 0}`, unit: '%', color: 'var(--rose)', icon: AlertTriangle },
              { label: 'Workers', value: metrics.active_workers ?? 0, unit: '', color: 'var(--violet)', icon: Server },
            ].map(({ label, value, unit, color, icon: Icon }) => (
              <div key={label} className="system-metric">
                <Icon size={15} style={{ color }} />
                <div>
                  <div className="system-metric-value" style={{ color }}>
                    {value}<span>{unit}</span>
                  </div>
                  <div className="system-metric-label">{label}</div>
                </div>
              </div>
            ))}
          </div>

          <div className="status-footer">
            <div>
              <Radio size={14} />
              Uptime {metrics.uptime ?? '0s'}
            </div>
            <button type="button" className="btn btn-ghost" onClick={() => setActiveView('tasks')}>
              View results <ArrowRight size={14} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
