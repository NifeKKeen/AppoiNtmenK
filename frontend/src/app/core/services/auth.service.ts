import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap, BehaviorSubject } from 'rxjs';
import { API_URL } from '../config';

export interface LoginResponse {
  access: string;
  refresh: string;
}

export interface RegisterPayload {
  username: string;
  email: string;
  password: string;
  become_specialist?: boolean;
  specialist_role?: string;
  specialist_description?: string;
  specialist_icon?: string;
}

export interface UpgradeSpecialistPayload {
  specialist_role: string;
  specialist_description: string;
  specialist_icon?: string;
}

export interface SpecialistProfile {
  id: number;
  name: string;
  slug: string;
  role: string;
  description: string;
  color: string;
  icon: string;
  avatar_url: string;
  time_slots: string[];
  is_active: boolean;
}

export interface UserProfile {
  id: number;
  username: string;
  email: string;
  is_specialist: boolean;
  specialist_profile: SpecialistProfile | null;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly API = API_URL;
  private loggedIn$ = new BehaviorSubject<boolean>(this.hasToken());

  constructor(private http: HttpClient) {}

  get isLoggedIn$(): Observable<boolean> {
    return this.loggedIn$.asObservable();
  }

  register(payload: RegisterPayload): Observable<any> {
    return this.http.post(`${this.API}/register/`, payload);
  }

  getProfile(): Observable<UserProfile> {
    return this.http.get<UserProfile>(`${this.API}/profile/`);
  }

  upgradeToSpecialist(payload: UpgradeSpecialistPayload): Observable<UserProfile> {
    return this.http.post<UserProfile>(`${this.API}/profile/upgrade-specialist/`, payload);
  }

  login(username: string, password: string): Observable<LoginResponse> {
    return this.http
      .post<LoginResponse>(`${this.API}/token/`, { username, password })
      .pipe(
        tap((res) => {
          localStorage.setItem('access_token', res.access);
          localStorage.setItem('refresh_token', res.refresh);
          this.loggedIn$.next(true);
        })
      );
  }

  logout(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    this.loggedIn$.next(false);
  }

  getToken(): string | null {
    return localStorage.getItem('access_token');
  }

  hasToken(): boolean {
    return !!localStorage.getItem('access_token');
  }

  getUsername(): string | null {
    const token = this.getToken();
    if (!token) return null;
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return payload.username || payload.user_id || null;
    } catch {
      return null;
    }
  }
}
