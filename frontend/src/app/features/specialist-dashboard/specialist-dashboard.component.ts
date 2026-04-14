import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormArray, FormBuilder, FormControl, FormGroup, ReactiveFormsModule } from '@angular/forms';
import { ActivatedRoute, RouterModule } from '@angular/router';

import { AuthService, UserProfile } from '../../core/services/auth.service';
import {
  SpecialistRequest,
  SpecialistService,
} from '../../core/services/specialist.service';

interface DayColumn {
  key: string;
  label: string;
}

@Component({
  selector: 'app-specialist-dashboard',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterModule],
  templateUrl: './specialist-dashboard.component.html',
  styleUrl: './specialist-dashboard.component.css',
})
export class SpecialistDashboardComponent implements OnInit {
  profile: UserProfile | null = null;
  profileLoading = true;

  readonly days: DayColumn[] = [
    { key: 'mon', label: 'Mon' },
    { key: 'tue', label: 'Tue' },
    { key: 'wed', label: 'Wed' },
    { key: 'thu', label: 'Thu' },
    { key: 'fri', label: 'Fri' },
    { key: 'sat', label: 'Sat' },
    { key: 'sun', label: 'Sun' },
  ];

  readonly timeSlots = this.buildTimeSlots('09:00', '21:00', 30);

  availabilityForm: FormGroup = this.fb.group({
    grid: this.fb.array([]),
  });

  availabilityLoading = true;
  availabilitySaving = false;
  availabilityMessage = '';
  availabilityError = '';

