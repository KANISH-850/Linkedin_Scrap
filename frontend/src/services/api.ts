import type {
  Application,
  DashboardAnalytics,
  DashboardSummary,
  DiscoveryRun,
  DiscoverySource,
  FollowUp,
  MessageDraft,
  OpportunityDetail,
  PaginatedOpportunities,
  ReplyAnalyzeResponse,
  UserProfile,
} from '../types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

const TOKEN_KEY = 'rp_access_token';

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setStoredToken(token: string | null): void {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_KEY);
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getStoredToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> | undefined),
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (res.status === 401) {
    setStoredToken(null);
    if (!window.location.pathname.startsWith('/login')) {
      window.location.href = '/login';
    }
    throw new Error('Unauthorized');
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
    throw new Error(err.detail || `Request failed with status ${res.status}`);
  }

  return res.json() as Promise<T>;
}

export const api = {
  login: (email: string, password: string) =>
    request<{ access_token: string; user_email: string; full_name: string }>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),

  getMe: () => request<{ id: number; email: string; full_name: string; role: string }>('/api/auth/me'),

  getSummary: () => request<DashboardSummary>('/api/dashboard/summary'),
  getAnalytics: () => request<DashboardAnalytics>('/api/dashboard/analytics'),

  getProfile: () => request<UserProfile>('/api/profile'),
  updateProfile: (payload: Partial<UserProfile>) =>
    request<UserProfile>('/api/profile', {
      method: 'PUT',
      body: JSON.stringify(payload),
    }),

  getOpportunities: (params: Record<string, string | number | undefined>) => {
    const qs = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== '' && v !== 'all') {
        qs.set(k, String(v));
      }
    });
    return request<PaginatedOpportunities>(`/api/opportunities?${qs.toString()}`);
  },

  getOpportunity: (id: number) => request<OpportunityDetail>(`/api/opportunities/${id}`),

  updateOpportunityStatus: (
    id: number,
    payload: {
      tracking_status?: string;
      is_interested?: boolean;
      personal_notes?: string;
      next_action?: string;
      follow_up_date?: string;
      note?: string;
    }
  ) =>
    request<OpportunityDetail>(`/api/opportunities/${id}/status`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }),

  draftMessage: (id: number, draft_type: string, contact_name?: string, custom_context?: string) =>
    request<MessageDraft>(`/api/opportunities/${id}/draft-message`, {
      method: 'POST',
      body: JSON.stringify({ draft_type, contact_name, custom_context }),
    }),

  createFollowUp: (id: number, due_date: string, notes?: string) =>
    request<FollowUp>(`/api/opportunities/${id}/follow-up`, {
      method: 'POST',
      body: JSON.stringify({ due_date, notes }),
    }),

  getFollowUps: () => request<FollowUp[]>('/api/follow-ups'),
  updateFollowUp: (id: number, payload: { status?: string; notes?: string; due_date?: string }) =>
    request<FollowUp>(`/api/follow-ups/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }),

  getApplications: () => request<Application[]>('/api/applications'),
  createApplication: (payload: {
    opportunity_id: number;
    status?: string;
    portal_url?: string;
    resume_version?: string;
    notes?: string;
  }) =>
    request<Application>('/api/applications', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getSources: () => request<DiscoverySource[]>('/api/sources'),
  updateSource: (id: number, payload: { enabled?: boolean; frequency_hours?: number; config_json?: Record<string, unknown> }) =>
    request<DiscoverySource>(`/api/sources/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }),

  runDiscovery: () => request<DiscoveryRun>('/api/discovery/run', { method: 'POST' }),
  getDiscoveryRuns: () => request<DiscoveryRun[]>('/api/discovery/runs'),

  submitManualOpportunity: (payload: {
    url?: string;
    raw_text?: string;
    title_hint?: string;
    organization_hint?: string;
    category_hint?: string;
  }) =>
    request<OpportunityDetail>('/api/discovery/submit', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  analyzeReply: (payload: { opportunity_id?: number; reply_text: string; sender_name?: string }) =>
    request<ReplyAnalyzeResponse>('/api/replies/analyze', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getScoringWeights: () => request<Record<string, number>>('/api/settings/weights'),
  updateScoringWeights: (weights: Record<string, number>) =>
    request<Record<string, number>>('/api/settings/weights', {
      method: 'PUT',
      body: JSON.stringify(weights),
    }),
};

