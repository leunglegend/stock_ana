#!/usr/bin/env bash

set -u

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${PROJECT_DIR}" || exit 0

# Automatic publishing is intentionally limited to the test branch.
if [[ "$(git branch --show-current)" != "test" ]]; then
  exit 0
fi

# Ignore edits that cannot affect the application, while still allowing new source files.
changed_files="$(git status --short | awk '{print substr($0, 4)}')"
if [[ -z "${changed_files}" ]] || ! printf '%s\n' "${changed_files}" | grep -Eq '(^|/)(frontend/src|frontend/tests|frontend/package(-lock)?\.json|backend/app|backend/tests|backend/requirements\.txt|README\.md|CLAUDE\.md|start\.sh|\.claude/settings\.json)'; then
  exit 0
fi

message=''
if ! (cd frontend && node --test tests/*.test.js && npm run build) > /tmp/stock-ana-auto-test.log 2>&1; then
  message="自动提交已跳过：前端测试或构建失败。详见 /tmp/stock-ana-auto-test.log"
  jq -cn --arg message "${message}" '{systemMessage:$message}'
  exit 0
fi
if ! python3 -m compileall -q backend/app >> /tmp/stock-ana-auto-test.log 2>&1; then
  message="自动提交已跳过：后端 Python 编译检查失败。详见 /tmp/stock-ana-auto-test.log"
  jq -cn --arg message "${message}" '{systemMessage:$message}'
  exit 0
fi

# Stage only repository changes; .gitignore excludes secrets, databases, dependencies, and runtime files.
git add -A
if git diff --cached --quiet; then
  exit 0
fi

git commit -m "chore: auto-save verified workspace changes" -m "Co-Authored-By: Claude Code <noreply@anthropic.com>" > /tmp/stock-ana-auto-commit.log 2>&1 || {
  jq -cn '{systemMessage:"自动提交失败，请检查 /tmp/stock-ana-auto-commit.log"}'
  exit 0
}

if git push origin test > /tmp/stock-ana-auto-push.log 2>&1; then
  jq -cn '{systemMessage:"测试通过，已自动提交并推送到 origin/test。"}'
else
  jq -cn '{systemMessage:"测试通过，已自动提交到本地 test；推送 GitHub 失败，请检查认证或 /tmp/stock-ana-auto-push.log。"}'
fi
