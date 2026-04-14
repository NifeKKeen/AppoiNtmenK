import { Component, OnInit, OnDestroy, ViewChild, ElementRef, AfterViewChecked } from '@angular/core';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { ChatService, ChatMessage } from '../../core/services/chat.service';
import { AuthService, UserProfile } from '../../core/services/auth.service';

@Component({
    selector: 'app-chat',
    standalone: true,
    imports: [FormsModule, RouterModule],
    templateUrl: './chat.component.html',
    styleUrl: './chat.component.css',
})
export class ChatComponent implements OnInit, OnDestroy, AfterViewChecked {
  @ViewChild('messagesContainer') private messagesContainer!: ElementRef<HTMLDivElement>;

  appointmentId = 0;
  messages: ChatMessage[] = [];
  newMessage = '';
  loading = true;
  sending = false;
  error = '';
  profile: UserProfile | null = null;

  private pollTimer: ReturnType<typeof setInterval> | null = null;
  private lastMessageId = 0;
  private shouldScroll = false;

  constructor(
    private route: ActivatedRoute,
    private chatService: ChatService,
    private authService: AuthService,
  ) {}

  ngOnInit(): void {
    this.appointmentId = Number(this.route.snapshot.paramMap.get('appointmentId')) || 0;

    this.authService.getProfile().subscribe({
      next: (profile) => {
        this.profile = profile;
      },
    });

    this.loadMessages(true);

    // Poll for new messages every 5 seconds
    this.pollTimer = setInterval(() => {
      this.pollNewMessages();
    }, 5000);
  }

  ngOnDestroy(): void {
    if (this.pollTimer) {
      clearInterval(this.pollTimer);
      this.pollTimer = null;
    }
  }

  ngAfterViewChecked(): void {
    if (this.shouldScroll) {
      this.scrollToBottom();
      this.shouldScroll = false;
    }
  }

  loadMessages(initial = false): void {
    if (initial) {
      this.loading = true;
    }
    this.chatService.getMessages(this.appointmentId).subscribe({
      next: (msgs) => {
        this.messages = msgs;
        if (msgs.length > 0) {
          this.lastMessageId = msgs[msgs.length - 1].id;
        }
        this.loading = false;
        this.shouldScroll = true;
      },
      error: (err) => {
        this.loading = false;
        this.error = err?.error?.detail || 'Failed to load messages.';
      },
    });
  }

  pollNewMessages(): void {
    if (!this.appointmentId) return;

    this.chatService.getMessages(this.appointmentId, this.lastMessageId).subscribe({
      next: (newMsgs) => {
        if (newMsgs.length > 0) {
          this.messages = [...this.messages, ...newMsgs];
          this.lastMessageId = newMsgs[newMsgs.length - 1].id;
          this.shouldScroll = true;
        }
      },
    });
  }

  send(): void {
    const body = this.newMessage.trim();
    if (!body || this.sending) return;

    this.sending = true;
    this.chatService.sendMessage(this.appointmentId, body).subscribe({
      next: (msg) => {
        this.messages = [...this.messages, msg];
        this.lastMessageId = msg.id;
        this.newMessage = '';
        this.sending = false;
        this.shouldScroll = true;
      },
      error: () => {
        this.sending = false;
      },
    });
  }

  isOwnMessage(msg: ChatMessage): boolean {
    return this.profile != null && msg.sender === this.profile.id;
  }

  formatTime(iso: string): string {
    const d = new Date(iso);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  formatDate(iso: string): string {
    const d = new Date(iso);
    const today = new Date();
    if (d.toDateString() === today.toDateString()) return 'Today';
    const yesterday = new Date(today);
    yesterday.setDate(today.getDate() - 1);
    if (d.toDateString() === yesterday.toDateString()) return 'Yesterday';
    return d.toLocaleDateString([], { month: 'short', day: 'numeric' });
  }

  onKeydown(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.send();
    }
  }

  private scrollToBottom(): void {
    try {
      const el = this.messagesContainer?.nativeElement;
      if (el) {
        el.scrollTop = el.scrollHeight;
      }
    } catch (_) {}
  }
}
