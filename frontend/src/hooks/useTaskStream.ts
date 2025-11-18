/**
 * useTaskStream - React hook for receiving real-time task updates via Server-Sent Events
 */
import { useEffect, useRef, useState } from 'react';
import { api } from '../services/api';
import Cookies from 'js-cookie';

export interface TaskUpdate {
  task_id: number;
  task_type: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  result?: any;
  error_message?: string;
  progress?: number;
}

interface UseTaskStreamResult {
  isConnected: boolean;
  lastUpdate: TaskUpdate | null;
  taskResults: Map<number, TaskUpdate>;
  connectionError: string | null;
}

export const useTaskStream = (): UseTaskStreamResult => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<TaskUpdate | null>(null);
  const [taskResults, setTaskResults] = useState<Map<number, TaskUpdate>>(new Map());
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    // Get auth token from cookie using same Cookies library as rest of app
    const token = Cookies.get('auth_token');
    console.log('SSE: Checking auth_token cookie:', token ? 'Found' : 'Not found');
    console.log('SSE: All cookies:', document.cookie);
    
    if (!token) {
      console.warn('No auth token available for SSE connection');
      setConnectionError('Authentication required');
      return;
    }

    // Create SSE connection with auth token in URL (EventSource doesn't support headers)
    const baseURL = api.defaults.baseURL || '';
    const url = `${baseURL}/task-stream/?token=${encodeURIComponent(token)}`;
    console.log('SSE: Attempting connection to:', url);
    const eventSource = new EventSource(url);
    eventSourceRef.current = eventSource;

    // Connection opened
    eventSource.addEventListener('open', () => {
      console.log('SSE connection opened');
      setIsConnected(true);
      setConnectionError(null);
    });

    // Connection established event
    eventSource.addEventListener('connected', (event) => {
      const data = JSON.parse(event.data);
      console.log('SSE connected:', data);
    });

    // Task update event
    eventSource.addEventListener('task_update', (event) => {
      const taskUpdate: TaskUpdate = JSON.parse(event.data);
      console.log('Task update received:', taskUpdate);
      
      setLastUpdate(taskUpdate);
      
      // Store result in map
      setTaskResults((prev) => {
        const updated = new Map(prev);
        updated.set(taskUpdate.task_id, taskUpdate);
        return updated;
      });
    });

    // Keepalive event
    eventSource.addEventListener('keepalive', (event) => {
      console.debug('SSE keepalive:', event.data);
    });

    // Connection error
    eventSource.addEventListener('error', (error) => {
      console.error('SSE connection error:', error);
      setIsConnected(false);
      setConnectionError('Connection error - retrying...');
      
      // EventSource automatically reconnects, but we can add custom logic here
    });

    // Cleanup on unmount
    return () => {
      console.log('Closing SSE connection');
      eventSource.close();
      eventSourceRef.current = null;
      setIsConnected(false);
    };
  }, []); // Empty dependency array - connect once on mount

  return {
    isConnected,
    lastUpdate,
    taskResults,
    connectionError,
  };
};
