# AppoiNtmenK - Project Documentation and Architecture

## 🛠 Technology Stack
- **Frontend (User Interface):** Angular (TypeScript) - a modern and powerful framework for building single-page applications (SPA).
- **Backend (Server Side):** Django (Python) + Django REST Framework - a framework for building robust APIs and server-side business logic.
- **Database:** SQLite3 (`db.sqlite3`) - a lightweight relational database (used by default in Django, an excellent choice for development and prototyping).

---

## 🗺 Project Map (Architecture)

The project is clearly divided into independent client and server components:

### 1. Backend (Server - `/backend/` Directory)
Handles data operations, security, request processing, and integrations.

- `manage.py` — main Django command-line utility (run server, migrations, create admins).
- `db.sqlite3` — the actual database file.
- **`appointmenk/`** — project core and configuration:
  - `settings.py` — global server settings (database, security, JWT tokens, CORS).
  - `urls.py` — root API router.
  - `asgi.py` / `wsgi.py` — interfaces for application deployment and support for asynchronous connections (e.g., for WebSockets).
- **`core/`** — main application with business logic:
  - `models.py` — database table definitions (User, SpecialistDetails, Appointment, ChatMessage, and Availability).
  - `views.py` — controllers (API Endpoints). Receive requests from the frontend, process them, and send responses.
  - `serializers.py` — "translator" between complex Python/database objects and JSON format that Angular understands.
  - `urls.py` — local routes for the core component (e.g., user and appointment routes).
  - `google_calendar.py` — integration module. Synchronizes appointments with the real Google Calendar.
  - `migrations/` — history of database structure changes (for creating and modifying tables).

### 2. Frontend (Client - `/frontend/` Directory)
Handles data display, interactivity, and logic on the user's browser side.

- `package.json` — list of JavaScript/TypeScript libraries and frontend dependencies.
- `angular.json` — Angular compiler configuration.
- **`src/app/`** — application source code:
  - **`core/`** — client core (system modules):
    - `services/` (`auth`, `appointment`, `chat`, etc.) — classes that make HTTP requests to the backend.
    - `guards/` (`auth.guard.ts`) — "route guards". Check if a user is authorized before allowing access to protected pages.
    - `interceptors/` (`auth.interceptor.ts`) — intercept all backend requests and automatically add security tokens (JWT).
  - **`features/`** — pages and their logic:
    - `auth/` — registration and login windows.
    - `booking/` & `availability-calendar/` — interface for viewing available slots and booking appointments with specialists.
    - `dashboard/` & `specialist-dashboard/` — personal accounts (one for clients, another for specialists).
    - `chat/` & `chat-list/` — messaging system between doctors/specialists and clients.
  - **`shared/`** — reusable interface components (like `navbar` - top menu, or `status-badge` - status badges).

---

## 💡 How Main Processes Work

1. **Appointment Booking**
   * **Frontend:** User opens the `booking.component.ts` component. A script triggers and sends an HTTP request to the API via `appointment.service.ts`.
   * **Backend:** Request reaches `urls.py`, then to a method in `views.py`. The method queries the database through models (`models.py`) and returns a list of available slots.
   * When the user selects a time, Frontend sends a `POST` request. Backend saves the appointment to SQLite and, if integration is enabled, sends the event through `google_calendar.py`.

2. **Security and Authorization**
   * When a user enters login and password in the Angular application, the request goes to the backend.
   * On success, the backend returns an encrypted key (Authorization Token).
   * Frontend stores the key. During all future actions (write to chat, open dashboard), the file `auth.interceptor.ts` automatically attaches this key to requests. Django sees the key and understands who is making the request.

3. **Messaging (Chats)**
   * The `chat.service.ts` service connects to the backend to retrieve message history (`ChatMessage`). The backend model stores references to the sender and recipient of messages and the message text itself.