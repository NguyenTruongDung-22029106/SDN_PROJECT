# Production Deployment Guide

 **WARNING**: This project is designed for research and education. Production deployment requires additional security hardening.

## Production Considerations

### 1. Security Hardening

#### Fabric Network
```bash
# Use production-grade network configuration
# NOT test-network

# Generate proper certificates
fabric-ca-client enroll ...

# Use hardware security modules (HSM) for key storage
# Implement proper access control
# Enable TLS for all communications
# Use real Certificate Authorities
```

#### SDN Controller
```python
# Implement authentication for controller API
# Use encrypted communication (TLS/SSL)
# Rate limiting for API endpoints
# Input validation and sanitization
# Secure credential storage (not hardcoded)
```

#### Network Security
```bash
# Isolate management network
# Firewall rules for controller
# VPN for remote access
# Network segmentation
```

### 2. High Availability

#### Controller HA
```
Option 1: Active-Passive
     
 Controller1  Controller2 
  (Active)         (Standby)   
     
       
   Keepalived/VRRP

Option 2: Active-Active
     
 Controller1  Controller2 
  (Active)          (Active)   
     
                         
    Load Balancer
```

Implementation:
```bash
# Install keepalived
sudo apt install keepalived

# Configure VRRP
# /etc/keepalived/keepalived.conf
vrrp_instance VI_1 {
    state MASTER
    interface eth0
    virtual_router_id 51
    priority 100
    virtual_ipaddress {
        192.168.1.100
    }
}
```

#### Blockchain HA
```bash
# Multi-organization setup
# 3+ ordering nodes (Raft consensus)
# Multiple peers per organization
# Distributed ledger storage
# Backup and disaster recovery
```

### 3. Scalability

#### Horizontal Scaling
```yaml
# docker-compose-prod.yml
version: '3.8'

services:
  controller:
    image: sdn-controller:latest
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
    
  blockchain-gateway:
    image: blockchain-gateway:latest
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '1'
          memory: 2G
```

#### Database for Logs
```bash
# Instead of CSV files, use database
# Options: PostgreSQL, MongoDB, InfluxDB

# PostgreSQL setup
sudo apt install postgresql
createdb sdn_logs

# Schema
CREATE TABLE flow_events (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP,
    switch_id VARCHAR(50),
    sfe FLOAT,
    ssip FLOAT,
    rfip FLOAT,
    prediction INTEGER
);
```

### 4. Monitoring & Observability

#### Prometheus + Grafana
```bash
# Install Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.40.0/prometheus-2.40.0.linux-amd64.tar.gz
tar xvf prometheus-*.tar.gz
cd prometheus-*

# Configure prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'ryu-controller'
    static_configs:
      - targets: ['localhost:8080']
  
  - job_name: 'blockchain-gateway'
    static_configs:
      - targets: ['localhost:3001']
```

#### Grafana Dashboard
```bash
# Install Grafana
sudo apt-get install -y software-properties-common
sudo add-apt-repository "deb https://packages.grafana.com/oss/deb stable main"
sudo apt-get update
sudo apt-get install grafana

# Start Grafana
sudo systemctl start grafana-server
sudo systemctl enable grafana-server

# Access: http://localhost:3000
# Default: admin/admin
```

### 5. Backup & Recovery

