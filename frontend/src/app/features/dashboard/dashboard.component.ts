import { Component, OnInit } from '@angular/core';

import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { AppointmentService, Appointment } from '../../core/services/appointment.service';
import { AuthService, UserProfile } from '../../core/services/auth.service';
import { StatusBadgeComponent } from '../../shared/status-badge/status-badge.component';

@Component({
    selector: 'app-dashboard',
    standalone: true,
    imports: [RouterModule, StatusBadgeComponent, FormsModule],
    templateUrl: './dashboard.component.html',
    styleUrl: './dashboard.component.css'
})
export class DashboardComponent implements OnInit {
  appointments: Appointment[] = [];
  loading = true;

  profile: UserProfile | null = null;
  profileLoading = true;

  showUpgradeForm = false;
  upgradeRole = '';
  upgradeDescription = '';
  upgradeIcon = '🧠';
  upgradeLoading = false;
  upgradeError = '';
  upgradeSuccess = '';

  readonly specialistRoles = [
    'Math Whisperer',
    'Tourist-Consultant',
    'Code Debugger',
  ];

  readonly iconOptions = ['🧠', '💻', '🧭', '🧮', '🧑‍🏫', '🛟'];

  constructor(
    private appointmentService: AppointmentService,
    private authService: AuthService,
  ) {}

  ngOnInit() {
    this.loadAppointments();
    this.loadProfile();
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

  loadProfile() {
    this.profileLoading = true;
    this.authService.getProfile().subscribe({
      next: (profile) => {
        this.profile = profile;
        this.profileLoading = false;
      },
      error: () => {
        this.profileLoading = false;
      },
    });
  }

  toggleUpgradeForm() {
    this.showUpgradeForm = !this.showUpgradeForm;
    this.upgradeError = '';
    this.upgradeSuccess = '';
  }

  submitUpgrade() {
    if (!this.upgradeRole || !this.upgradeDescription.trim()) {
      this.upgradeError = 'Заполни роль и описание, чтобы стать специалистом.';
      return;
    }

    this.upgradeLoading = true;
    this.upgradeError = '';
    this.upgradeSuccess = '';

    this.authService
      .upgradeToSpecialist({
        specialist_role: this.upgradeRole,
        specialist_description: this.upgradeDescription.trim(),
        specialist_icon: this.upgradeIcon,
      })
      .subscribe({
        next: (profile) => {
          this.profile = profile;
          this.upgradeLoading = false;
          this.upgradeSuccess = 'Профиль специалиста успешно создан.';
          this.showUpgradeForm = false;
        },
        error: (err) => {
          this.upgradeLoading = false;
          const errors = err?.error;
          if (typeof errors === 'object') {
            this.upgradeError = Object.values(errors).flat().join(' ');
            return;
          }
          this.upgradeError = 'Не удалось обновить профиль.';
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
