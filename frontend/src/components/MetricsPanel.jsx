import {
  AreaChart, Area, LineChart, Line, BarChart, Bar,
  PieChart, Pie, Cell,
  ResponsiveContainer, Tooltip, XAxis, YAxis, CartesianGrid, Legend,
} from 'recharts';
import { useStore } from '../store/useStore';

const PIE_COLORS = {
  created:    '#4a6080',
  queued:     '#3b82f6',
  assigned:   '#06b6d4',
  running:    '#f59e0b',
  completed:  '#10b981',
  validated:  '#8b5cf6',
  failed:     '#f43f5e',
  stored:     '#a855f7',
};

function StatCard({ label, value, unit, color, sublabel }) {
  return (
    <div style={{
      background: `${color}10`, border: `1px solid ${color}30`,
      borderRadius: 10, padding: '14px 16px',
    }}>
      <div className="metric-value" style={{ color }}>{value}<span style={{ fontSize: 14, fontWeight: 500, marginLeft: 3 }}>{unit}</span></div>
      <div className="metric-label">{label}</div>
      {sublabel && <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 4 }}>{sublabel}</div>}
    </div>
  );
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-bright)', borderRadius: 8, padding: '8px 12px', fontSize: 12 }}>
      {payload.map((p) => (
        <div key={p.name} style={{ color: p.color }}>
          {p.name}: <strong>{typeof p.value === 'number' ? p.value.toFixed(2) : p.value}</strong>
        </div>
      ))}
    </div>
  );
};

export default function MetricsPanel() {
  const metrics   = useStore((s) => s.metrics);
  const history   = useStore((s) => s.metricsHistory);

  const data = history.slice(-40).map((h, i) => ({
    t: i,
    throughput: h.throughput ?? 0,
    latency:    h.avg_latency ?? 0,
    queueDepth: h.queue_depth ?? 0,
    failures:   h.failure_rate ?? 0,
  }));

  const statusCounts = metrics.tasks_by_status || {};
  const pieData = Object.entries(statusCounts)
    .filter(([, v]) => v > 0)
    .map(([name, value]) => ({ name, value }));

  const healthColor = metrics.system_health === 'stable' ? 'var(--emerald)' : metrics.system_health === 'degraded' ? 'var(--amber)' : 'var(--rose)';

  return (
    <div className="card h-full" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div className="card-header">
        <div className="card-title"><span>📊</span> System Metrics</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12 }}>
          <div className="dot" style={{ background: healthColor, boxShadow: `0 0 6px ${healthColor}` }} />
          <span style={{ color: healthColor, fontWeight: 600, textTransform: 'capitalize' }}>{metrics.system_health}</span>
          <span style={{ color: 'var(--text-muted)', marginLeft: 4 }}>{metrics.uptime}</span>
        </div>
      </div>

      {/* KPI Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10 }}>
        <StatCard label="Throughput"    value={metrics.throughput?.toFixed(1)    ?? 0} unit="t/min" color="var(--blue)" />
        <StatCard label="Avg Latency"   value={metrics.avg_latency?.toFixed(2)   ?? 0} unit="s"     color="var(--cyan)" />
        <StatCard label="Failure Rate"  value={metrics.failure_rate?.toFixed(1)  ?? 0} unit="%"     color="var(--rose)" />
        <StatCard label="Retries"       value={metrics.retries                   ?? 0} unit=""      color="var(--amber)" />
      </div>

      {/* Charts */}
      <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, minHeight: 0 }}>
        {/* Throughput */}
        <div style={{ background: 'var(--bg-elevated)', borderRadius: 10, padding: '12px 4px 4px 4px' }}>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', paddingLeft: 12, marginBottom: 4 }}>Throughput (tasks/min)</div>
          <ResponsiveContainer width="100%" height={110}>
            <AreaChart data={data} margin={{ top: 0, right: 8, left: -22, bottom: 0 }}>
              <defs>
                <linearGradient id="gTP" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.5} />
                  <stop offset="100%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="t" hide />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip content={<CustomTooltip />} />
              <Area type="monotone" dataKey="throughput" name="Throughput" stroke="#3b82f6" fill="url(#gTP)" strokeWidth={2} dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Latency */}
        <div style={{ background: 'var(--bg-elevated)', borderRadius: 10, padding: '12px 4px 4px 4px' }}>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', paddingLeft: 12, marginBottom: 4 }}>Avg Latency (s)</div>
          <ResponsiveContainer width="100%" height={110}>
            <LineChart data={data} margin={{ top: 0, right: 8, left: -22, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="t" hide />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip content={<CustomTooltip />} />
              <Line type="monotone" dataKey="latency" name="Latency" stroke="#06b6d4" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Failure Rate */}
        <div style={{ background: 'var(--bg-elevated)', borderRadius: 10, padding: '12px 4px 4px 4px' }}>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', paddingLeft: 12, marginBottom: 4 }}>Failure Rate (%)</div>
          <ResponsiveContainer width="100%" height={110}>
            <AreaChart data={data} margin={{ top: 0, right: 8, left: -22, bottom: 0 }}>
              <defs>
                <linearGradient id="gFR" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#f43f5e" stopOpacity={0.4} />
                  <stop offset="100%" stopColor="#f43f5e" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="t" hide />
              <YAxis tick={{ fontSize: 10 }} domain={[0, 100]} />
              <Tooltip content={<CustomTooltip />} />
              <Area type="monotone" dataKey="failures" name="Failure %" stroke="#f43f5e" fill="url(#gFR)" strokeWidth={2} dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Status Breakdown Pie */}
        <div style={{ background: 'var(--bg-elevated)', borderRadius: 10, padding: '12px 4px 4px 4px' }}>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', paddingLeft: 12, marginBottom: 4 }}>Task Status Breakdown</div>
          {pieData.length > 0 ? (
            <ResponsiveContainer width="100%" height={110}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="40%" cy="50%"
                  innerRadius={28} outerRadius={44}
                  dataKey="value" paddingAngle={2}
                >
                  {pieData.map((entry) => (
                    <Cell key={entry.name} fill={PIE_COLORS[entry.name] || '#888'} />
                  ))}
                </Pie>
                <Legend
                  layout="vertical" align="right" verticalAlign="middle"
                  formatter={(v) => <span style={{ fontSize: 10, color: 'var(--text-secondary)' }}>{v}</span>}
                />
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div style={{ height: 110, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: 12 }}>
              No task data yet
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
