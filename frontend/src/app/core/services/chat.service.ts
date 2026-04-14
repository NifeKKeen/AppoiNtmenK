import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { API_URL } from '../config';

export interface ChatMessage {
  id: number;
  appointment: number;
  sender: number;
  sender_username: string;
  sender_role: 'USER' | 'SPECIALIST';
  body: string;
  created_at: string;
}

@Injectable({ providedIn: 'root' })
export class ChatService {
  private readonly API = API_URL;

  constructor(private http: HttpClient) {}

  getMessages(appointmentId: number, afterId?: number): Observable<ChatMessage[]> {
    const params: Record<string, string> = {};
    if (afterId != null) {
      params['after'] = String(afterId);
    }
    return this.http.get<ChatMessage[]>(
      `${this.API}/appointments/${appointmentId}/messages/`,
      { params },
    );
  }

  sendMessage(appointmentId: number, body: string): Observable<ChatMessage> {
    return this.http.post<ChatMessage>(
      `${this.API}/appointments/${appointmentId}/messages/`,
      { body },
    );
  }
}
