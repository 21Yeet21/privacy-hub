#!/bin/sh
# Fix permissions for the mounted volume so the 'tor' user can access it
chown -R tor:tor /var/lib/tor

# Drop privileges to the 'tor' user and start Tor
exec su-exec tor tor -f /etc/tor/torrc
