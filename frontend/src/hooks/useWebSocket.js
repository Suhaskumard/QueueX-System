import { useEffect, useRef, useCallback } from 'react';
import { useStore } from '../store/useStore';

const WS_URL = 'ws://localhost:8000/ws';
const BASE_DELAY = 1000;
const MAX_DELAY = 30000;

export function useWebSocket() {
  const wsRef = useRef(null);
  const reconnectTimer = useRef(null);
  const attemptRef = useRef(0);
  const mountedRef = useRef(true);

  const {
    setConnectionStatus,
    updateTask,
    setAllTasks,
    updateWorkers,
    setMetrics,
    addLog,
    addRetryEvent,
    setSummary,
    setShowSummaryModal,
  } = useStore();

  const handleMessage = useCallback((raw) => {
    let msg;
    try { msg = JSON.parse(raw); } catch { return; }
    const { type, data } = msg;

    switch (type) {
      case 'initial_state':
        if (data.tasks)   setAllTasks(data.tasks);
        if (data.workers) updateWorkers(data.workers);
        if (data.summary) setSummary(data.summary);
        break;
      case 'task_update':
        updateTask(data);
        break;
      case 'worker_update':
        updateWorkers(Array.isArray(data) ? data : [data]);
        break;
      case 'metric_update':
        setMetrics(data);
        break;
      case 'log_entry':
        addLog(data);
        break;
      case 'retry_event':
        addRetryEvent(data);
        break;
      case 'system_summary':
        setSummary(data);
        setShowSummaryModal(true);
        break;
      default:
        break;
    }
  }, [setAllTasks, updateTask, updateWorkers, setMetrics, addLog, addRetryEvent, setSummary, setShowSummaryModal]);

  useEffect(() => {
    const connect = () => {
      if (!mountedRef.current) return;
      if (wsRef.current?.readyState === WebSocket.OPEN) return;

      setConnectionStatus('connecting');
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        if (!mountedRef.current) { ws.close(); return; }
        attemptRef.current = 0;
        setConnectionStatus('connected');
      };

      ws.onmessage = (e) => handleMessage(e.data);

      ws.onclose = () => {
        if (!mountedRef.current) return;
        setConnectionStatus('disconnected');
        const delay = Math.min(BASE_DELAY * 2 ** attemptRef.current, MAX_DELAY);
        attemptRef.current += 1;
        reconnectTimer.current = setTimeout(connect, delay);
      };

      ws.onerror = () => ws.close();
    };

    mountedRef.current = true;
    connect();
    return () => {
      mountedRef.current = false;
      clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [handleMessage, setConnectionStatus]);

  return { ws: wsRef.current };
}
