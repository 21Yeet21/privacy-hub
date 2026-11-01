# Privacy Hub

![Status](https://img.shields.io/badge/Status-Homelab_Project-blue)
![Architecture](https://img.shields.io/badge/Architecture-Policy_Routing-blue)
![Tech](https://img.shields.io/badge/Tech-WireGuard_%7C_Tor_%7C_iptables-orange)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

A self-hosted Linux network gateway for managing per-device traffic routing over WireGuard.

Privacy Hub combines policy-based routing, Pi-hole, Cloudflare WARP, Tor, and Unbound to provide different network-routing profiles for connected devices through a Flask web dashboard.

> **Project status:** Personal homelab project. Configuration and security properties are environment-dependent. This project does not guarantee anonymity, leak prevention, or production-grade network isolation.

---

## Architecture

[![Privacy Hub Architecture](assets/hero_isometric.png)](assets/hero_isometric.png)

[![Privacy Hub Dashboard](assets/ui_dashboard.png)](assets/ui_dashboard.png)

## Features

- **Per-device routing:** Assign different routing profiles to individual WireGuard clients.
- **Pi-hole integration:** DNS-based filtering for supported clients.
- **Cloudflare WARP:** Route selected device traffic through the WARP interface.
- **Unbound integration:** Redirect selected DNS queries to a local Unbound resolver.
- **Tor transparent proxy:** Redirect TCP traffic and UDP DNS queries from selected devices to Tor.
- **Panic mode:** Apply a loopback-based routing policy to isolate a selected device from normal forwarding.
- **Boot recovery:** Restore saved device routing policies during controller initialization.
- **Firewall repair:** Reapply required base firewall rules during initialization and device-mode application.
- **Web dashboard:** Manage device profiles through an authenticated Flask interface.

## Routing Modes

The controller assigns dedicated Linux routing tables to five profiles.

| Profile | Table | Main behavior |
|---|---:|---|
| `no_ads` | 100 | LAN gateway routing with intended Pi-hole DNS integration |
| `vpn_only` | 101 | LAN gateway routing with Cloudflare DNS redirection |
| `full_privacy` | 102 | WARP routing with DNS redirection to local Unbound |
| `fully_hidden` | 103 | TCP transparent proxy through Tor and UDP DNS redirection to Tor |
| `panic` | 104 | Loopback-based routing policy |

### Per-device Routing Engine

[![Routing Engine](assets/routing_engine_2d.png)](assets/routing_engine_2d.png)

### Split-Trust DNS

[![Split-Trust DNS](assets/split_trust_dns.png)](assets/split_trust_dns.png)

### Panic Mode

[![Panic Mode](assets/panic_mode_blackhole.png)](assets/panic_mode_blackhole.png)

### Boot Recovery

[![Boot Recovery](assets/boot_recovery.png)](assets/boot_recovery.png)

> **Important technical notes**
>
> - `vpn_only` uses the configured LAN gateway. It is not a separate commercial VPN tunnel.
> - `full_privacy` routes selected traffic through WARP and redirects DNS queries to local Unbound.
> - `fully_hidden` redirects TCP traffic and UDP DNS queries to Tor. It does not transparently proxy every possible protocol.
> - `panic` uses a loopback-based routing table, not a literal kernel blackhole or physical air gap.
> - WARP and Tor have different privacy properties. Neither guarantees complete anonymity.

## Technology Stack

- Linux policy routing (`ip rule`, `ip route`)
- iptables-compatible Netfilter rules
- WireGuard / wg-easy
- Cloudflare WARP
- Tor
- Pi-hole
- Unbound
- Docker Compose
- Python and Flask
- systemd

## Repository Structure

```text
privacy-hub/
├── assets/                 # Architecture and UI illustrations
├── data/                   # Persistent service data
├── docs/                   # Technical documentation
├── hub_controller.py       # Flask controller and routing engine
├── docker-compose.yml      # Container services
├── Dockerfile              # Custom Tor image build
├── entrypoint.sh           # Tor container startup
├── torrc                   # Tor configuration
├── requirements.txt        # Python dependencies
├── .env.example            # Configuration template
└── README.md
```

## Deployment

This repository reflects a specific homelab deployment. The checked-in Compose configuration uses host networking, contains host-specific network values, and builds a custom Tor image.

It is not a universal one-command installer.

### Prerequisites

- Linux server with Docker and Docker Compose
- Python 3 and a virtual environment
- WireGuard interface (`wg0`)
- Cloudflare WARP WireGuard interface (`warp0`)
- Pi-hole and Unbound configuration
- Required routing and firewall tools
- Appropriate systemd service configuration

### Configuration

Review `.env.example` and `docker-compose.yml` before deployment.

The example environment file is not currently connected to every Compose service. Some settings are hardcoded in Compose, and the Tor control-password configuration requires separate attention.

Do not copy the current configuration to another host without adapting interface names, addresses, firewall rules, service dependencies, and credentials.

### Starting an Existing Deployment

```bash
docker compose up -d
sudo systemctl start warp.service
sudo systemctl start privacy-hub.service
```

These commands assume the required containers, systemd units, WireGuard interfaces, and configuration files already exist.

### Dashboard Access

Observed deployment addresses:

- **Local:** `http://192.168.1.13:5000`
- **Remote over WireGuard:** `http://10.8.0.1:5000`

Replace these addresses with the values appropriate to your deployment.

## Security Considerations

- Use strong, unique credentials and protect `.env` and persistent data directories.
- Do not expose the Flask dashboard directly to the public internet.
- Review IPv4 and IPv6 forwarding rules independently.
- Test routing behavior and DNS handling after configuration changes.
- Tor does not make every application or protocol anonymous.
- WARP changes the network path but does not provide Tor-style anonymity.
- DNS-based ad blocking cannot reliably remove every application-layer advertisement.
- Routing policies and firewall rules should be independently audited before being relied upon as security boundaries.

This project is intended for experimentation, learning, and personal network management. It has not been independently security-audited.

## Documentation

| Document | Subject |
|---|---|
| [Overview](docs/00-Overview.md) | Project evolution and architecture |
| [Networking Architecture](docs/01-Networking-Architecture.md) | Firewall and policy routing |
| [Routing Modes](docs/02-Routing-Modes.md) | Per-device traffic profiles |
| [Authentication and UI](docs/03-Authentication-And-UI.md) | Dashboard and authentication |
| [Remote Access](docs/04-Remote-Access-ZTNA.md) | WireGuard and remote access |
| [Systemd and Boot Recovery](docs/05-Systemd-And-Boot-Recovery.md) | Startup and recovery |
| [Engineering Decisions](docs/06-Engineering-Decisions.md) | Implementation decisions |
| [War Stories and Bugfixes](docs/07-War-Stories-And-Bugfixes.md) | Troubleshooting history |
| [Knowledge Base](docs/08-Knowledge-Base.md) | DNS and network behavior |
| [How to Run](docs/09-How-To-Run.md) | Deployment notes |

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
