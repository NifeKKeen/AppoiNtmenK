import { Component, OnInit } from '@angular/core';

import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { SpecialistService, Specialist } from '../../core/services/specialist.service';
import { AppointmentService } from '../../core/services/appointment.service';

@Component({
    selector: 'app-booking',
    standalone: true,
    imports: [ReactiveFormsModule, RouterModule],
    templateUrl: './booking.component.html',
    styleUrl: './booking.component.css'
})
export class BookingComponent implements OnInit {
  bookingForm!: FormGroup;
  specialists: Specialist[] = [];
  allSlots: string[] = [];
  availableSlots: string[] = [];
  bookedSlots: string[] = [];
  availabilityLoading = false;
  minDate = '';
  loading = false;
  error = '';
  submitted = false;
  calendarUrl = '';
  private initialTimeSlotFromQuery = '';

  constructor(
    private fb: FormBuilder,
    private route: ActivatedRoute,
    private specialistService: SpecialistService,
    private appointmentService: AppointmentService
  ) {}

  ngOnInit() {
    // Set min date to today
    const today = new Date();
    this.minDate = today.toISOString().split('T')[0];

    // Build the reactive form
    this.bookingForm = this.fb.group({
      specialist: ['', Validators.required],
      date: ['', Validators.required],
      time_slot: ['', Validators.required],
      description: ['', [Validators.required, Validators.minLength(10)]],
    });

    // Load specialists
    this.specialistService.getAll().subscribe((data: Specialist[]) => {
      this.specialists = data;
      this.applyQueryPrefill();
    });
  }

  onSpecialistChange() {
    this.refreshAvailableSlots(true);
  }

  onDateChange() {
    this.refreshAvailableSlots(true);
  }

  selectSlot(slot: string) {
    if (this.bookedSlots.includes(slot)) {
      return;
    }
    this.bookingForm.patchValue({ time_slot: slot });
  }

  onSubmit() {
    if (this.bookingForm.invalid) return;

    this.loading = true;
    this.error = '';

    const payload = {
      specialist: +this.bookingForm.value.specialist,
      date: this.bookingForm.value.date,
      time_slot: this.bookingForm.value.time_slot,
      description: this.bookingForm.value.description,
    };

    this.appointmentService.create(payload).subscribe({
      next: () => {
        const specialist = this.getSelectedSpecialist();
        const title = specialist
          ? `SOS Session: ${specialist.name}`
          : 'SOS Session';
        this.calendarUrl = this.buildGoogleCalendarLink(
          title,
          payload.description,
          payload.date,
          payload.time_slot,
        );
        this.loading = false;
        this.submitted = true;
      },
      error: (err: any) => {
        this.loading = false;
        if (err.error?.non_field_errors) {
          this.error = err.error.non_field_errors.join(' ');
        } else if (err.error?.detail) {
          this.error = err.error.detail;
        } else {
          this.error = 'Failed to submit request. The time slot may already be taken.';
        }
      },
    });
  }

  private refreshAvailableSlots(clearSelected: boolean) {
    const specialist = this.getSelectedSpecialist();
    if (!specialist) {
      this.allSlots = [];
      this.availableSlots = [];
      this.bookedSlots = [];
      if (clearSelected) {
        this.bookingForm.patchValue({ time_slot: '' });
      }
      return;
    }

    const dateValue = this.bookingForm.get('date')?.value;
    if (!dateValue) {
      const localSlots = this.getLocalWeeklySlots(specialist, this.minDate);
      this.allSlots = localSlots;
      this.availableSlots = localSlots;
      this.bookedSlots = [];
      if (clearSelected) {
        this.bookingForm.patchValue({ time_slot: '' });
      }
      return;
    }

    this.availabilityLoading = true;
    this.specialistService.getDailyAvailability(specialist.slug, dateValue).subscribe({
      next: (response) => {
        this.availabilityLoading = false;
        this.allSlots = response.all_slots;
        this.availableSlots = response.available_slots;
        this.bookedSlots = response.booked_slots;

        const selected = this.bookingForm.get('time_slot')?.value;
        if (clearSelected || (selected && !this.availableSlots.includes(selected))) {
          this.bookingForm.patchValue({ time_slot: '' });
        }

        if (
          this.initialTimeSlotFromQuery &&
          this.availableSlots.includes(this.initialTimeSlotFromQuery)
        ) {
          this.bookingForm.patchValue({ time_slot: this.initialTimeSlotFromQuery });
          this.initialTimeSlotFromQuery = '';
        }
      },
      error: () => {
        this.availabilityLoading = false;
        const localSlots = this.getLocalWeeklySlots(specialist, dateValue);
        this.allSlots = localSlots;
        this.availableSlots = localSlots;
        this.bookedSlots = [];
        if (clearSelected) {
          this.bookingForm.patchValue({ time_slot: '' });
        }
      },
    });
  }

  private applyQueryPrefill() {
    const params = this.route.snapshot.queryParamMap;
    const specId = params.get('specialist');
    const date = params.get('date');
    const timeSlot = params.get('time_slot');

    const patch: { specialist?: number; date?: string } = {};
    if (specId) {
      patch.specialist = +specId;
    }
    if (date) {
      patch.date = date;
    }

    if (Object.keys(patch).length > 0) {
      this.bookingForm.patchValue(patch);
    }

    if (timeSlot) {
      this.initialTimeSlotFromQuery = timeSlot;
    }

    if (specId || date) {
      this.refreshAvailableSlots(false);
    }
  }

  private getLocalWeeklySlots(specialist: Specialist, dateIso: string): string[] {
    const dayKey = this.getWeekdayKey(dateIso);
    const weeklyMap = specialist.weekly_availability || {};
    const daySlots = weeklyMap[dayKey] || [];
    return daySlots.length > 0 ? daySlots : specialist.time_slots || [];
  }

  private getSelectedSpecialist(): Specialist | undefined {
    const selectedId = +this.bookingForm.get('specialist')?.value;
    return this.specialists.find((s) => s.id === selectedId);
  }

  private getWeekdayKey(dateIso: string): string {
    const days = ['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat'];
    const date = new Date(`${dateIso}T00:00:00`);
    return days[date.getDay()];
  }

  private buildGoogleCalendarLink(
    title: string,
    details: string,
    dateIso: string,
    timeSlot: string,
  ): string {
    const start = new Date(`${dateIso}T${timeSlot}:00`);
    const end = new Date(start.getTime() + 30 * 60 * 1000);

    const format = (value: Date) => {
      const yyyy = value.getFullYear();
      const mm = String(value.getMonth() + 1).padStart(2, '0');
      const dd = String(value.getDate()).padStart(2, '0');
      const hh = String(value.getHours()).padStart(2, '0');
      const min = String(value.getMinutes()).padStart(2, '0');
      const ss = String(value.getSeconds()).padStart(2, '0');
      return `${yyyy}${mm}${dd}T${hh}${min}${ss}`;
    };

    const params = new URLSearchParams({
      action: 'TEMPLATE',
      text: title,
      details,
      location: 'AppointmenK',
      dates: `${format(start)}/${format(end)}`,
    });

    return `https://www.google.com/calendar/render?${params.toString()}`;
  }
}
