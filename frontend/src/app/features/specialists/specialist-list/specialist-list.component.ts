import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { SpecialistService, Specialist } from '../../../core/services/specialist.service';

@Component({
    selector: 'app-specialist-list',
    standalone: true,
    imports: [CommonModule, RouterModule],
    templateUrl: './specialist-list.component.html',
    styleUrl: './specialist-list.component.css'
})
export class SpecialistListComponent implements OnInit {
  specialists: Specialist[] = [];

  constructor(private specialistService: SpecialistService) {}

  ngOnInit() {
    this.specialistService.getAll().subscribe((data) => {
      this.specialists = data;
    });
  }

  getSlotCount(spec: Specialist): number {
    if (spec.weekly_availability) {
      return Object.values(spec.weekly_availability)
        .reduce((sum, slots) => sum + (slots ? slots.length : 0), 0);
    }
    return spec.time_slots ? spec.time_slots.length : 0;
  }
}
