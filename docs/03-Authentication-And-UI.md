# Authentication \& User Interface

## Flask Session Authentication
The Web UI is protected by Flask session-based authentication. Unauthenticated requests to `/` are redirected to `/login`. API endpoints (`/api/...`) return `401 Unauthorized` if a valid session cookie is not present, preventing external tools from interacting with the routing engine.

## UI Structure
The frontend utilizes a single-page application approach via Vanilla JavaScript. Device states are fetched via `/api/devices` and dynamically injected into the DOM as "Device Cards". Each card contains mode-selection buttons that trigger API POST requests to `/api/devices/<ip>/mode`.

## Security Posture
- Passwords are never stored in plain text in the Python code; they are hashed using SHA-256.
- Secrets (Flask Key, Admin Password, Tor Password) are externalized into a `.env` file to prevent repository leaks.

## System Refresh & Tor Control
- **Refresh System Button:** Triggers a full backend restart of WARP, Docker containers, and the base routing layer. This acts as a "Panic/Reset" button for system administrators if networking gets into a bad state.
- **New Identity Button:** Connects to the Tor Control Port (9051) via raw Python sockets and sends the `SIGNAL NEWNYM` command, forcing Tor to build fresh circuits for all `fully_hidden` users.
.