  requests: SpecialistRequest[] = [];
  requestsLoading = true;
  requestsError = '';
  requestActionMessage = '';

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
    private specialistService: SpecialistService,
    private route: ActivatedRoute,
  ) {}

  ngOnInit(): void {
    this.initGrid();
    this.loadProfile();
  }

  get gridRows(): FormArray {
    return this.availabilityForm.get('grid') as FormArray;
  }

  getRow(dayIndex: number): FormArray {
    return this.gridRows.at(dayIndex) as FormArray;
  }

  toggleCell(dayIndex: number, slotIndex: number): void {
    const control = this.getRow(dayIndex).at(slotIndex) as FormControl<boolean>;
    control.setValue(!control.value);
  }

  isActive(dayIndex: number, slotIndex: number): boolean {
    const control = this.getRow(dayIndex).at(slotIndex) as FormControl<boolean>;
    return !!control.value;
  }

  clearAll(): void {
    this.days.forEach((_, dayIdx) => {
      this.timeSlots.forEach((__, slotIdx) => {
        const control = this.getRow(dayIdx).at(slotIdx) as FormControl<boolean>;
        control.setValue(false);
      });
    });
  }

  copyFirstDayToWeek(): void {
    const sourceRow = this.getRow(0);
    this.days.forEach((_, dayIdx) => {
      if (dayIdx === 0) {
        return;
      }
      this.timeSlots.forEach((__, slotIdx) => {
        const source = sourceRow.at(slotIdx) as FormControl<boolean>;
        const target = this.getRow(dayIdx).at(slotIdx) as FormControl<boolean>;
        target.setValue(!!source.value);
      });
    });
  }

  saveAvailability(): void {
    this.availabilitySaving = true;
    this.availabilityMessage = '';
    this.availabilityError = '';

    this.specialistService
      .saveAvailability({ weekly_availability: this.collectAvailabilityMap() })
      .subscribe({
        next: () => {
          this.availabilitySaving = false;
          this.availabilityMessage = 'Availability updated successfully.';
        },
        error: (err) => {
          this.availabilitySaving = false;
          this.availabilityError = this.extractError(err, 'Failed to save availability.');
        },
      });
  }

  acceptRequest(requestId: number): void {
    this.requestActionMessage = '';
    this.specialistService.acceptRequest(requestId).subscribe({
      next: (response) => {
        this.requests = this.requests.map((item) =>
          item.id === requestId ? response.appointment : item,
        );

        if (response.google_calendar_synced) {
          this.requestActionMessage = 'Request accepted and synced to Google Calendar.';
        } else if (response.google_calendar_error) {
          this.requestActionMessage = `Request accepted, but calendar sync failed: ${response.google_calendar_error}`;
        } else {
          this.requestActionMessage = 'Request accepted.';
        }
      },
      error: (err) => {
        this.requestsError = this.extractError(err, 'Failed to accept request.');
      },
    });
  }

  rejectRequest(requestId: number): void {
    this.requestActionMessage = '';
    this.specialistService.rejectRequest(requestId).subscribe({
      next: (updated) => {
        this.requests = this.requests.map((item) =>
          item.id === requestId ? updated : item,
        );
        this.requestActionMessage = 'Request rejected.';
      },
      error: (err) => {
        this.requestsError = this.extractError(err, 'Failed to reject request.');
      },
    });
  }

  private initGrid(): void {
    const rows = this.fb.array(
      this.days.map(() =>
        this.fb.array(
          this.timeSlots.map(() => this.fb.control(false, { nonNullable: true })),
        ),
      ),
    );

    this.availabilityForm.setControl('grid', rows);
  }

  private loadProfile(): void {
    this.profileLoading = true;
    this.authService.getProfile().subscribe({
      next: (profile) => {
        this.profile = profile;
        this.profileLoading = false;

        if (!profile.is_specialist) {
          this.availabilityLoading = false;
          this.requestsLoading = false;
          return;
        }

        this.loadAvailability();
        this.loadRequests();
      },
      error: () => {
        this.profileLoading = false;
        this.availabilityLoading = false;
        this.requestsLoading = false;
      },
    });
  }

  private loadAvailability(): void {
    this.availabilityLoading = true;
    this.specialistService.getAvailability().subscribe({
      next: (response) => {
        this.patchAvailability(response.weekly_availability || {});
        this.availabilityLoading = false;
      },
      error: (err) => {
        this.availabilityLoading = false;
        this.availabilityError = this.extractError(err, 'Failed to load availability.');
      },
    });
  }

  private loadRequests(): void {
    this.requestsLoading = true;
    this.requestsError = '';
    this.specialistService.getIncomingRequests().subscribe({
      next: (requests) => {
        this.requests = requests;
        this.requestsLoading = false;
      },
      error: (err) => {
        this.requestsLoading = false;
        this.requestsError = this.extractError(err, 'Failed to load incoming requests.');
      },
    });
  }

  private patchAvailability(map: Record<string, string[]>): void {
    this.days.forEach((day, dayIdx) => {
      const selected = new Set(map[day.key] || []);
      this.timeSlots.forEach((slot, slotIdx) => {
        const control = this.getRow(dayIdx).at(slotIdx) as FormControl<boolean>;
        control.setValue(selected.has(slot));
      });
    });
  }

  private collectAvailabilityMap(): Record<string, string[]> {
    const payload: Record<string, string[]> = {};

    this.days.forEach((day, dayIdx) => {
      const selectedSlots: string[] = [];
      this.timeSlots.forEach((slot, slotIdx) => {
        const control = this.getRow(dayIdx).at(slotIdx) as FormControl<boolean>;
        if (control.value) {
          selectedSlots.push(slot);
        }
      });
      payload[day.key] = selectedSlots;
    });

    return payload;
  }

  private buildTimeSlots(start: string, end: string, stepMinutes: number): string[] {
    const result: string[] = [];
    const [startHour, startMinute] = start.split(':').map((v) => Number(v));
    const [endHour, endMinute] = end.split(':').map((v) => Number(v));

    let current = startHour * 60 + startMinute;
    const endTotal = endHour * 60 + endMinute;

    while (current < endTotal) {
      const h = Math.floor(current / 60)
        .toString()
        .padStart(2, '0');
      const m = (current % 60).toString().padStart(2, '0');
      result.push(`${h}:${m}`);
      current += stepMinutes;
    }

    return result;
  }

  private extractError(err: any, fallback: string): string {
    const payload = err?.error;
    if (typeof payload === 'string') {
      return payload;
    }
    if (payload?.detail) {
      return payload.detail;
    }
    if (typeof payload === 'object' && payload) {
      return Object.values(payload).flat().join(' ');
    }
    return fallback;
  }
}
