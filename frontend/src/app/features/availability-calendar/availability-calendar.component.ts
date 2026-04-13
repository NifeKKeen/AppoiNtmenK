import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';

import {
  AvailabilityCalendarRow,
  Specialist,
  SpecialistService,
} from '../../core/services/specialist.service';

@Component({
  selector: 'app-availability-calendar',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './availability-calendar.component.html',
  styleUrl: './availability-calendar.component.css',
})
export class AvailabilityCalendarComponent implements OnInit {
  specialists: Specialist[] = [];
  rows: AvailabilityCalendarRow[] = [];

  startDate = '';
  days = 7;
  specialistSlug = '';
  timeFrom = '';
  timeTo = '';

  loading = true;
  error = '';

  constructor(private specialistService: SpecialistService) {}

  ngOnInit(): void {
    this.startDate = new Date().toISOString().split('T')[0];

    this.specialistService.getAll().subscribe({
      next: (specialists) => {
        this.specialists = specialists;
      },
    });

    this.loadCalendar();
  }

  applyFilters() {
    this.loadCalendar();
  }

  resetFilters() {
    this.startDate = new Date().toISOString().split('T')[0];
    this.days = 7;
    this.specialistSlug = '';
    this.timeFrom = '';
    this.timeTo = '';
    this.loadCalendar();
  }

  trackByRow(_: number, row: AvailabilityCalendarRow): string {
    return `${row.date}-${row.specialist.id}`;
  }

  get groupedByDate(): { date: string; entries: AvailabilityCalendarRow[] }[] {
    const map = new Map<string, AvailabilityCalendarRow[]>();

    for (const row of this.rows) {
      if (!map.has(row.date)) {
        map.set(row.date, []);
      }
      map.get(row.date)?.push(row);
    }

    return Array.from(map.entries()).map(([date, entries]) => ({ date, entries }));
  }

  private loadCalendar() {
    this.loading = true;
    this.error = '';

    this.specialistService
      .getAvailabilityCalendar({
        start_date: this.startDate,
        days: this.days,
        specialist_slug: this.specialistSlug || undefined,
        time_from: this.timeFrom || undefined,
        time_to: this.timeTo || undefined,
      })
      .subscribe({
        next: (response) => {
          this.rows = response.rows;
          this.loading = false;
        },
        error: (err) => {
          this.loading = false;
          const detail = err?.error?.detail;
          this.error = detail || 'Failed to load availability calendar.';
        },
      });
  }
}
