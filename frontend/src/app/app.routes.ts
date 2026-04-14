import { Routes } from '@angular/router';
import { LandingComponent } from './features/landing/landing.component';
import { LoginComponent } from './features/auth/login/login.component';
import { RegisterComponent } from './features/auth/register/register.component';
import { SpecialistListComponent } from './features/specialists/specialist-list/specialist-list.component';
import { SpecialistDetailComponent } from './features/specialists/specialist-detail/specialist-detail.component';
import { BookingComponent } from './features/booking/booking.component';
import { DashboardComponent } from './features/dashboard/dashboard.component';
import { SpecialistDashboardComponent } from './features/specialist-dashboard/specialist-dashboard.component';
import { AvailabilityCalendarComponent } from './features/availability-calendar/availability-calendar.component';
import { ChatComponent } from './features/chat/chat.component';
import { authGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  { path: '', component: LandingComponent },
  { path: 'login', component: LoginComponent },
  { path: 'register', component: RegisterComponent },
  { path: 'specialists', component: SpecialistListComponent, canActivate: [authGuard] },
  { path: 'specialists/:slug', component: SpecialistDetailComponent, canActivate: [authGuard] },
  { path: 'book', component: BookingComponent, canActivate: [authGuard] },
  { path: 'calendar', component: AvailabilityCalendarComponent, canActivate: [authGuard] },
  { path: 'dashboard', component: DashboardComponent, canActivate: [authGuard] },
  { path: 'specialist/dashboard', component: SpecialistDashboardComponent, canActivate: [authGuard] },
  { path: 'chat/:appointmentId', component: ChatComponent, canActivate: [authGuard] },
  { path: '**', redirectTo: '' },
];
