import {
  Camera,
  Detection,
  PaginatedDetections,
  Alert,
  PaginatedAlerts,
  ModelStatus,
  AnalyticsSummary,
  OperationalSettings,
  PredictionResponse
} from '../types';

const BASE_URL = '/api/v1';

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorDetail = res.statusText;
    try {
      const data = await res.json();
      errorDetail = data.detail || JSON.stringify(data);
    } catch {
      // Use fallback
    }
    throw new Error(errorDetail || `Request failed with status ${res.status}`);
  }
  return res.json();
}

export const api = {
  async getHealth(): Promise<{ status: string; database: string; model_loaded: boolean; demo_mode: boolean; timestamp: string }> {
    const res = await fetch(`${BASE_URL}/health`);
    return handleResponse(res);
  },

  async getModelStatus(): Promise<ModelStatus> {
    const res = await fetch(`${BASE_URL}/model/status`);
    return handleResponse(res);
  },

  async predictImage(file: File, cameraId?: string): Promise<PredictionResponse> {
    const formData = new FormData();
    formData.append('file', file);
    if (cameraId) {
      formData.append('camera_id', cameraId);
    }
    const res = await fetch(`${BASE_URL}/predictions/image`, {
      method: 'POST',
      body: formData
    });
    return handleResponse(res);
  },

  async uploadVideo(file: File): Promise<{ task_id: string; status: string; filename: string }> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${BASE_URL}/predictions/video`, {
      method: 'POST',
      body: formData
    });
    return handleResponse(res);
  },

  async getVideoTaskStatus(taskId: string): Promise<any> {
    const res = await fetch(`${BASE_URL}/predictions/video/${taskId}`);
    return handleResponse(res);
  },

  async getCameras(): Promise<Camera[]> {
    const res = await fetch(`${BASE_URL}/monitoring/cameras`);
    return handleResponse(res);
  },

  async startMonitoring(cameraId: string): Promise<{ camera_id: string; status: string }> {
    const res = await fetch(`${BASE_URL}/monitoring/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ camera_id: cameraId })
    });
    return handleResponse(res);
  },

  async stopMonitoring(cameraId: string): Promise<{ camera_id: string; status: string }> {
    const res = await fetch(`${BASE_URL}/monitoring/stop`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ camera_id: cameraId })
    });
    return handleResponse(res);
  },

  async getMonitoringStatus(): Promise<{ active_workers_count: number; workers: any[] }> {
    const res = await fetch(`${BASE_URL}/monitoring/status`);
    return handleResponse(res);
  },

  async getDetections(
    page: number = 1,
    pageSize: number = 20,
    cameraId?: string,
    className?: string,
    minConfidence?: number
  ): Promise<PaginatedDetections> {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString()
    });
    if (cameraId) params.append('camera_id', cameraId);
    if (className) params.append('class_name', className);
    if (minConfidence !== undefined) params.append('min_confidence', minConfidence.toString());

    const res = await fetch(`${BASE_URL}/detections?${params.toString()}`);
    return handleResponse(res);
  },

  async getDetection(id: string): Promise<Detection> {
    const res = await fetch(`${BASE_URL}/detections/${id}`);
    return handleResponse(res);
  },

  async getAlerts(
    page: number = 1,
    pageSize: number = 20,
    status?: string,
    cameraId?: string
  ): Promise<PaginatedAlerts> {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString()
    });
    if (status) params.append('status', status);
    if (cameraId) params.append('camera_id', cameraId);

    const res = await fetch(`${BASE_URL}/alerts?${params.toString()}`);
    return handleResponse(res);
  },

  async updateAlertStatus(id: string, status: 'ACKNOWLEDGED' | 'CLOSED'): Promise<Alert> {
    const res = await fetch(`${BASE_URL}/alerts/${id}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status })
    });
    return handleResponse(res);
  },

  async getAnalyticsSummary(): Promise<AnalyticsSummary> {
    const res = await fetch(`${BASE_URL}/analytics/summary`);
    return handleResponse(res);
  },

  async getSettings(): Promise<OperationalSettings> {
    const res = await fetch(`${BASE_URL}/settings`);
    return handleResponse(res);
  },

  async updateSettings(settings: Partial<OperationalSettings>): Promise<OperationalSettings> {
    const res = await fetch(`${BASE_URL}/settings`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings)
    });
    return handleResponse(res);
  }
};