#### Blockchain Backup
```bash
#!/bin/bash
# backup_blockchain.sh

BACKUP_DIR="/backup/blockchain"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup ledger
docker cp peer0.org1.example.com:/var/hyperledger/production \
  $BACKUP_DIR/ledger_$DATE

# Backup chaincode
docker cp peer0.org1.example.com:/var/hyperledger/production/chaincodes \
  $BACKUP_DIR/chaincode_$DATE

# Compress
tar -czf $BACKUP_DIR/blockchain_backup_$DATE.tar.gz \
  $BACKUP_DIR/ledger_$DATE $BACKUP_DIR/chaincode_$DATE

# Remove old backups (keep 30 days)
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

#### Controller State Backup
```bash
# Backup ML models
cp ryu_app/*.pkl /backup/models/

# Backup configuration
cp config.ini /backup/config/

# Backup flow rules (if persistent)
ovs-ofctl dump-flows s1 > /backup/flows/switch1_$(date +%Y%m%d).txt
```

### 6. Performance Tuning

#### Ryu Controller
```python
# config.ini
[controller]
# Increase flow cache
flow_cache_size = 10000

# Adjust monitoring interval
flow_monitor_interval = 5

# Thread pool size
worker_threads = 4

# Enable async operations
async_mode = true
```

#### Blockchain
```yaml
# core.yaml (Fabric peer)
peer:
  gossip:
    maxBlockCountToStore: 100
    maxPropagationBurstLatency: 10ms
    maxPropagationBurstSize: 10
    
  chaincode:
    executetimeout: 30s
    startuptimeout: 300s
```

#### Linux Kernel Tuning
```bash
# /etc/sysctl.conf
# Network performance
net.core.rmem_max = 134217728
net.core.wmem_max = 134217728
net.ipv4.tcp_rmem = 4096 87380 67108864
net.ipv4.tcp_wmem = 4096 65536 67108864

# Connection tracking
net.netfilter.nf_conntrack_max = 1000000
net.nf_conntrack_max = 1000000

# Apply
sudo sysctl -p
```

### 7. Logging & Auditing

#### Centralized Logging (ELK Stack)
```bash
# Install Elasticsearch
wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-8.5.0-amd64.deb
sudo dpkg -i elasticsearch-8.5.0-amd64.deb

# Install Logstash
wget https://artifacts.elastic.co/downloads/logstash/logstash-8.5.0-amd64.deb
sudo dpkg -i logstash-8.5.0-amd64.deb

# Install Kibana
wget https://artifacts.elastic.co/downloads/kibana/kibana-8.5.0-amd64.deb
sudo dpkg -i kibana-8.5.0-amd64.deb

# Configure Logstash
# /etc/logstash/conf.d/sdn.conf
input {
  file {
    path => "/var/log/ryu/*.log"
    type => "ryu"
  }
  file {
    path => "/var/log/blockchain/*.log"
    type => "blockchain"
  }
}

output {
  elasticsearch {
    hosts => ["localhost:9200"]
    index => "sdn-logs-%{+YYYY.MM.dd}"
  }
}
```

### 8. API Security

#### Rate Limiting
```python
# gateway_server.py
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["100 per hour"]
)

@app.route('/api/event/record', methods=['POST'])
@limiter.limit("10 per minute")
def record_event():
    # ...
```

#### Authentication
```python
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import check_password_hash

auth = HTTPBasicAuth()

users = {
    "admin": generate_password_hash("secure_password")
}

@auth.verify_password
def verify_password(username, password):
    if username in users:
        return check_password_hash(users.get(username), password)
    return False

@app.route('/api/event/record', methods=['POST'])
@auth.login_required
def record_event():
    # ...
```

### 9. Container Orchestration (Kubernetes)

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sdn-controller
spec:
  replicas: 3
  selector:
    matchLabels:
      app: sdn-controller
  template:
    metadata:
      labels:
        app: sdn-controller
    spec:
      containers:
      - name: controller
        image: sdn-controller:1.0
        ports:
        - containerPort: 6633
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: sdn-controller-service
spec:
  selector:
    app: sdn-controller
  ports:
  - protocol: TCP
    port: 6633
    targetPort: 6633
  type: LoadBalancer
```

### 10. Compliance & Regulations

#### GDPR Considerations
- Implement data retention policies
- Add user consent mechanisms
- Enable data deletion requests
- Audit logging

#### Security Standards
- ISO 27001 compliance
- PCI DSS (if handling payment data)
- SOC 2 certification
- Regular security audits

---

## Production Checklist

### Pre-Deployment
- [ ] Security audit completed
- [ ] Load testing performed
- [ ] Disaster recovery plan documented
- [ ] Monitoring configured
- [ ] Logging centralized
- [ ] Backups automated
- [ ] Access control implemented
- [ ] TLS/SSL certificates installed
- [ ] Firewall rules configured
- [ ] Network segmentation completed

### Deployment
- [ ] Blue-green deployment strategy
- [ ] Canary releases for updates
- [ ] Rollback plan prepared
- [ ] Health checks configured
- [ ] Performance baselines established
- [ ] Alerts configured
- [ ] Documentation updated
- [ ] Team training completed

### Post-Deployment
- [ ] Monitor metrics
- [ ] Review logs
- [ ] Test failover
- [ ] Verify backups
- [ ] Update runbooks
- [ ] Conduct post-mortem
- [ ] Optimize performance
- [ ] Plan capacity

---

## Support & Maintenance

### On-Call Procedures
1. Alert received
2. Check monitoring dashboard
3. Review recent logs
4. Identify root cause
5. Apply fix or rollback
6. Document incident
7. Update runbooks

### Maintenance Windows
- Schedule regular maintenance
- Communicate with stakeholders
- Plan for zero-downtime deployments
- Test rollback procedures

---

**Remember**: This guide provides a starting point. Each production environment has unique requirements. Always conduct thorough testing and security audits before deployment.
