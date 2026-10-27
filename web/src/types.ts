export type UserRole = 'admin' | 'viewer';

export interface User {
  id: number;
  username: string;
  email: string;
  role: UserRole;
  full_name: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

export interface KPIStats {
  total_events_24h: number;
  max_magnitude_24h: number;
  avg_magnitude_24h: number;
  tsunami_events_24h: number;
  data_quality_score: number;
  last_updated_at: string | null;
  active_anomalies_24h: number;
}

export interface EarthquakeEvent {
  event_id: string;
  mag: number;
  place: string;
  event_time: string;
  updated_time: string;
  tsunami: number;
  sig: number;
  status: string;
  mag_type?: string;
  event_type: string;
  url?: string;
  longitude: number;
  latitude: number;
  depth_km: number;
}

export interface PaginatedEvents {
  total: number;
  limit: number;
  offset: number;
  items: EarthquakeEvent[];
}

export interface HourlyBucket {
  hour: string;
  count: number;
  avg_mag: number;
}

export interface MagBucket {
  bucket: string;
  count: number;
}

export interface RegionCount {
  region: string;
  count: number;
  avg_mag: number;
}

export interface TimeseriesStats {
  hourly: HourlyBucket[];
  magnitude_distribution: MagBucket[];
  top_regions: RegionCount[];
}

export interface DailyReport {
  id: number;
  report_date: string;
  title: string;
  executive_summary: string;
  narrative_report: string;
  stats_json: Record<string, any>;
  provider: string;
  model: string;
  latency_ms?: number;
  is_fallback: boolean;
  created_at: string;
}

export interface QualityMetricSummary {
  batch_id: string;
  evaluated_records: number;
  passed_records: number;
  rejected_records: number;
  quality_score: number;
  freshness_seconds?: number;
  created_at: string;
}

export interface AnomalyAlertSummary {
  id: number;
  alert_time: string;
  metric_name: string;
  current_value: number;
  z_score: number;
  severity: string;
  explanation: string;
}

export interface PipelineStatus {
  total_curated_events: number;
  total_quarantined_events: number;
  latest_quality_score: number;
  data_freshness_seconds?: number;
  last_sync_timestamp?: string;
  recent_batches: QualityMetricSummary[];
  recent_anomalies: AnomalyAlertSummary[];
}

export interface QuarantineRecord {
  id: number;
  batch_id: string;
  event_id?: string;
  rejection_reasons: string[];
  failed_rules: string[];
  raw_record: Record<string, any>;
  quarantined_at: string;
}
