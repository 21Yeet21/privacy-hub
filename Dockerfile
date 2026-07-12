# --- Stage 1: Build Snowflake Client from source ---
FROM golang:1.24-alpine AS builder
RUN apk add --no-cache git
WORKDIR /app
RUN git clone https://gitlab.torproject.org/tpo/anti-censorship/pluggable-transports/snowflake.git .
RUN go build -o snowflake-client ./client

# --- Stage 2: Final Tor Image ---
FROM alpine:latest

# Install Tor, obfs4proxy, su-exec, and CA certificates
RUN apk add --no-cache tor obfs4proxy su-exec ca-certificates

# Copy the compiled snowflake-client from the builder stage
COPY --from=builder /app/snowflake-client /usr/bin/snowflake-client
RUN chmod +x /usr/bin/snowflake-client

# Ensure the data directory exists
RUN mkdir -p /var/lib/tor

# Copy our custom entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Use the entrypoint script
CMD ["/entrypoint.sh"]
