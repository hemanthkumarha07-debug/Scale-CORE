# SCALE.Core — Production Deployment & Operations Guide
**Product:** Supply Chain Analytics & Logistics Engine (SCALE.Core)  
**Target Environment:** On-Premise Enterprise Linux (Ubuntu 22.04 LTS / Debian 12 / RHEL 9)  
**Local Development:** Windows 11 / Linux / macOS  
**Lead DevOps & Infrastructure Engineer:** Hemanth Kumar H A  
**Document Status:** Production Operational Runbook  

---

## 1. System Requirements & Architecture Topology

### 1.1 Minimum Hardware Specifications (Local On-Premise Server)
- **CPU:** 8 Cores (x86_64 or ARM64)
- **RAM:** 32 GB ECC DDR4/DDR5 (16 GB reserved for OS/Django/PostgreSQL/Redis, 16 GB for Ollama Llama 3.2 + TensorFlow)
- **Storage:** 500 GB NVMe SSD (PCIe Gen4) with automated backup volume
- **GPU (Optional/Recommended):** NVIDIA RTX 3060 12GB or higher (for accelerated LSTM training and Ollama inference)

### 1.2 Deployment Topology
```
                     +---------------------------------------+
                     |         Local Network Clients         |
                     +-------------------+-------------------+
                                         │ HTTPS (Port 443)
                                         ▼
                     +---------------------------------------+
                     |           Nginx Reverse Proxy         |
                     |  - SSL Termination                    |
                     |  - Static / Media Asset Serving       |
                     |  - Security Headers & Rate Limits     |
                     +-------------------+-------------------+
                                         │ UNIX Socket / HTTP
                                         ▼
                     +---------------------------------------+
                     |         Gunicorn WSGI Server          |
                     |         (SCALE.Core Django 5)         |
                     +---------+-------------------+---------+
                               │                   │
                Database Query │                   │ Task Enqueue
                               ▼                   ▼
                     +-------------------+   +-------------------+
                     |   PostgreSQL 16   |   |      Redis 7      |
                     | (Audit & Storage) |   |  (Message Broker) |
                     +-------------------+   +---------+---------+
                                                       │
                                        Task Execution │
                                                       ▼
+---------------------+                      +-------------------+
|     Ollama Daemon   |◄─────────────────────┤   Celery Worker   |
| (Llama 3.2 Local AI)|  HTTP (127.0.0.1)    |  & Celery Beat    |
+---------------------+                      +-------------------+
```

---

## 2. Linux Systemd Service Unit Files

### 2.1 Web Application: `/etc/systemd/system/scale-gunicorn.service`
```ini
[Unit]
Description=SCALE.Core Gunicorn Application Server
After=network.target postgresql.service redis-server.service
Requires=postgresql.service redis-server.service

[Service]
Type=notify
User=scale
Group=scale
WorkingDirectory=/opt/scale-core
EnvironmentFile=/opt/scale-core/.env
ExecStart=/opt/scale-core/venv/bin/gunicorn \
    --workers 5 \
    --threads 2 \
    --bind 127.0.0.1:8000 \
    --timeout 120 \
    --access-logfile /var/log/scale/gunicorn.access.log \
    --error-logfile /var/log/scale/gunicorn.error.log \
    scale_core.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=30
PrivateTmp=true
Restart=always
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

### 2.2 Celery Task Worker: `/etc/systemd/system/scale-celery-worker.service`
```ini
[Unit]
Description=SCALE.Core Celery Background Worker
After=network.target redis-server.service scale-gunicorn.service
Requires=redis-server.service

[Service]
Type=simple
User=scale
Group=scale
WorkingDirectory=/opt/scale-core
EnvironmentFile=/opt/scale-core/.env
ExecStart=/opt/scale-core/venv/bin/celery \
    -A scale_core worker \
    --loglevel=INFO \
    --concurrency=4 \
    --logfile=/var/log/scale/celery-worker.log
Restart=always
RestartSec=10s

[Install]
WantedBy=multi-user.target
```

### 2.3 Celery Beat Scheduler: `/etc/systemd/system/scale-celery-beat.service`
```ini
[Unit]
Description=SCALE.Core Celery Beat Periodic Scheduler
After=network.target scale-celery-worker.service
Requires=scale-celery-worker.service

[Service]
Type=simple
User=scale
Group=scale
WorkingDirectory=/opt/scale-core
EnvironmentFile=/opt/scale-core/.env
ExecStart=/opt/scale-core/venv/bin/celery \
    -A scale_core beat \
    --loglevel=INFO \
    --scheduler django_celery_beat.schedulers:DatabaseScheduler \
    --logfile=/var/log/scale/celery-beat.log
Restart=always
RestartSec=10s

[Install]
WantedBy=multi-user.target
```

---

## 3. Nginx Reverse Proxy Configuration

Create `/etc/nginx/sites-available/scale-core.conf`:
```nginx
upstream scale_backend {
    server 127.0.0.1:8000 fail_timeout=0;
}

server {
    listen 80;
    server_name scale.internal.corp;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name scale.internal.corp;

    ssl_certificate /etc/ssl/certs/scale_core.crt;
    ssl_certificate_key /etc/ssl/private/scale_core.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Enterprise Security Headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;

    client_max_body_size 25M;

    # Static Assets
    location /static/ {
        alias /opt/scale-core/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    # Application Proxy
    location / {
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Host $http_host;
        proxy_redirect off;
        proxy_pass http://scale_backend;
    }
}
```

---

## 4. Automated Backup and Disaster Recovery

### 4.1 Daily Backup Script (`/opt/scale-core/scripts/backup_database.sh`)
```bash
#!/bin/bash
set -euo pipefail
BACKUP_DIR="/var/backups/scale_core"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DB_NAME="scale_core_prod"
DB_USER="scale_db_user"

mkdir -p "$BACKUP_DIR"

echo "Starting SCALE.Core automated backup: $TIMESTAMP"
pg_dump -U "$DB_USER" -F c -b -v -f "$BACKUP_DIR/db_${DB_NAME}_${TIMESTAMP}.dump" "$DB_NAME"

# Snapshot trained model weights
tar -czf "$BACKUP_DIR/models_${TIMESTAMP}.tar.gz" -C /opt/scale-core models_store/

# Retention: Delete backups older than 30 days
find "$BACKUP_DIR" -type f -mtime +30 -delete

echo "Backup completed successfully."
```

### 4.2 Disaster Recovery Procedure
1. Provision target Linux server with prerequisites (PostgreSQL 16, Redis, Python 3.11).
2. Restore database: `pg_restore -U scale_db_user -d scale_core_prod -v /var/backups/scale_core/db_*.dump`
3. Extract model weights: `tar -xzf /var/backups/scale_core/models_*.tar.gz -C /opt/scale-core/`
4. Run migrations: `python manage.py migrate`
5. Verify cryptographic audit chain integrity: `python manage.py verify_audit_integrity`
6. Start systemd services: `systemctl start scale-gunicorn scale-celery-worker scale-celery-beat`
