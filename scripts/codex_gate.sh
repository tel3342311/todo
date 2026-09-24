#!/usr/bin/env bash
# 單元 5：codex exec 當 quality gate（任何 CI 都能用：GitHub Actions / Harness.io / GitLab）
# 用 --output-schema 逼 Codex 回傳結構化 JSON，再用 jq 決定 pipeline 要不要擋下來。
set -euo pipefail

SCHEMA=".github/codex/schemas/review.json"
OUT="codex-review.json"

codex exec \
  --sandbox read-only \
  --ask-for-approval never \
  --output-schema "$SCHEMA" \
  -o "$OUT" \
  "$(cat .github/codex/prompts/review.md)

請以符合 schema 的 JSON 回覆。"

echo "===== Codex review ====="
cat "$OUT"

VERDICT=$(jq -r '.verdict' "$OUT")
BLOCKING=$(jq '[.findings[] | select(.severity=="blocking")] | length' "$OUT")

if [[ "$VERDICT" == "needs_changes" || "$BLOCKING" -gt 0 ]]; then
  echo "::error::Codex 審查：$BLOCKING 個 blocking 問題，pipeline 停止"
  exit 1
fi
echo "Codex 審查通過"
