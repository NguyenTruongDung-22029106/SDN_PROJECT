FROM golang:1.21-bullseye AS builder
WORKDIR /src

# Copy your chaincode source into the image. When building from repo root the path is
# relative to the build context (repo root), so reference the full path under the repo.
COPY blockchain/chaincode/ ./chaincode/
WORKDIR /src/chaincode

# Build the chaincode server binary. Expect package main or a suitable entrypoint that
# starts a chaincode server (external mode). You may need to adapt build flags for your code.
RUN CGO_ENABLED=0 go build -o /bin/trustlog_server ./...

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /app

# Copy built binary
COPY --from=builder /bin/trustlog_server /app/trustlog_server

# Copy start script (path relative to build context)
COPY blockchain/cc-external/start_chaincode.sh /app/start_chaincode.sh
RUN chmod +x /app/start_chaincode.sh

# Default: expect certs mounted at /etc/hyperledger/fabric
VOLUME ["/etc/hyperledger/fabric"]

EXPOSE 9999

ENTRYPOINT ["/app/start_chaincode.sh"]
