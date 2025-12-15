Step: produce or copy TLS cert/key for the chaincode service.

1) If you have a Fabric CA:
   - Register an identity for the chaincode service (e.g. 'chaincode-trustlog') with the CA.
   - Use fabric-ca-client to enroll that identity and get the cert+key.
   - Copy signcert and key to client_pem.crt / client_pem.key and the CA cert into cacerts/.

2) If you already have cert/key (signed by the same CA the peers trust), copy them here.

Important: the TLS cert must be signed by the CA that the peer trusts (or be in the peer's cacerts).
