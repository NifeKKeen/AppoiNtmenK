import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { SpecialistService, Specialist } from '../../core/services/specialist.service';

@Component({
    selector: 'app-landing',
    standalone: true,
    imports: [CommonModule, RouterModule],
    templateUrl: './landing.component.html',
    styleUrl: './landing.component.css'
})
export class LandingComponent {
  specialists: Specialist[] = [];

  constructor(private specialistService: SpecialistService) {}

  ngOnInit() {
    this.specialistService.getAll().subscribe((data) => {
      this.specialists = data;
    });
  }
}
