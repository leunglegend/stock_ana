#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="${PROJECT_DIR}/backend"
FRONTEND_DIR="${PROJECT_DIR}/frontend"
RUNTIME_DIR="${BACKEND_DIR}/.runtime"
PID_FILE="${RUNTIME_DIR}/stock-analyzer.pid"
LOG_FILE="${RUNTIME_DIR}/stock-analyzer.log"
STARTUP_ATTEMPTS=20
STARTUP_DELAY_SECONDS=0.25

if [[ -x "${BACKEND_DIR}/venv/bin/python" ]]; then
  PYTHON="${BACKEND_DIR}/venv/bin/python"
elif [[ -x "${BACKEND_DIR}/.venv/bin/python" ]]; then
  PYTHON="${BACKEND_DIR}/.venv/bin/python"
else
  echo "错误：未找到后端虚拟环境。" >&2
  echo "请先运行：python3 -m venv backend/venv && backend/venv/bin/pip install -r backend/requirements.txt" >&2
  exit 1
fi

if ! "${PYTHON}" -c 'import uvicorn' >/dev/null 2>&1; then
  echo "错误：虚拟环境中未安装 uvicorn。" >&2
  echo "请先运行：backend/venv/bin/pip install -r backend/requirements.txt" >&2
  exit 1
fi

PORT="$(cd "${BACKEND_DIR}" && "${PYTHON}" -c 'from app.config import settings; print(settings.PORT)')"

if ! command -v npm >/dev/null 2>&1; then
  echo "错误：未找到 npm，请先安装 Node.js 和 npm。" >&2
  exit 1
fi

if [[ ! -d "${FRONTEND_DIR}/node_modules" ]]; then
  echo "错误：前端依赖尚未安装。" >&2
  echo "请先运行：cd frontend && npm install" >&2
  exit 1
fi

mkdir -p "${RUNTIME_DIR}"

if [[ -f "${PID_FILE}" ]]; then
  running_pid="$(<"${PID_FILE}")"
  if [[ "${running_pid}" =~ ^[0-9]+$ ]] && kill -0 "${running_pid}" 2>/dev/null; then
    echo "应用已在运行，PID：${running_pid}" >&2
    echo "日志：${LOG_FILE}" >&2
    exit 1
  fi
  rm -f "${PID_FILE}"
fi

echo "构建前端静态资源..."
npm --prefix "${FRONTEND_DIR}" run build

cd "${BACKEND_DIR}"
nohup "${PYTHON}" -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT}" \
  >"${LOG_FILE}" 2>&1 </dev/null &
app_pid=$!
echo "${app_pid}" >"${PID_FILE}"

started=false
for ((attempt = 1; attempt <= STARTUP_ATTEMPTS; attempt++)); do
  if ! kill -0 "${app_pid}" 2>/dev/null; then
    break
  fi
  if "${PYTHON}" -c \
    "import urllib.request; urllib.request.urlopen('http://127.0.0.1:${PORT}/health', timeout=1)" \
    >/dev/null 2>&1; then
    started=true
    break
  fi
  sleep "${STARTUP_DELAY_SECONDS}"
done

if [[ "${started}" != true ]]; then
  kill "${app_pid}" 2>/dev/null || true
  rm -f "${PID_FILE}"
  echo "应用启动失败，日志如下：" >&2
  tail -n 20 "${LOG_FILE}" >&2
  exit 1
fi

echo "应用已在后台启动：http://localhost:${PORT}"
echo "PID：${app_pid}"
echo "日志：${LOG_FILE}"
