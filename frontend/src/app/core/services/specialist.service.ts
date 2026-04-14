import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { API_URL } from '../config';

export interface Specialist {
  id: number;
  name: string;
  slug: string;
  role: string;
  description: string;
  color: string;
  icon: string;
  avatar_url: string;
  time_slots: string[];
  weekly_availability?: Record<string, string[]>;
  is_active: boolean;
}

export interface SpecialistAvailability {
  weekly_availability: Record<string, string[]>;
}

export interface SpecialistRequest {
  id: number;
  student_name: string;
  student_email: string;
  date: string;
  time_slot: string;
  description: string;
  status: string;
  created_at: string;
}

export interface SpecialistAcceptResponse {
  appointment: SpecialistRequest;
  google_calendar_synced: boolean;
  google_calendar_error: string | null;
}

export interface GoogleCalendarConnectResponse {
  auth_url: string;
}

export interface GoogleCalendarStatus {
  connected: boolean;
  configured: boolean;
  missing_vars?: string[];
  oauth_redirect_uri?: string;
}

export interface SpecialistDayAvailability {
  date: string;
  specialist: {
    id: number;
    slug: string;
    name: string;
    icon: string;
    role: string;
  };
  all_slots: string[];
  booked_slots: string[];
  available_slots: string[];
}

export interface AvailabilityCalendarRow {
  date: string;
  weekday: string;
  specialist: {
    id: number;
    slug: string;
    name: string;
    icon: string;
    role: string;
  };
  available_slots: string[];
  available_count: number;
}

export interface AvailabilityCalendarResponse {
  filters: {
    start_date: string;
    days: number;
    specialist_slug: string | null;
    time_from: string | null;
    time_to: string | null;
  };
  rows: AvailabilityCalendarRow[];
}

@Injectable({ providedIn: 'root' })
export class SpecialistService {
  private readonly API = API_URL;

  constructor(private http: HttpClient) {}

  getAll(): Observable<Specialist[]> {
    return this.http.get<Specialist[]>(`${this.API}/specialists/`);
  }

  getBySlug(slug: string): Observable<Specialist> {
    return this.http.get<Specialist>(`${this.API}/specialists/${slug}/`);
  }

  getAvailability(): Observable<SpecialistAvailability> {
    return this.http.get<SpecialistAvailability>(`${this.API}/specialist/availability/`);
  }

  saveAvailability(payload: SpecialistAvailability): Observable<SpecialistAvailability> {
    return this.http.post<SpecialistAvailability>(`${this.API}/specialist/availability/`, payload);
  }

  getIncomingRequests(): Observable<SpecialistRequest[]> {
    return this.http.get<SpecialistRequest[]>(`${this.API}/specialist/requests/`);
  }

  acceptRequest(id: number): Observable<SpecialistAcceptResponse> {
    return this.http.post<SpecialistAcceptResponse>(`${this.API}/specialist/requests/${id}/accept/`, {});
  }

  rejectRequest(id: number): Observable<SpecialistRequest> {
    return this.http.post<SpecialistRequest>(`${this.API}/specialist/requests/${id}/reject/`, {});
  }

  getGoogleConnectUrl(): Observable<GoogleCalendarConnectResponse> {
    return this.http.get<GoogleCalendarConnectResponse>(`${this.API}/specialist/google/connect/`);
  }

  getGoogleStatus(): Observable<GoogleCalendarStatus> {
    return this.http.get<GoogleCalendarStatus>(`${this.API}/specialist/google/status/`);
  }

  disconnectGoogleCalendar(): Observable<{ connected: boolean }> {
    return this.http.post<{ connected: boolean }>(`${this.API}/specialist/google/disconnect/`, {});
  }

  getDailyAvailability(slug: string, date: string): Observable<SpecialistDayAvailability> {
    return this.http.get<SpecialistDayAvailability>(`${this.API}/specialists/${slug}/availability/`, {
      params: { date },
    });
  }

  getAvailabilityCalendar(filters: {
    start_date: string;
    days: number;
    specialist_slug?: string;
    time_from?: string;
    time_to?: string;
  }): Observable<AvailabilityCalendarResponse> {
    const params: Record<string, string> = {
      start_date: filters.start_date,
      days: String(filters.days),
    };

    if (filters.specialist_slug) {
      params['specialist_slug'] = filters.specialist_slug;
    }
    if (filters.time_from) {
      params['time_from'] = filters.time_from;
    }
    if (filters.time_to) {
      params['time_to'] = filters.time_to;
    }

    return this.http.get<AvailabilityCalendarResponse>(`${this.API}/calendar/availability/`, {
      params,
    });
  }
}
