/**
 * API service for agent tasks management
 */
import api from './api';

export interface AgentTask {
  id: number;
  task_type: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  title: string;
  description: string | null;
  created_by: number;
  payload: Record<string, any> | null;
  result: Record<string, any> | null;
  error_message: string | null;
  progress: number;
  created_at: string;
  updated_at: string;
  started_at: string | null;
  completed_at: string | null;
}

export interface AgentTaskCreate {
  task_type: string;
  title: string;
  description?: string;
  payload?: Record<string, any>;
}

export interface AgentTaskUpdate {
  status?: string;
  progress?: number;
  result?: Record<string, any>;
  error_message?: string;
}

export interface AgentTaskListResponse {
  tasks: AgentTask[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface TaskStats {
  total: number;
  pending: number;
  running: number;
  completed: number;
  failed: number;
  cancelled: number;
}

export const agentTasksService = {
  /**
   * Get all agent tasks with pagination and filters
   */
  async getAll(params?: {
    status?: string;
    task_type?: string;
    page?: number;
    page_size?: number;
  }): Promise<AgentTaskListResponse> {
    const response = await api.get('/agent-tasks/', { params });
    return response.data;
  },

  /**
   * Get task statistics
   */
  async getStats(): Promise<TaskStats> {
    const response = await api.get('/agent-tasks/stats');
    return response.data;
  },

  /**
   * Get a specific task by ID
   */
  async getById(id: number): Promise<AgentTask> {
    const response = await api.get(`/agent-tasks/${id}`);
    return response.data;
  },

  /**
   * Create a new agent task
   */
  async create(task: AgentTaskCreate): Promise<AgentTask> {
    const response = await api.post('/agent-tasks/', task);
    return response.data;
  },

  /**
   * Update a task
   */
  async update(id: number, updates: AgentTaskUpdate): Promise<AgentTask> {
    const response = await api.patch(`/agent-tasks/${id}`, updates);
    return response.data;
  },

  /**
   * Cancel a running task
   */
  async cancel(id: number): Promise<AgentTask> {
    const response = await api.put(`/agent-tasks/${id}/cancel`);
    return response.data;
  },

  /**
   * Delete a task
   */
  async delete(id: number): Promise<void> {
    await api.delete(`/agent-tasks/${id}`);
  },
};
