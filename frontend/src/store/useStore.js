import { create } from 'zustand';

const MAX_LOGS = 200;
const MAX_HISTORY = 120;
const MAX_RETRIES = 50;

export const useStore = create((set, get) => ({
  // ── Connection ─────────────────────────────────────────────
  connectionStatus: 'disconnected', // connecting | connected | disconnected
  setConnectionStatus: (s) => set({ connectionStatus: s }),

  // ── Tasks ──────────────────────────────────────────────────
  tasks: {},   // task_id → task object
  updateTask: (task) => set((s) => ({
    tasks: { ...s.tasks, [task.task_id]: { ...(s.tasks[task.task_id] || {}), ...task } },
  })),
  setAllTasks: (taskList) => set({
    tasks: Object.fromEntries(taskList.map((t) => [t.task_id, t])),
  }),

  // ── Workers ────────────────────────────────────────────────
  workers: {},  // worker_id → worker object
  updateWorkers: (workerList) => set({
    workers: Object.fromEntries(workerList.map((w) => [w.worker_id, w])),
  }),

  // ── Metrics ────────────────────────────────────────────────
  metrics: {
    throughput: 0,
    avg_latency: 0,
    failure_rate: 0,
    queue_depth: 0,
    active_workers: 0,
    tasks_by_status: {},
    tasks_total: 0,
    completed: 0,
    failed: 0,
    retries: 0,
    system_health: 'stable',
    uptime: '0s',
  },
  metricsHistory: [],   // rolling 120-entry array
  setMetrics: (m) => set((s) => ({
    metrics: { ...s.metrics, ...m },
    metricsHistory: [
      ...s.metricsHistory.slice(-MAX_HISTORY + 1),
      { ...m, ts: Date.now() },
    ],
  })),

  // ── Logs ───────────────────────────────────────────────────
  logs: [],
  addLog: (log) => set((s) => ({
    logs: [...s.logs.slice(-MAX_LOGS + 1), { ...log, id: Date.now() + Math.random() }],
  })),
  clearLogs: () => set({ logs: [] }),

  // ── Retry Events ───────────────────────────────────────────
  retryEvents: [],
  addRetryEvent: (evt) => set((s) => ({
    retryEvents: [{ ...evt, id: Date.now() + Math.random() }, ...s.retryEvents.slice(0, MAX_RETRIES - 1)],
  })),

  // ── System Summary ─────────────────────────────────────────
  systemSummary: null,
  setSummary: (summary) => set({ systemSummary: summary }),

  // ── UI State ───────────────────────────────────────────────
  showSummaryModal: false,
  setShowSummaryModal: (v) => set({ showSummaryModal: v }),

  activeView: 'dashboard',  // dashboard | tasks | workers | logs
  setActiveView: (v) => set({ activeView: v }),

  sidebarCollapsed: false,
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),

  // ── Computed helpers ───────────────────────────────────────
  getTaskList: () => Object.values(get().tasks),
  getWorkerList: () => Object.values(get().workers),
}));
