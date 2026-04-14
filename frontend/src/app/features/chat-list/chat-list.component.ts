import { Component, OnInit } from '@angular/core';
import { RouterModule } from '@angular/router';
import { AppointmentService, Appointment } from '../../core/services/appointment.service';
import { AuthService, UserProfile } from '../../core/services/auth.service';
import { SpecialistService, SpecialistRequest } from '../../core/services/specialist.service';

@Component({
  selector: 'app-chat-list',
  standalone: true,
  imports: [RouterModule],
  templateUrl: './chat-list.component.html',
  styleUrl: './chat-list.component.css',
})
export class ChatListComponent implements OnInit {
  profile: UserProfile | null = null;
  appointments: Appointment[] = [];
  specialistRequests: SpecialistRequest[] = [];
  loading = true;

  constructor(
    private authService: AuthService,
    private appointmentService: AppointmentService,
    private specialistService: SpecialistService,
  ) {}

  ngOnInit(): void {
    this.authService.getProfile().subscribe({
      next: (profile) => {
        this.profile = profile;
        this.loadAppointments();
        if (profile.is_specialist) {
          this.loadSpecialistRequests();
        }
      },
      error: () => {
        this.loading = false;
      },
    });
  }

  private loadAppointments(): void {
    this.appointmentService.getMyAppointments().subscribe({
      next: (appts) => {
        this.appointments = appts;
        this.loading = false;
      },
      error: () => {
        this.loading = false;
      },
    });
  }

  private loadSpecialistRequests(): void {
    this.specialistService.getIncomingRequests().subscribe({
      next: (requests) => {
        this.specialistRequests = requests;
      },
    });
  }

  formatDate(dateStr: string): string {
    const d = new Date(dateStr + 'T00:00:00');
    return d.toLocaleDateString([], { month: 'short', day: 'numeric' });
  }
}
