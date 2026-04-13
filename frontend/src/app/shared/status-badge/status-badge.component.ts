import { Component, input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
    selector: 'app-status-badge',
    standalone: true,
    imports: [CommonModule],
    templateUrl: './status-badge.component.html',
    styles: [`
    .appt-status {
      display: inline-block;
      padding: 0.2rem 0.6rem;
      border-radius: 6px;
      font-size: 0.75rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    .status-pending {
      background: hsla(45, 90%, 55%, 0.15);
      color: hsl(45, 90%, 60%);
    }

    .status-confirmed {
      background: hsla(160, 70%, 50%, 0.15);
      color: hsl(160, 70%, 55%);
    }

    .status-accepted {
      background: hsla(160, 70%, 50%, 0.15);
      color: hsl(160, 70%, 55%);
    }

    .status-rejected {
      background: hsla(0, 80%, 55%, 0.15);
      color: hsl(0, 80%, 65%);
    }

    .status-completed {
      background: hsla(270, 70%, 60%, 0.15);
      color: hsl(270, 70%, 65%);
    }
  `]
})
export class StatusBadgeComponent {
  // Using the new signal-based input() feature
  status = input.required<string>();
}
