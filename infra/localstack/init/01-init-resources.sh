#!/bin/bash
# Bootstrap de recursos AWS en LocalStack.
# Se ejecuta automáticamente cuando LocalStack está listo (carpeta ready.d).
set -euo pipefail

BUCKET="dnd-manuals"
MANUAL_LOCAL="/data/player-handbook.pdf"
MANUAL_KEY="player-handbook.pdf"

echo "[bootstrap] Creando bucket S3: ${BUCKET}"
awslocal s3 mb "s3://${BUCKET}" || true

if [ -f "${MANUAL_LOCAL}" ]; then
  echo "[bootstrap] Subiendo manual a s3://${BUCKET}/${MANUAL_KEY}"
  awslocal s3 cp "${MANUAL_LOCAL}" "s3://${BUCKET}/${MANUAL_KEY}"
else
  echo "[bootstrap] AVISO: no se encontró ${MANUAL_LOCAL}; omito la subida"
fi

echo "[bootstrap] Guardando clave de OpenAI en Secrets Manager"
awslocal secretsmanager create-secret \
  --name "openai-api-key" \
  --secret-string "${OPENAI_API_KEY:-sk-placeholder}" \
  >/dev/null 2>&1 || \
awslocal secretsmanager put-secret-value \
  --secret-id "openai-api-key" \
  --secret-string "${OPENAI_API_KEY:-sk-placeholder}" >/dev/null

echo "[bootstrap] Guardando credenciales de BBDD en Secrets Manager"
awslocal secretsmanager create-secret \
  --name "db-credentials" \
  --secret-string '{"username":"rag","password":"ragpass","host":"postgres","port":5432,"dbname":"ragdb"}' \
  >/dev/null 2>&1 || true

echo "[bootstrap] Recursos listos."
