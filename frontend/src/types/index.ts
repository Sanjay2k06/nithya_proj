export type ClassLabel = 'fire' | 'smoke' | 'normal';
export type AnalysisProvider = 'firenet' | 'gemini';

export interface VideoAnalysisFrame {
  timestamp_seconds: number;
  classification: ClassLabel | 'uncertain';
  observation: string;
  heatmap_image_url?: string | null;
}

export interface VideoAnalysisTask {
  task_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  filename: string;
  error?: string | null;
  analysis_provider: AnalysisProvider;
  analysis_summary?: string | null;
  frame_results: VideoAnalysisFrame[];
  total_frames?: number;
  processed_frames?: number;
  detections_count?: number;
  alerts_count?: number;
  created_at: string;
}

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
  source_id?: string;
  source_name?: string;
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
  source_id?: string;
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
  gemini_configured: boolean;
  gemini_model: string;
  error?: string | null;
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

export interface NotificationRecord {
  id: string;
  alert_id?: string;
  channel: string;
  status: 'DELIVERED' | 'FAILED';
  recipient?: string;
  message?: string;
  evidence_path?: string;
  retry_count: number;
  attempted_at: string;
  delivered_at?: string;
  error_code?: string;
}

export interface NotificationHistory {
  items: NotificationRecord[];
  total: number;
}

export interface TelegramStatus {
  enabled: boolean;
  configured: boolean;
  connection_status: 'disabled' | 'unconfigured' | 'not_tested' | 'connected' | 'error';
  recipient_hint?: string;
  total_messages: number;
  delivered_messages: number;
  failed_messages: number;
  last_notification_time?: string;
  last_notification_message?: string;
  last_incident_id?: string;
}

export interface PredictionResponse {
  detection_id?: string;
  source_id?: string;
  predicted_class: ClassLabel | 'uncertain';
  confidence?: number | null;
  probabilities: Partial<Record<ClassLabel, number>>;
  inference_ms: number;
  model_version: string;
  analysis_provider?: 'firenet' | 'gemini';
  analysis_text?: string | null;
  analysis_evidence?: string[];
  analysis_caveat?: string | null;
  original_image_url?: string;
  heatmap_image_url?: string;
  temporally_verified: boolean;
  alert_triggered: boolean;
  alert_id?: string;
  notification_status?: string;
  status_label: string;
  demo_mode: boolean;
  processing_duration_ms?: number;
  visual_motion?: {
    mean_displacement_px_per_sample: number;
    moving_pixel_percent: number;
  } | null;
  temporal_state?: {
    is_temporally_verified: boolean;
    verified_class?: ClassLabel;
    alert_triggered: boolean;
    status_label: string;
    positive_fire_count: number;
    positive_smoke_count: number;
    window_size: number;
    required_positives: number;
    in_cooldown: boolean;
    cooldown_remaining_seconds: number;
  };
}

export interface DemoCctvSource {
  source_id: string;
  name: string;
  description: string;
  file_name: string;
  available: boolean;
  video_url: string;
  source_type: 'simulated_cctv';
  source_status?: string;
  playback_status?: string;
  processing_status?: string;
  last_processed_at?: string | null;
  last_processed_video_seconds?: number | null;
}

export interface DemoMonitoringStatus {
  selected_source: DemoCctvSource | null;
  is_monitoring: boolean;
  is_processing: boolean;
  latest_detection: PredictionResponse | null;
  last_processed_video_seconds: number | null;
  processing_delay_ms: number | null;
  processed_frames: number;
  status: 'IDLE' | 'IN_PROGRESS' | 'VERIFYING' | 'VERIFIED' | 'STOPPED' | 'ERROR';
  error?: string | null;
}

export interface EnvironmentalReading {
  id: string;
  source_id: string;
  temperature_c?: number | null;
  humidity_percent?: number | null;
  wind_speed_mps?: number | null;
  wind_direction_degrees?: number | null;
  smoke_sensor_value?: number | null;
  recorded_at: string;
  created_at: string;
}
