set -e

echo "Creating demo containers for DockerTUI screenshots..."

# Pull images
docker pull nginx:alpine
docker pull redis:alpine
docker pull postgres:15
docker pull busybox:latest
docker pull alpine:latest

# NGINX
docker run -d --name demo_nginx -p 8080:80 nginx:alpine

# Redis
docker run -d --name demo_redis redis:alpine

# Postgres
docker run -d --name demo_postgres -e POSTGRES_PASSWORD=pass postgres:15

# BusyBox (sleep so it stays running)
docker run -d --name demo_busybox busybox sleep 3600

# Alpine (sleep to remain running)
docker run -d --name demo_alpine alpine sleep 3600

# docker compose
cat > docker-compose.yaml <<'EOF'
version: "3.9"

services:
  web:
    image: nginx:alpine
    container_name: compose_web
    ports:
      - "9090:80"

  db:
    image: postgres:15
    container_name: compose_db
    environment:
      POSTGRES_PASSWORD: pass

  cache:
    image: redis:alpine
    container_name: compose_cache

  worker:
    image: alpine
    container_name: compose_worker
    command: ["sh", "-c", "while true; do echo 'worker running'; sleep 5; done"]
EOF
docker compose -f docker-compose.yaml -p my-docker-compose up -d
rm docker-compose.yaml

echo
echo "Containers created:"
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}"
echo
echo "You can now take your DockerTUI screenshots."
