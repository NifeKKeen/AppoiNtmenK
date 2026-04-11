import { Component, OnInit } from '@angular/core';

import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
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
  availableSlots: string[] = [];
  minDate = '';
  loading = false;
  error = '';

  constructor(
    private fb: FormBuilder,
    private route: ActivatedRoute,
    private router: Router,
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

      // Pre-fill specialist from query param
      const specId = this.route.snapshot.queryParamMap.get('specialist');
      if (specId) {
        this.bookingForm.patchValue({ specialist: +specId });
        this.onSpecialistChange();
      }
    });
  }

  onSpecialistChange() {
    const selectedId = +this.bookingForm.get('specialist')?.value;
    const spec = this.specialists.find((s) => s.id === selectedId);
    this.availableSlots = spec ? spec.time_slots : [];
    // Reset time slot when specialist changes
    this.bookingForm.patchValue({ time_slot: '' });
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
        this.router.navigate(['/dashboard']);
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
}
