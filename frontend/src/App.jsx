import { useWebSocket } from './hooks/useWebSocket';
import { useStore } from './store/useStore';

import Layout from './components/Layout';
import Dashboard from './components/Dashboard';
import TaskTable from './components/TaskTable';
import TaskGraph from './components/TaskGraph';
import WorkerHealth from './components/WorkerHealth';
import MetricsPanel from './components/MetricsPanel';
import LogStream from './components/LogStream';
import RetryEvents from './components/RetryEvents';
import SystemSummary from './components/SystemSummary';

function AppContent() {
  const activeView      = useStore((s) => s.activeView);
  const showSummary     = useStore((s) => s.showSummaryModal);

  return (
    <Layout>
      {/* System summary modal */}
      {showSummary && <SystemSummary />}

      {/* Dashboard view */}
      {activeView === 'dashboard' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <Dashboard />
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <div style={{ height: 320 }}><TaskGraph /></div>
            <div style={{ height: 320 }}><WorkerHealth /></div>
          </div>
          <div style={{ height: 460 }}><MetricsPanel /></div>
        </div>
      )}

      {/* Tasks view */}
      {activeView === 'tasks' && (
        <div style={{ height: 'calc(100vh - 100px)' }}>
          <TaskTable />
        </div>
      )}

      {/* Workers view */}
      {activeView === 'workers' && (
        <div style={{ height: 'calc(100vh - 100px)' }}>
          <WorkerHealth />
        </div>
      )}

      {/* Logs view */}
      {activeView === 'logs' && (
        <div style={{ height: 'calc(100vh - 100px)' }}>
          <LogStream />
        </div>
      )}

      {/* Retries view */}
      {activeView === 'retries' && (
        <div style={{ height: 'calc(100vh - 100px)' }}>
          <RetryEvents />
        </div>
      )}
    </Layout>
  );
}

export default function App() {
  // Initialize WebSocket connection at root level
  useWebSocket();
  return <AppContent />;
}
