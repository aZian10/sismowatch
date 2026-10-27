import {
  User,
  KPIStats,
  PaginatedEvents,
  EarthquakeEvent,
  TimeseriesStats,
  DailyReport,
  PipelineStatus,
  QuarantineRecord
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class ApiService {
  private token: string | null = null;

  constructor() {
    this.token = localStorage.getItem('sismowatch_token');
  }

  setToken(token: string | null) {
    this.token = token;
    if (token) {
      localStorage.setItem('sismowatch_token', token);
    } else {
      localStorage.removeItem('sismowatch_token');
    }
  }

  getToken(): string | null {
    return this.token || localStorage.getItem('sismowatch_token');
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    const token = this.getToken();

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    try {
      const response = await fetch(url, { ...options, headers });

      if (response.status === 401) {
        this.setToken(null);
        window.dispatchEvent(new Event('sismowatch_unauthorized'));
        throw new Error('Session expired or unauthorized. Please log in again.');
      }

      if (!response.ok) {
        let errorDetail = `Request failed with status ${response.status}`;
        try {
          const errData = await response.json();
          errorDetail = errData.detail || errorDetail;
        } catch (_) {}
        throw new Error(errorDetail);
      }

      return await response.json();
    } catch (err: any) {
      throw err;
    }
  }

  // Authentication
  async login(username: string, password: string): Promise<{ access_token: string; user: User }> {
    const res = await this.request<{ access_token: string; user: User }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password })
    });
    this.setToken(res.access_token);
    return res;
  }

  async getMe(): Promise<User> {
    return this.request<User>('/auth/me');
  }

  // Dashboard & KPIs
  async getKPIs(): Promise<KPIStats> {
    return this.request<KPIStats>('/api/kpis');
  }

  async getEvents(params: {
    min_mag?: number;
    max_mag?: number;
    region?: string;
    start_date?: string;
    end_date?: string;
    tsunami_only?: boolean;
    limit?: number;
    offset?: number;
  }): Promise<PaginatedEvents> {
    const query = new URLSearchParams();
    if (params.min_mag !== undefined && params.min_mag !== null) query.append('min_mag', params.min_mag.toString());
    if (params.max_mag !== undefined && params.max_mag !== null) query.append('max_mag', params.max_mag.toString());
    if (params.region) query.append('region', params.region);
    if (params.start_date) query.append('start_date', params.start_date);
    if (params.end_date) query.append('end_date', params.end_date);
    if (params.tsunami_only) query.append('tsunami_only', 'true');
    if (params.limit) query.append('limit', params.limit.toString());
    if (params.offset !== undefined) query.append('offset', params.offset.toString());

    return this.request<PaginatedEvents>(`/api/events?${query.toString()}`);
  }

  async getEventById(id: string): Promise<EarthquakeEvent> {
    return this.request<EarthquakeEvent>(`/api/events/${id}`);
  }

  async getStats(hours: number = 24): Promise<TimeseriesStats> {
    return this.request<TimeseriesStats>(`/api/stats/timeseries?hours=${hours}`);
  }

  // Reports
  async getReports(limit: number = 20, offset: number = 0): Promise<{ total: number; items: DailyReport[] }> {
    return this.request<{ total: number; items: DailyReport[] }>(`/api/reports?limit=${limit}&offset=${offset}`);
  }

  getExportUrl(format: 'csv' | 'html'): string {
    const token = this.getToken();
    return `${API_BASE_URL}/api/reports/export?format=${format}&token=${token || ''}`;
  }

  // Pipeline Status
  async getPipelineStatus(): Promise<PipelineStatus> {
    return this.request<PipelineStatus>('/api/pipeline/status');
  }

  // Admin Operations
  async getQuarantine(limit: number = 50, offset: number = 0): Promise<{ total: number; items: QuarantineRecord[] }> {
    return this.request<{ total: number; items: QuarantineRecord[] }>(`/api/quality/quarantine?limit=${limit}&offset=${offset}`);
  }

  async triggerBackfill(payload: { starttime?: string; endtime?: string; minmagnitude?: number }): Promise<any> {
    return this.request<any>('/api/admin/backfill', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }

  async regenerateReport(target_date?: string): Promise<any> {
    return this.request<any>('/api/admin/reports/regenerate', {
      method: 'POST',
      body: JSON.stringify({ target_date })
    });
  }

  // SSE Stream URL
  getStreamUrl(): string {
    const token = this.getToken();
    return `${API_BASE_URL}/api/stream?token=${encodeURIComponent(token || '')}`;
  }
}

export const api = new ApiService();
