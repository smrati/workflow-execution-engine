import axios from 'axios';

const API_BASE = '/api';
const ACCESS_TOKEN_KEY = 'access_token';

function getAuthHeaders(): Record<string, string> {
  const token = localStorage.getItem(ACCESS_TOKEN_KEY);
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export interface Workflow {
  name: string;
  command: string;
  cron: string;
  enabled: boolean;
  timeout: number | null;
  retry_count: number;
  retry_delay: number;
  working_dir: string | null;
  env: Record<string, string>;
  next_run: string | null;
}

export interface WorkflowDetail extends Workflow {
  last_run: string | null;
  stats: {
    total_runs: number;
    successful_runs: number;
    failed_runs: number;
    timeout_runs: number;
  } | null;
}

export interface Run {
  id: number | null;
  workflow_name: string;
  command: string;
  start_time: string;
  end_time: string | null;
  exit_code: number | null;
  status: 'running' | 'success' | 'failed' | 'timeout' | 'retry';
  log_file_path: string | null;
  attempt: number;
  triggered_by: string | null;
  duration_seconds: number | null;
}

export interface RunListResponse {
  runs: Run[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface OverviewStats {
  total_workflows: number;
  enabled_workflows: number;
  total_runs: number;
  successful_runs: number;
  failed_runs: number;
  recent_runs: Run[];
  running_tasks: number;
}

export interface EngineStatus {
  running: boolean;
  workflows_count: number;
  enabled_workflows: number;
  running_tasks: number;
  max_concurrent: number;
}

export interface WorkflowStats {
  workflow_name: string;
  total_runs: number;
  successful_runs: number;
  failed_runs: number;
  timeout_runs: number;
  success_rate: number;
}

export interface LogResponse {
  run_id: number;
  workflow_name: string;
  log_file_path: string;
  content: string;
  exists: boolean;
}

export interface DeleteRunsResponse {
  deleted_count: number;
  deleted_log_files: number;
  errors: string[];
}

const api = {
  async getWorkflows(enabledOnly = false): Promise<Workflow[]> {
    const response = await axios.get(`${API_BASE}/workflows`, {
      params: { enabled_only: enabledOnly },
      headers: getAuthHeaders()
    });
    return response.data;
  },

  async getWorkflow(name: string): Promise<WorkflowDetail> {
    const response = await axios.get(`${API_BASE}/workflows/${encodeURIComponent(name)}`, {
      headers: getAuthHeaders()
    });
    return response.data;
  },

  async getWorkflowSchedule(name: string): Promise<{ next_run: string | null; last_run: string | null }> {
    const response = await axios.get(`${API_BASE}/workflows/${encodeURIComponent(name)}/schedule`, {
      headers: getAuthHeaders()
    });
    return response.data;
  },

  async triggerWorkflow(name: string): Promise<{ message: string }> {
    const response = await axios.post(`${API_BASE}/workflows/${encodeURIComponent(name)}/run`, {}, {
      headers: getAuthHeaders()
    });
    return response.data;
  },

  async enableWorkflow(name: string): Promise<{ message: string; enabled: boolean }> {
    const response = await axios.put(`${API_BASE}/workflows/${encodeURIComponent(name)}/enable`, {}, {
      headers: getAuthHeaders()
    });
    return response.data;
  },

  async disableWorkflow(name: string): Promise<{ message: string; enabled: boolean }> {
    const response = await axios.put(`${API_BASE}/workflows/${encodeURIComponent(name)}/disable`, {}, {
      headers: getAuthHeaders()
    });
    return response.data;
  },

  async getRuns(params: {
    workflow_name?: string;
    status?: string;
    page?: number;
    page_size?: number;
  } = {}): Promise<RunListResponse> {
    const response = await axios.get(`${API_BASE}/runs`, { 
      params,
      headers: getAuthHeaders()
    });
    return response.data;
  },

  async getRun(id: number): Promise<Run> {
    const response = await axios.get(`${API_BASE}/runs/${id}`, {
      headers: getAuthHeaders()
    });
    return response.data;
  },

  async getEngineStatus(): Promise<EngineStatus> {
    const response = await axios.get(`${API_BASE}/stats/engine`, {
      headers: getAuthHeaders()
    });
    return response.data;
  },

  async getOverviewStats(): Promise<OverviewStats> {
    const response = await axios.get(`${API_BASE}/stats/overview`, {
      headers: getAuthHeaders()
    });
    return response.data;
  },

  async getWorkflowStats(name: string): Promise<WorkflowStats> {
    const response = await axios.get(`${API_BASE}/stats/workflows/${encodeURIComponent(name)}`, {
      headers: getAuthHeaders()
    });
    return response.data;
  },

  async getRunLog(runId: number): Promise<LogResponse> {
    const response = await axios.get(`${API_BASE}/logs/${runId}`, {
      headers: getAuthHeaders()
    });
    return response.data;
  },

  async deleteRuns(params: {
    before?: string;
    after?: string;
    workflow_name?: string;
  }): Promise<DeleteRunsResponse> {
    const response = await axios.delete(`${API_BASE}/runs/cleanup`, {
      data: params,
      headers: getAuthHeaders()
    });
    return response.data;
  },
};

export default api;
