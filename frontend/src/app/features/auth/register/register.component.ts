import { Component } from '@angular/core';

import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { AuthService, RegisterPayload } from '../../../core/services/auth.service';

@Component({
    selector: 'app-register',
    standalone: true,
    imports: [FormsModule, RouterModule],
    templateUrl: './register.component.html',
    styleUrl: './register.component.css'
})
export class RegisterComponent {
  username = '';
  email = '';
  password = '';
  becomeSpecialist = false;
  specialistRole = '';
  specialistDescription = '';
  specialistIcon = '🧠';

  readonly specialistRoles = [
    'Math Whisperer',
    'Tourist-Consultant',
    'Code Debugger',
  ];

  readonly iconOptions = ['🧠', '💻', '🧭', '🧮', '🧑‍🏫', '🛟'];

  error = '';
  success = '';
  loading = false;

  constructor(private auth: AuthService, private router: Router) {}

  onSpecialistToggle() {
    if (!this.becomeSpecialist) {
      this.specialistRole = '';
      this.specialistDescription = '';
      this.specialistIcon = '🧠';
    }
  }

  onRegister() {
    if (
      this.becomeSpecialist &&
      (!this.specialistRole || !this.specialistDescription.trim())
    ) {
      this.error = 'Для регистрации специалиста нужно заполнить роль и описание.';
      return;
    }

    this.loading = true;
    this.error = '';
    this.success = '';

    const payload: RegisterPayload = {
      username: this.username,
      email: this.email,
      password: this.password,
      become_specialist: this.becomeSpecialist,
    };

    if (this.becomeSpecialist) {
      payload.specialist_role = this.specialistRole;
      payload.specialist_description = this.specialistDescription.trim();
      payload.specialist_icon = this.specialistIcon;
    }

    this.auth.register(payload).subscribe({
      next: () => {
        this.success = this.becomeSpecialist
          ? 'Specialist profile created! Redirecting to login...'
          : 'Account created! Redirecting to login...';
        setTimeout(() => this.router.navigate(['/login']), 1500);
      },
      error: (err) => {
        this.loading = false;
        const errors = err.error;
        if (typeof errors === 'object') {
          this.error = Object.values(errors).flat().join(' ');
        } else {
          this.error = 'Registration failed. Please try again.';
        }
      },
    });
  }
}
