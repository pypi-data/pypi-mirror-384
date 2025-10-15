# Multi-line content examples with proper formatting

# Create a YAML configuration file
resource "pyvider_file_content" "kubernetes_config" {
  filename = "/tmp/k8s-deployment.yaml"
  content = <<-EOF
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: my-app
      labels:
        app: my-app
        version: "1.0"
    spec:
      replicas: 3
      selector:
        matchLabels:
          app: my-app
      template:
        metadata:
          labels:
            app: my-app
        spec:
          containers:
          - name: app
            image: my-app:1.0
            ports:
            - containerPort: 8080
            env:
            - name: DATABASE_URL
              value: "postgresql://db:5432/myapp"
            - name: LOG_LEVEL
              value: "INFO"
  EOF
}

# Create a Docker Compose file
resource "pyvider_file_content" "docker_compose" {
  filename = "/tmp/docker-compose.yml"
  content = <<-EOF
    version: '3.8'

    services:
      web:
        image: nginx:alpine
        ports:
          - "80:80"
        volumes:
          - ./nginx.conf:/etc/nginx/nginx.conf:ro
        depends_on:
          - api

      api:
        build: .
        ports:
          - "8080:8080"
        environment:
          - DATABASE_URL=postgresql://postgres:password@db:5432/myapp
          - REDIS_URL=redis://redis:6379
        depends_on:
          - db
          - redis

      db:
        image: postgres:15-alpine
        environment:
          - POSTGRES_DB=myapp
          - POSTGRES_USER=postgres
          - POSTGRES_PASSWORD=password
        volumes:
          - postgres_data:/var/lib/postgresql/data

      redis:
        image: redis:7-alpine
        command: redis-server --appendonly yes
        volumes:
          - redis_data:/data

    volumes:
      postgres_data:
      redis_data:
  EOF
}

# Create a complex configuration with heredoc syntax
resource "pyvider_file_content" "nginx_config" {
  filename = "/tmp/nginx.conf"
  content = <<-NGINX
    user nginx;
    worker_processes auto;
    error_log /var/log/nginx/error.log warn;
    pid /var/run/nginx.pid;

    events {
        worker_connections 1024;
        use epoll;
        multi_accept on;
    }

    http {
        include /etc/nginx/mime.types;
        default_type application/octet-stream;

        # Logging
        log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                        '$status $body_bytes_sent "$http_referer" '
                        '"$http_user_agent" "$http_x_forwarded_for"';

        access_log /var/log/nginx/access.log main;

        # Performance
        sendfile on;
        tcp_nopush on;
        tcp_nodelay on;
        keepalive_timeout 65;
        types_hash_max_size 2048;

        # Compression
        gzip on;
        gzip_vary on;
        gzip_min_length 1024;
        gzip_types
            text/plain
            text/css
            text/xml
            text/javascript
            application/javascript
            application/xml+rss
            application/json;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";

        # Default server
        server {
            listen 80 default_server;
            listen [::]:80 default_server;
            server_name _;

            location / {
                proxy_pass http://api:8080;
                proxy_set_header Host $host;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto $scheme;
            }

            location /health {
                access_log off;
                return 200 "healthy\n";
                add_header Content-Type text/plain;
            }
        }
    }
  NGINX
}

output "multiline_files" {
  description = "Information about multi-line configuration files"
  value = {
    kubernetes = {
      path         = pyvider_file_content.kubernetes_config.filename
      content_hash = pyvider_file_content.kubernetes_config.content_hash
      content_size = length(pyvider_file_content.kubernetes_config.content)
    }
    docker_compose = {
      path         = pyvider_file_content.docker_compose.filename
      content_hash = pyvider_file_content.docker_compose.content_hash
      content_size = length(pyvider_file_content.docker_compose.content)
    }
    nginx = {
      path         = pyvider_file_content.nginx_config.filename
      content_hash = pyvider_file_content.nginx_config.content_hash
      content_size = length(pyvider_file_content.nginx_config.content)
    }
  }
}