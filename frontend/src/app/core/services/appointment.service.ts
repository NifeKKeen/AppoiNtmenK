import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Appointment {
  id: number;
  user: number;
  specialist: number;
  specialist_name: string;
  specialist_color: string;
  specialist_icon: string;
  date: string;
  time_slot: string;
  description: string;
  status: string;
  created_at: string;
}

export interface AppointmentPayload {
  specialist: number;
  date: string;
  time_slot: string;
  description: string;
}

@Injectable({ providedIn: 'root' })
export class AppointmentService {
  private readonly API = 'http://localhost:8000/api';

  constructor(private http: HttpClient) {}

  getMyAppointments(): Observable<Appointment[]> {
    return this.http.get<Appointment[]>(`${this.API}/appointments/`);
  }

  create(payload: AppointmentPayload): Observable<Appointment> {
    return this.http.post<Appointment>(`${this.API}/appointments/`, payload);
  }

  delete(id: number): Observable<void> {
    return this.http.delete<void>(`${this.API}/appointments/${id}/`);
  }
}
