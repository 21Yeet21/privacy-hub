# Remote Access & Zero-Trust Network Access (ZTNA)

Tunisia uses dynamic IPs. We solved remote access using a 100% free stack combined with strict segmentation to prevent the new attack surface from compromising the home network.

## The DDNS & Port Forward Stack
1.  **DuckDNS Cron:** Updates the public IP every 5 minutes via a `crontab` job on the server.
2.  **Router Port Forward:** UDP 51820 -> 192.168.1.13.
3.  **WireGuard `PersistentKeepalive = 25`:** Keeps the NAT state open on cellular networks.

## The Zero-Trust Firewall
When a phone connects via WireGuard using `AllowedIPs = 0.0.0.0/0`, *all* traffic hits the server, including attempts to reach the local home network (`192.168.1.x`).

To prevent a stolen phone from scanning the local network (e.g., attacking the router at `192.168.1.1`), we inserted a DROP rule at the very top of the `FORWARD` chain:
```bash
sudo iptables -I FORWARD -s 10.8.0.0/24 -d 192.168.1.0/24 -j DROP
```
Now, remote devices can only reach the internet (via their assigned mode) and the server's WireGuard IP (`10.8.0.1`) for the dashboard. The Web UI port (5000) is also explicitly blocked from the outside WAN, only allowing connections from the `10.8.0.0/24` subnet.
