#!/bin/bash

echo "[*] Activating FULLY HIDDEN mode (Tor Transparent Proxy + Kill Switch)..."

# 1. Intercept ALL TCP traffic from WireGuard (wg0) and send it to Tor's TransPort (9040)
sudo iptables -t nat -I PREROUTING 1 -i wg0 -p tcp -j REDIRECT --to-ports 9040

# 2. Intercept all DNS traffic from WireGuard (wg0) and send it to Pi-hole (53)
sudo iptables -t nat -I PREROUTING 1 -i wg0 -p udp --dport 53 -j REDIRECT --to-ports 53
sudo iptables -t nat -I PREROUTING 1 -i wg0 -p tcp --dport 53 -j REDIRECT --to-ports 53

# 3. KILL SWITCH: Drop anything that tries to bypass Tor
sudo iptables -I FORWARD 1 -i wg0 -j DROP

# 4. Tell Pi-hole to use Tor for upstream DNS (Using 127.0.0.1 now)
echo "server=127.0.0.1#9053" | sudo tee ./data/dnsmasq/99-tor-dns.conf
docker restart pihole

echo "[✓] Fully Hidden Mode ACTIVE. All WireGuard traffic is now forced through Tor."
echo "[✓] If Tor crashes, all internet access for WireGuard devices will immediately stop (Kill Switch)."
