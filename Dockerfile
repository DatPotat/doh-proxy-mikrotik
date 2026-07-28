FROM alpine:3.22

RUN apk add --no-cache dnscrypt-proxy ca-certificates

CMD ["dnscrypt-proxy", "-config", "/config/dnscrypt-proxy.toml"]