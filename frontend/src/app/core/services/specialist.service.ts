import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

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
  is_active: boolean;
}

@Injectable({ providedIn: 'root' })
export class SpecialistService {
  private readonly API = 'https://appointmenk.onrender.com/api';

  constructor(private http: HttpClient) {}

  getAll(): Observable<Specialist[]> {
    return this.http.get<Specialist[]>(`${this.API}/specialists/`);
  }

  getBySlug(slug: string): Observable<Specialist> {
    return this.http.get<Specialist>(`${this.API}/specialists/${slug}/`);
  }
}
