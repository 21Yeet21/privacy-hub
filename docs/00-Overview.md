# Privacy Hub: Overview

## Project Evolution
**Phase 1** established a global "Clean Slate" routing engine where the *entire* WireGuard network switched modes at once. 

**Phase 2 & 3** evolved this into a **Multi-User, Zero-Trust Appliance**. We moved to per-device policy routing, added Web UI authentication, implemented Tor circuit rotation, achieved total auto-recovery on boot via `systemd`, securely bridged the network to the outside world using DDNS, and engineered a kernel-level "Panic Mode" for instant data leak prevention.

**Phase 4 (Final)** introduced the "Self-Healing" firewall architecture. To prevent `wg-easy` container restarts from silently dropping base `FORWARD` rules and breaking the network, the backend now verifies and repairs base routing rules on every mode switch. It also integrated Unbound DNS over WARP to achieve true zero-trust DNS resolution.

## Quick Links
- [Core Infrastructure](01-Networking-Architecture.md)
- [Traffic Flow Diagrams](02-Routing-Modes.md)
- [Remote Access & Zero-Trust](04-Remote-Access-ZTNA.md)
- [Engineering Decisions](06-Engineering-Decisions.md)
- [War Stories & Bugfixes](07-War-Stories-And-Bugfixes.md)
