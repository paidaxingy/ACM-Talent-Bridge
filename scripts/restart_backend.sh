#!/usr/bin/env bash
set -euo pipefail

# 后端重启脚本（Docker Compose 版本）
# 用途：在修改后端代码/依赖或数据库结构后，快速重启 API + Worker + Beat 三个服务。
#
# 使用方式（从任意目录都可以执行）：
#   bash /home/yzt/workspace/ACM-Talent-Bridge/scripts/restart_backend.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${ROOT_DIR}"

echo "[backend-restart] project root: ${ROOT_DIR}"

echo "[backend-restart] building judge runner image (for Docker 判题，若已存在会复用缓存)..."
docker build -t acm-judge-runner:latest docker/judge-runner >/dev/null 2>&1 || {
  echo "[backend-restart] warning: failed to build acm-judge-runner image（请检查 docker/judge-runner）"
}
echo "[backend-restart] stopping api/worker/beat (if running)..."
docker compose stop api worker beat >/dev/null 2>&1 || true

echo "[backend-restart] removing old api/worker/beat containers..."
docker compose rm -f api worker beat >/dev/null 2>&1 || true

echo "[backend-restart] starting api/worker/beat with --build..."
# 注意：要启用 Docker 判题，请在 backend/.env 中设置：
#   JUDGE_ENABLE_DOCKER=1
#   JUDGE_DOCKER_MODE=volume
#   JUDGE_WORKSPACE_DIR=/judge_workspace
#   JUDGE_WORKSPACE_VOLUME=judge_workspace
docker compose up -d --build api worker beat

echo "[backend-restart] tailing latest api logs (20 lines):"
docker compose logs --tail=20 api || true

echo "[backend-restart] done."

