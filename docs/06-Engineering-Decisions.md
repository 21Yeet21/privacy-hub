# Architecture & Engineering Decisions

## Decision 1: The Tor "Silent Banner" Bypass
**Context:** Integrating Tor’s Control Port for circuit rotation.
**The Problem:** Python's standard `socket.recv(1024)` is a blocking I/O call. Tor's control port is supposed to send a `250` banner immediately upon connection. However, due to Docker's `host` networking implementation and kernel TCP windowing, the banner was delayed. Python hung until the 5-second timeout.
**Options Considered:**
1. Increase socket timeout (Band-aid, slows down UI).
2. Use asynchronous Python (`asyncio`) (Over-engineering for one feature).
3. Fire payload immediately.
**Decision:** We deleted the `s.recv(1024)` line entirely. We now fire the `AUTHENTICATE` payload immediately upon connecting, mimicking the behavior of raw `netcat`.
**Consequences:** Perfectly reliable Tor control without rewriting the app architecture.

## Decision 2: Unbound DNS over WARP
**Context:** Hiding DNS metadata from Cloudflare WARP in `full_privacy` mode.
**Options Considered:**
1. Route DNS through Pi-hole -> Cloudflare DoH. (Cloudflare sees both payload and DNS).
2. Route DNS through Tor. (Slow, causes CAPTCHAs).
3. Kernel-level NAT redirect to local Unbound, forced out WARP via `fwmark`.
**Decision:** Option 3.
**Consequences:** Achieved complete DNS/WARP decorrelation. Unbound talks directly to root servers, but its outbound traffic is encrypted inside the WARP tunnel. Cloudflare only sees encrypted TCP payloads, not DNS requests.
