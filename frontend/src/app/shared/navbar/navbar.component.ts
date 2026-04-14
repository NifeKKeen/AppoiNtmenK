import { Component, OnInit } from '@angular/core';

import { Router, RouterModule, NavigationEnd } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';
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
  isSpecialist = false;

  private hiddenRoutes = ['/', '/login', '/register'];

  constructor(
    private router: Router,
    private authService: AuthService,
  ) {}

  ngOnInit() {
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

    this.showNavbar =
      !this.hiddenRoutes.includes(this.router.url) &&
      this.authService.hasToken();

    if (this.authService.hasToken()) {
      this.loadProfileRole();
    }

    this.authService.isLoggedIn$.subscribe((loggedIn) => {
      if (loggedIn) {
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
