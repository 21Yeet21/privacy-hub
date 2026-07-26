# The 5 Per-Device Routing Modes

## 1. `no_ads` Mode (Pi-hole DNS)
```mermaid
flowchart LR
    A[Phone 10.8.0.x] --> B(wg0 Interface)
    B --> C[iptables Mangle<br>Mark 100]
    C --> D[Routing Table 100<br>Default via LAN GW]
    D --> E[Pi-hole DNS :53]
    E --> F((Internet via ISP))
```

## 2. `vpn_only` Mode (Direct Internet + Cloudflare DNS)
```mermaid
flowchart LR
    A[Phone 10.8.0.x] --> B(wg0 Interface)
    B --> C[iptables Mangle<br>Mark 101]
    C --> D[Routing Table 101<br>Default via LAN GW]
    D --> E[iptables NAT<br>DNS to 1.1.1.1]
    E --> F((Internet via ISP))
```
*Note: This mode bypasses Pi-hole to prevent ad-blocking from interfering with strict app connections.*

## 3. `full_privacy` Mode (Split-Trust: WARP Payload + Unbound DNS)
```mermaid
flowchart TD
    A[📱 Device 10.8.0.x] --> B{Traffic Type?}
    
    B -->|UDP Port 53| C[iptables NAT PREROUTING]
    B -->|TCP / HTTPS| D[iptables Mangle<br>fwmark 102]
    
    C -->|Hijacked at Kernel| E[Unbound DNS :5333]
    E --> F[Forced through WARP<br>Talks directly to Root Servers]
    F -.->|Returns IP to Device| A
    
    D --> G[Routing Table 102]
    G --> H[warp0 Interface]
    H --> I[Cloudflare Edge<br>Sees encrypted payload<br>Is blind to DNS]
    I --> J((Internet))
```
> [!tip] The "Zero-Trust" DNS Architecture
> Notice that DNS (UDP 53) goes straight to Unbound. Unbound then talks directly to root nameservers, but its outbound traffic is forced through the WARP tunnel via `fwmark 102` on the `OUTPUT` chain. This ensures Cloudflare only sees encrypted IPs, while your ISP sees nothing but the WARP tunnel.

## 4. `fully_hidden` Mode (Transparent Tor)
```mermaid
flowchart TD
    A[Phone 10.8.0.x] --> B(wg0 Interface)
    B --> C[iptables Mangle<br>Mark 103]
    B --> D{iptables NAT<br>Is dst 10.8.0.1?}
    D -->|Yes| E[RETURN<br>Go to Hub Web UI]
    D -->|No| F[Redirect TCP to :9040<br>Redirect UDP:53 to :9053]
    C --> G[Routing Table 103<br>Blackhole to 127.0.0.1]
    F --> H[Tor TransPort :9040]
    F --> I[Tor DNSPort :9053]
    H --> J[obfs4 Bridge]
    I --> J
    J --> K((Tor Exit Node))
```
> [!tip] The 10.8.0.1 Exception
> Notice the `RETURN` rule for `10.8.0.1` in Fully Hidden mode. Without this, when a remote user tries to load the Privacy Hub web UI, the NAT rule would try to redirect port 5000 traffic to Tor, breaking the dashboard. This rule ensures local management traffic bypasses the Tor proxy.

## 5. `panic` Mode (Virtual Air-Gap)
```mermaid
flowchart LR
    A[Phone 10.8.0.x] --> B(wg0 Interface)
    B --> C[iptables Mangle<br>Mark 104]
    C --> D[Routing Table 104<br>Default via 127.0.0.1]
    D --> E[Local Loopback<br>No listener found]
    E --> F((🗑️ Packet Dropped))
```

### Technical Execution
When triggered, the system performs a surgical, stateful teardown and rebuild of the device's network routing at Linux kernel speed:
*   **The Purge:** `clear_device_rules()` surgically deletes *only* the `iptables` mangle marks, `ip rule` entries, and NAT redirects associated with that specific IP. Other devices are unaffected.
*   **The Blackhole:** The engine applies a new mangle mark (`--set-mark 104`) to all traffic from the target IP, binding it to Linux Routing Table 104. This table routes *everything* to the local loopback interface (`127.0.0.1`). Because no services are listening for this specific traffic on the loopback, the kernel silently drops the packets.
