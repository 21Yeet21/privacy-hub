# How To Run This Project

## Prerequisites
- Ubuntu/Debian Linux Server (Tested on Dell Inspiron Laptop)
- Docker & Docker Compose
- Python 3 + venv
- Cloudflare WARP configured (`warp0.conf` via `wgcf`)
- WireGuard configured (`wg0` via `wg-easy`)

## Environment Setup
1. Clone the repository.
2. Copy `.env.example` to `.env` and fill in your secure keys:
   ```bash
   FLASK_SECRET_KEY=<generate_via_python3_secrets_token_hex>
   ADMIN_PASSWORD=<your_dashboard_password>
   TOR_CONTROL_PASS=<your_tor_control_password>
   ```
3. Generate the Tor Hash and inject it into `torrc` (do not manually copy-paste).

## Boot Sequence
Start the infrastructure in order:
```bash
# 1. Start Docker Containers (Pi-hole, Tor, wg-easy, Unbound)
sudo docker compose up -d

# 2. Start Systemd Services (WARP, Privacy Hub)
sudo systemctl start warp.service
sudo systemctl start privacy-hub.service
```

## Accessing the Dashboard
- **Local:** `http://192.168.1.13:5000`
- **Remote:** Connect to WireGuard externally, then `http://10.8.0.1:5000`

## Troubleshooting
- **WARP won't start on boot:** Check `systemctl status warp.service`. Usually a ghost interface. The `ExecStartPre` directive handles this automatically.
- **Tor Control Port timed out:** Verify the hash in `torrc` is exactly 60 characters. If in doubt, re-run the generation command.
- **Phone loads pages but no ads are blocked:** Check if iCloud Private Relay is active on iOS; ensure Pi-hole is blocking it via `dns.specialDomains.iCloudPrivateRelay`.
- **Modes stop working after a few days:** Click the "Refresh System" button in the UI. This forces the self-healing firewall to rebuild the base rules.
