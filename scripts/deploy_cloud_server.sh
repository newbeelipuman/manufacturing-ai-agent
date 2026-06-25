#!/usr/bin/env bash
set -euo pipefail

PUBLIC_BASE_URL="${1:-}"
RESET_DEMO_VOLUME="${RESET_DEMO_VOLUME:-0}"

if [[ -z "${PUBLIC_BASE_URL}" ]]; then
  echo "Usage: bash scripts/deploy_cloud_server.sh http://<server-ip-or-domain>"
  exit 2
fi

if [[ ! -f ".env.production.example" ]]; then
  echo "Run this script from the extracted project root."
  exit 2
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required on the server."
  exit 2
fi

if docker ps >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  DOCKER=(docker)
elif sudo docker ps >/dev/null 2>&1 && sudo docker compose version >/dev/null 2>&1; then
  DOCKER=(sudo docker)
else
  echo "Docker Engine and Docker Compose plugin are required on the server."
  exit 2
fi

compose() {
  "${DOCKER[@]}" compose -f docker-compose.yml -f docker-compose.cloud.yml --env-file .env.production "$@"
}

print_diagnostics() {
  local exit_code=$?
  echo ""
  echo "Deployment failed with exit code ${exit_code}. Diagnostics:"
  if [[ -f ".env.production" ]]; then
    compose ps || true
    echo ""
    echo "--- backend logs ---"
    compose logs --tail=120 backend || true
    echo ""
    echo "--- nginx logs ---"
    compose logs --tail=80 nginx || true
    echo ""
    echo "--- postgres logs ---"
    compose logs --tail=80 postgres || true
  fi
  exit "${exit_code}"
}

trap print_diagnostics ERR

generate_secret() {
  if command -v openssl >/dev/null 2>&1; then
    openssl rand -hex 32
  else
    python3 - <<'PY'
import secrets
print(secrets.token_hex(32))
PY
  fi
}

if [[ -f ".env.production" ]]; then
  echo "Reusing existing .env.production so database credentials stay aligned with the current Docker volume."
else
  POSTGRES_PASSWORD_VALUE="$(generate_secret)"
  AUTH_SECRET_KEY_VALUE="$(generate_secret)$(generate_secret)"
  DATABASE_URL_VALUE="postgresql+psycopg://agent_user:${POSTGRES_PASSWORD_VALUE}@postgres:5432/manufacturing_ai_agent"

  python3 - <<PY
from pathlib import Path

source = Path(".env.production.example")
target = Path(".env.production")
values = {}
for raw_line in source.read_text(encoding="utf-8").splitlines():
    if not raw_line.strip() or raw_line.lstrip().startswith("#") or "=" not in raw_line:
        continue
    key, value = raw_line.split("=", 1)
    values[key] = value

values.update(
    {
        "ENVIRONMENT": "production",
        "POSTGRES_PASSWORD": "${POSTGRES_PASSWORD_VALUE}",
        "DATABASE_URL": "${DATABASE_URL_VALUE}",
        "AUTH_SECRET_KEY": "${AUTH_SECRET_KEY_VALUE}",
        "LLM_GATEWAY_MODE": "mock",
        "LLM_PROVIDER": "mock",
        "LLM_MODEL": "mock-enterprise-agent",
        "LLM_FALLBACK_MODEL": "mock-safe-fallback",
        "DEEPSEEK_API_KEY": "",
        "DEEPSEEK_BASE_URL": "https://api.deepseek.com",
        "DEEPSEEK_TIMEOUT_SECONDS": "20",
    }
)

ordered_keys = [
    "APP_NAME",
    "APP_VERSION",
    "ENVIRONMENT",
    "LOG_LEVEL",
    "ENABLE_SQL_ECHO",
    "POSTGRES_DB",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "DATABASE_URL",
    "REDIS_URL",
    "LLM_GATEWAY_MODE",
    "LLM_PROVIDER",
    "LLM_MODEL",
    "LLM_FALLBACK_MODEL",
    "DEEPSEEK_API_KEY",
    "DEEPSEEK_BASE_URL",
    "DEEPSEEK_TIMEOUT_SECONDS",
    "AUTH_SECRET_KEY",
    "ACCESS_TOKEN_EXPIRE_MINUTES",
]

lines = [
    "# Generated on the server by scripts/deploy_cloud_server.sh.",
    "# This MVP uses simulated ERP/MES/WMS data and read-only Agent tools.",
]
for key in ordered_keys:
    if key in values:
        lines.append(f"{key}={values[key]}")

target.write_text("\\n".join(lines) + "\\n", encoding="utf-8")
PY
fi

python3 scripts/check_production_env.py --env-file .env.production
compose config >/tmp/manufacturing-ai-agent-compose-config.yml

if [[ "${RESET_DEMO_VOLUME}" == "1" ]]; then
  echo "RESET_DEMO_VOLUME=1: removing existing demo containers and volumes before startup."
  compose down -v || true
fi

compose up -d --build
compose exec -T backend python -m app.db.init_db
compose exec -T backend python scripts/seed_demo_data.py
python3 scripts/verify_cloud_deployment.py \
  --base-url "${PUBLIC_BASE_URL}" \
  --environment cloud \
  --write-report docs/cloud-deployment-check-report.md
python3 scripts/verify_cloud_report.py --report docs/cloud-deployment-check-report.md

compose ps
echo "Cloud deployment verification passed for ${PUBLIC_BASE_URL}"
