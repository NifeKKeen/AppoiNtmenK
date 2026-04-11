import { Component, OnInit } from '@angular/core';

import { RouterModule } from '@angular/router';
import { AppointmentService, Appointment } from '../../core/services/appointment.service';
import { StatusBadgeComponent } from '../../shared/status-badge/status-badge.component';

@Component({
    selector: 'app-dashboard',
    standalone: true,
    imports: [RouterModule, StatusBadgeComponent],
    templateUrl: './dashboard.component.html',
    styleUrl: './dashboard.component.css'
})
export class DashboardComponent implements OnInit {
  appointments: Appointment[] = [];
  loading = true;

  constructor(private appointmentService: AppointmentService) {}

  ngOnInit() {
    this.loadAppointments();
  }

  loadAppointments() {
    this.loading = true;
    this.appointmentService.getMyAppointments().subscribe({
      next: (data) => {
        this.appointments = data;
        this.loading = false;
      },
      error: () => {
        this.loading = false;
      },
    });
  }

  cancelAppointment(id: number) {
    if (confirm('Are you sure you want to cancel this SOS request?')) {
      this.appointmentService.delete(id).subscribe({
        next: () => {
          this.appointments = this.appointments.filter((a) => a.id !== id);
        },
      });
    }
  }
}
