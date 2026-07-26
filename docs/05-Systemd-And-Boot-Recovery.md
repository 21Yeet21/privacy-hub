# Systemd & Boot Recovery

To ensure the Privacy Hub survives a power outage without manual intervention, the infrastructure is managed entirely by `systemd`.

## Service: `warp.service`
Handles the Cloudflare WARP interface.
*   **Type:** `oneshot` with `RemainAfterExit=yes`
*   **Critical Fix:** Uses `ExecStartPre=/usr/bin/wg-quick down warp0` to aggressively tear down any ghost interfaces before starting, preventing "already exists" collisions on reboot.

## Service: `privacy-hub.service`
Handles the Python Flask application.
*   **Type:** `simple`
*   **Resilience:** `Restart=always` and `RestartSec=5`. If the Python app crashes, systemd automatically restarts it in 5 seconds.
*   **Dependencies:** `After=warp.service docker.service` to ensure networking is ready before the app tries to apply routes.

## State Recovery Logic
Because `systemd` handles the daemons, the Python script only needs to handle routing state. On boot, `init_base_layer()` sets up the base routing tables, then iterates through `devices.json` and re-applies the exact `fwmark` and NAT rules that were active before the power went out.

## The Watchdog Cron Job
A background script runs every 5 minutes to check if the internet is reachable. If the internet drops (e.g., during a power cut), it waits patiently. When the internet returns, it automatically restarts the WARP interface, Tor, and the Flask app to ensure clean handshakes are re-established.
