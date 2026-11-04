export type ClassLabel = 'fire' | 'smoke' | 'normal';

export interface Camera {
  id: string;
  name: string;
  source_type: string;
  source_reference: string;
  location_label?: string;
  latitude?: number;
  longitude?: number;
  enabled: boolean;
  status: 'IDLE' | 'STREAMING' | 'ERROR' | 'OFFLINE';
  created_at: string;
  updated_at: string;
}

export interface Detection {
  id: string;
  camera_id?: string;
  camera_name?: string;
  source_type: string;
  predicted_class: ClassLabel;
  confidence: number;
  probabilities_json: Record<ClassLabel, number>;
  frame_timestamp: number;
  inference_ms: number;
  model_version: string;
  image_path?: string;
  heatmap_path?: string;
  temporal_state?: {
    is_temporally_verified: boolean;
    verified_class?: string;
    alert_triggered: boolean;
    status_label: string;
    positive_fire_count: number;
    positive_smoke_count: number;
    window_size: number;
    required_positives: number;
    in_cooldown: boolean;
    cooldown_remaining_seconds: number;
  };
  created_at: string;
}

export interface PaginatedDetections {
  items: Detection[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface Alert {
  id: string;
  camera_id?: string;
  camera_name?: string;
  detection_id?: string;
  alert_type: ClassLabel;
  severity: 'CRITICAL' | 'WARNING' | 'INFO';
  status: 'ACTIVE' | 'ACKNOWLEDGED' | 'CLOSED';
  first_seen_at: string;
  last_seen_at: string;
  acknowledged_at?: string;
  closed_at?: string;
  notification_status: string;
  created_at: string;
}

export interface PaginatedAlerts {
  items: Alert[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ModelStatus {
  loaded: boolean;
  model_name: string;
  version: string;
  classes: string[];
  device: string;
  demo_mode: boolean;
  checkpoint_path: string;
  fire_threshold: number;
  smoke_threshold: number;
}

export interface AnalyticsSummary {
  total_detections: number;
  classes: {
    fire: number;
    smoke: number;
    normal: number;
  };
  active_alerts: number;
  total_alerts: number;
  total_cameras: number;
  active_cameras: number;
  avg_inference_ms: number;
  suppression_efficiency: {
    raw_positives: number;
    verified_alerts: number;
    suppressed_transients: number;
    suppression_percentage: number;
  };
  daily_trend: Array<{
    date: string;
    detections: number;
    alerts: number;
  }>;
}

export interface OperationalSettings {
  fire_threshold: number;
  smoke_threshold: number;
  temporal_window: number;
  temporal_required_positives: number;
  alert_cooldown_seconds: number;
  max_upload_mb: number;
  max_video_seconds: number;
  model_demo_mode: boolean;
}

export interface PredictionResponse {
  detection_id?: string;
  predicted_class: ClassLabel;
  confidence: number;
  probabilities: Record<ClassLabel, number>;
  inference_ms: number;
  model_version: string;
  original_image_url?: string;
  heatmap_image_url?: string;
  temporally_verified: boolean;
  alert_triggered: boolean;
  alert_id?: string;
  status_label: string;
  demo_mode: boolean;
}
