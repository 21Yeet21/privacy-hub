# Knowledge Base & Network Theory

## The "Unstoppable" YouTube Ads
*   **The Problem:** Pi-hole logs showed 32,000+ queries from the iPhone, yet YouTube ads still played.
*   **The Cause:** This is an application-layer limitation, not a network flaw. YouTube serves video ads from the exact same domain as the content (`googlevideo.com`). Blocking it at DNS breaks the video player entirely.
*   **The Fix:** Accepted the architectural limit of DNS-level blocking. Browser-level extensions (AdGuard for Safari) are required for DOM-manipulation ads.

## How the "Split-Trust" Architecture Works
In `full_privacy` mode, the Netfilter stack processes packets in a specific order: NAT PREROUTING happens *before* the routing decision. 
1. An `fwmark` of 102 is applied to all packets from the device.
2. In the NAT PREROUTING chain, a port-specific `REDIRECT` rule intercepts *only* UDP port 53 and forces it to Unbound's port locally.
3. When the routing engine evaluates the packet, it sees mark 102, ignores the main routing table, uses Table 102, and pushes the untouched TCP payload out the WARP interface. 
By manipulating the packet destination at the NAT layer before the routing layer, we successfully split DNS and web traffic to two entirely different engines.

## The IPv6 Leak
*   **The Problem:** `dnsleaktest.com` showed the real Tunisian ISP IP alongside the Cloudflare WARP IP.
*   **The Cause:** Our `iptables` rules only handled IPv4. The phone was using IPv6 to connect to the internet, bypassing the WARP tunnel entirely.
*   **The Fix:** Added a strict IPv6 Kill Switch using `ip6tables`, dropping all IPv6 forwarding from the WireGuard interface.
