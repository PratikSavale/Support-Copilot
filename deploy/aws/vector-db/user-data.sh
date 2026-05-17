#!/bin/sh
set -eux

POSTGRES_USER="__POSTGRES_USER__"
POSTGRES_PASSWORD="__POSTGRES_PASSWORD__"
POSTGRES_DB="__POSTGRES_DB__"

apt-get update
apt-get install -y docker.io docker-compose curl ca-certificates

systemctl enable docker
systemctl start docker

if [ ! -f /swapfile ]; then
  fallocate -l 1G /swapfile || dd if=/dev/zero of=/swapfile bs=1M count=1024
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

mkdir -p /opt/vector-db
cat > /opt/vector-db/.env <<EOF
POSTGRES_USER=$POSTGRES_USER
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
POSTGRES_DB=$POSTGRES_DB
EOF

cat > /opt/vector-db/docker-compose.yml <<'EOF'
__DOCKER_COMPOSE__
EOF

cd /opt/vector-db
docker-compose up -d
docker-compose ps

for attempt in $(seq 1 40); do
  PG_READY=0
  CHROMA_READY=0
  docker exec pgvector pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" && PG_READY=1
  curl -fsS http://localhost:8000/api/v2/heartbeat >/tmp/chroma-heartbeat.json && CHROMA_READY=1
  if [ "$PG_READY" = "1" ] && [ "$CHROMA_READY" = "1" ]; then
    echo "Vector DB stack is ready."
    cat /tmp/chroma-heartbeat.json
    exit 0
  fi
  echo "Waiting for vector DB readiness... attempt ${attempt}/40"
  sleep 10
done

docker-compose ps
docker-compose logs --tail=200
echo "Vector DB stack did not become ready in time."
exit 1
