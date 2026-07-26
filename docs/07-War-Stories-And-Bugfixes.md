# War Stories: Phase 2, 3 & 4 Challenges

## 1. The ISP DNS Hijacking (Snowflake vs. obfs4)
*   **The Problem:** Snowflake (WebRTC) failed to connect with `no such host`. Diagnostics revealed the Tunisian ISP was performing Transparent DNS Hijacking. Even when we hardcoded `1.1.1.1`, the ISP intercepted port 53 UDP packets and replied with `NXDOMAIN`.
*   **The Fix:** Switched to `obfs4` bridges. Because `obfs4` uses hardcoded IP addresses, it never queries the ISP's DNS. The ISP's hijacking was completely bypassed.

## 2. The Truncated Hash Sabotage
*   **The Problem:** The "Refresh Tor Circuits" button returned `515 Authentication failed`.
*   **The Cause:** When generating the Tor hash via `docker exec`, the terminal output was visually truncated when copy-pasted into `nano`. Tor silently rejected the incomplete hash.
*   **The Fix:** Used a `docker run --rm` command to generate the hash cleanly, ensuring 100% character accuracy.

## 3. The WARP Systemd Collision
*   **The Problem:** On first boot, `warp.service` failed with `wg-quick: 'warp0' already exists`.
*   **The Fix:** Added `ExecStartPre=/usr/bin/wg-quick down warp0` to the systemd unit. It aggressively tears down ghost interfaces before bringing it up.

## 4. The Asymmetric Routing Drop (`rp_filter`)
*   **The Problem:** WARP traffic leaked to the ISP. `tcpdump` showed packets hitting `warp0`, but never returning.
*   **The Cause:** Linux's Reverse Path Filtering (`rp_filter`) dropped return traffic coming *in* on `warp0` because it expected it to go *out* on `wg0`.
*   **The Fix:** Disabled `rp_filter` globally and on specific interfaces via `sysctl`.

## 5. The wg-easy Firewall Wipe
*   **The Problem:** `full_privacy` and `vpn_only` modes mysteriously stopped working after a few days.
*   **The Cause:** `wg-easy` periodically restarts in the background and wipes the host's `FORWARD` chain to rebuild its own rules, breaking our policy routing.
*   **The Fix:** Engineered the `repair_base_firewall()` self-healing function. It runs on every UI interaction to verify and restore the base rules if `wg-easy` wiped them.

## 6. The Laptop Sleep State
*   **The Problem:** The server (an Inspiron laptop) would drop off the network randomly.
*   **The Cause:** Ubuntu's power management was suspending the system or turning off the Wi-Fi card despite systemd targets.
*   **The Fix:** Masked all sleep/suspend targets, disabled Wi-Fi power saving (`wifi.powersave = 2`), and set the lid switch to `ignore`.