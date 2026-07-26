# Core Infrastructure: The Multi-User Shift

The hardest architectural shift in Phase 2 was moving from *global* `iptables` flushes (which broke `wg-easy` in Phase 1) to **surgical, per-device routing**.

> [!warning] Why Global Flushing Failed at Scale
> In Phase 1, switching modes meant flushing `FORWARD` and `POSTROUTING` chains and restarting Docker. This was fine for one user, but catastrophic for multiple users. If User A changed modes, User B's connection would briefly drop while `wg-easy` restarted.
> 
> **The Fix:** We abandoned chain flushing. Now, rules are applied *exclusively* to source IPs (`-s 10.8.0.x`). The `FORWARD` and base `POSTROUTING` rules are set once at boot and verified on every mode switch.

## The "Self-Healing" Firewall
`wg-easy` periodically restarts itself in the background. When it does, it wipes the host's `FORWARD` chain. 

To combat this, the `repair_base_firewall()` function runs every time a user clicks a button in the UI. It checks if the base `ACCEPT` rules for `wg0` and the `MASQUERADE` rules for the internet interfaces exist. If they are missing, it instantly rebuilds them before applying the user's specific mode rules.

## Boot Sequence
*(See [05-Systemd-And-Boot-Recovery.md](05-Systemd-And-Boot-Recovery.md) for the full systemd breakdown)*

1.  **`warp.service` (Systemd):** Brings `warp0` up cleanly using `ExecStartPre=/usr/bin/wg-quick down warp0` to prevent "already exists" collisions.
2.  **`privacy-hub.service` (Systemd):** Starts the Flask app inside the Python virtual environment.
3.  **`init_base_layer()`:** Creates the 5 dedicated routing tables (100-104), sets up masquerading, enables IP forwarding, and forces host DNS through WARP.
4.  **State Recovery:** The Python script reads `devices.json` and silently re-applies `iptables` marks and NAT redirects for every device that was active before the reboot.

