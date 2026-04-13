import { Component, OnInit } from '@angular/core';

import { Router, RouterModule, NavigationEnd } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';
import { SpecialistService, Specialist } from '../../core/services/specialist.service';
import { filter } from 'rxjs';

@Component({
    selector: 'app-navbar',
    standalone: true,
    imports: [RouterModule],
    templateUrl: './navbar.component.html',
    styleUrl: './navbar.component.css'
})
export class NavbarComponent implements OnInit {
  showNavbar = false;
  specialists: Specialist[] = [];
  isSpecialist = false;

  private hiddenRoutes = ['/', '/login', '/register'];

  constructor(
    private router: Router,
    private authService: AuthService,
    private specialistService: SpecialistService
  ) {}

  ngOnInit() {
    // Track route changes to show/hide navbar
    this.router.events
      .pipe(filter((e) => e instanceof NavigationEnd))
      .subscribe((e: any) => {
        this.showNavbar =
          !this.hiddenRoutes.includes(e.urlAfterRedirects) &&
          this.authService.hasToken();

        if (this.showNavbar && this.authService.hasToken()) {
          this.loadProfileRole();
        }
      });

    // Check immediately on init
    this.showNavbar =
      !this.hiddenRoutes.includes(this.router.url) &&
      this.authService.hasToken();

    // Load specialists for nav links (only if logged in)
    if (this.authService.hasToken()) {
      this.specialistService.getAll().subscribe((data) => {
        this.specialists = data;
      });
      this.loadProfileRole();
    }

    // Reload specialists when login state changes
    this.authService.isLoggedIn$.subscribe((loggedIn) => {
      if (loggedIn && this.specialists.length === 0) {
        this.specialistService.getAll().subscribe((data) => {
          this.specialists = data;
        });
        this.loadProfileRole();
      }

      if (!loggedIn) {
        this.isSpecialist = false;
      }
    });
  }

  loadProfileRole() {
    this.authService.getProfile().subscribe({
      next: (profile) => {
        this.isSpecialist = profile.is_specialist;
      },
      error: () => {
        this.isSpecialist = false;
      },
    });
  }

  logout() {
    this.authService.logout();
    this.router.navigate(['/login']);
  }
}
