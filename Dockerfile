FROM alpine:3.18

RUN apk add --no-cache dnscrypt-proxy

# Copy the dnscrypt-proxy configuration file
COPY dnscrypt-proxy.toml /etc/dnscrypt-proxy/dnscrypt-proxy.toml

# Expose the DNS port
EXPOSE 53/udp
EXPOSE 53/tcp

# Run dnscrypt-proxy
CMD ["dnscrypt-proxy", "-config", "/etc/dnscrypt-proxy/dnscrypt-proxy.toml"]