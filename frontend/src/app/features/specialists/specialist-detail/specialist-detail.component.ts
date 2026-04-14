import { Component, OnInit } from '@angular/core';

import { ActivatedRoute, RouterModule } from '@angular/router';
import { SpecialistService, Specialist } from '../../../core/services/specialist.service';

@Component({
    selector: 'app-specialist-detail',
    standalone: true,
    imports: [RouterModule],
    templateUrl: './specialist-detail.component.html',
    styleUrl: './specialist-detail.component.css'
})
export class SpecialistDetailComponent implements OnInit {
  specialist: Specialist | null = null;
  error = '';

  constructor(
    private route: ActivatedRoute,
    private specialistService: SpecialistService
  ) {}

  ngOnInit() {
    this.route.paramMap.subscribe((params) => {
      const slug = params.get('slug');
      if (slug) {
        this.specialist = null;
        this.error = '';
        this.specialistService.getBySlug(slug).subscribe({
          next: (data) => (this.specialist = data),
          error: () => (this.error = 'Specialist not found.'),
        });
      }
    });
  }

  getUniqueSlots(spec: Specialist): string[] {
    if (spec.weekly_availability) {
      const allSlots = Object.values(spec.weekly_availability).flat();
      return Array.from(new Set(allSlots)).sort();
    }
    return spec.time_slots || [];
  }
}
