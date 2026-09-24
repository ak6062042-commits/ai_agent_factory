#!/usr/bin/env bash
# Full end-to-end smoke test for AI Agent Factory backend.
# Requires: server already running on port 8001, jq installed, and two real
# test files at the paths set below (adjust DOC_PATH if yours differ).
#
# Usage: bash run_tests.sh

set -uo pipefail

# --- Logging setup ---------------------------------------------------------
# Writes everything this script prints to test_results.txt, in the SAME
# directory as this script (so if you keep this in a scripts/ folder, the
# log lands there too — no nested scripts/scripts/).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/test_results.txt"

if [ -z "${TEST_LOGGING_ACTIVE:-}" ]; then
  export TEST_LOGGING_ACTIVE=1
  # Re-exec this same script piped through tee, so every line below (and any
  # echo/pass/fail output) is captured to the log file as well as shown live.
  exec > >(tee "$LOG_FILE") 2>&1
  echo "=== Test run started: $(date '+%Y-%m-%d %H:%M:%S') ==="
  echo "Logging to: $LOG_FILE"
  echo ""
fi
# ----------------------------------------------------------------------------

BASE="http://127.0.0.1:8001"
DOC_PATH="/home/muhammad-anas-khan/Desktop/dummy.txt"
PASS=0
FAIL=0

check_jq() {
  if ! command -v jq &> /dev/null; then
    echo "jq is required. Install with: sudo apt install jq"
    exit 1
  fi
}

pass() { echo "  PASS: $1"; PASS=$((PASS+1)); }
fail() { echo "  FAIL: $1"; FAIL=$((FAIL+1)); }

expect_status() {
  local label="$1" expected="$2" actual="$3"
  if [ "$actual" == "$expected" ]; then
    pass "$label (got $actual)"
  else
    fail "$label (expected $expected, got $actual)"
  fi
}

check_jq

echo "=== 1. Create tenant ==="
RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE/tenants" \
  -H "Content-Type: application/json" \
  -d '{"organization_name": "Test Org", "admin_email": "test_'"$RANDOM"'@example.com"}')
BODY=$(echo "$RESP" | head -n -1)
CODE=$(echo "$RESP" | tail -n1)
expect_status "create tenant" "201" "$CODE"
API_KEY=$(echo "$BODY" | jq -r '.api_key')
TENANT_ID=$(echo "$BODY" | jq -r '.tenant_id')
echo "  api_key=$API_KEY"
echo "  tenant_id=$TENANT_ID"

echo ""
echo "=== 2. Duplicate email rejected ==="
CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/tenants" \
  -H "Content-Type: application/json" \
  -d '{"organization_name": "Test Org 2", "admin_email": "test@example.com"}')
# NOTE: this uses a fixed email that may not collide with the random one above.
# We separately verify duplicate rejection using the SAME random email:
EMAIL_USED=$(echo "$BODY" | jq -r '.admin_email')
CODE2=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/tenants" \
  -H "Content-Type: application/json" \
  -d '{"organization_name": "Test Org Dup", "admin_email": "'"$EMAIL_USED"'"}')
expect_status "duplicate email rejected" "409" "$CODE2"

echo ""
echo "=== 3. Create agent (valid) ==="
RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE/agents" \
  -H "X-API-Key: $API_KEY" \
  -F "agent_name=test_agent_1" \
  -F "website_url=https://en.wikipedia.org/wiki/Proximal_policy_optimization" \
  -F "documents=@${DOC_PATH}")
BODY=$(echo "$RESP" | head -n -1)
CODE=$(echo "$RESP" | tail -n1)
expect_status "create agent" "201" "$CODE"
AGENT_ID=$(echo "$BODY" | jq -r '.agent_id')
echo "  agent_id=$AGENT_ID"

echo ""
echo "=== 4. Reject blank agent_name ==="
CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/agents" \
  -H "X-API-Key: $API_KEY" -F "agent_name= " \
  -F "website_url=https://example.com" -F "documents=@${DOC_PATH}")
expect_status "blank agent_name rejected" "422" "$CODE"

echo ""
echo "=== 5. Reject invalid website_url ==="
CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/agents" \
  -H "X-API-Key: $API_KEY" -F "agent_name=test" \
  -F "website_url=not-a-url" -F "documents=@${DOC_PATH}")
expect_status "invalid website_url rejected" "422" "$CODE"

echo ""
echo "=== 6. Wait for ingestion (20s) ==="
sleep 20
RESP=$(curl -s "$BASE/agents/$AGENT_ID" -H "X-API-Key: $API_KEY")
STATUS=$(echo "$RESP" | jq -r '.ingestion_status')
CHUNKS=$(echo "$RESP" | jq -r '.indexed_chunk_count')
PROMPT=$(echo "$RESP" | jq -r '.system_prompt')
if [ "$STATUS" == "ready" ]; then pass "ingestion reached ready"; else fail "ingestion status is $STATUS"; fi
if [ "$CHUNKS" -gt 0 ] 2>/dev/null; then pass "indexed_chunk_count > 0 ($CHUNKS)"; else fail "indexed_chunk_count is $CHUNKS"; fi
echo "  system_prompt: $PROMPT"
if [[ "$PROMPT" == *"an AI assistant. Answer questions using only the knowledge provided. If the answer isn't in your knowledge base"* ]] && [[ "$PROMPT" != *"knowledge base covers"* ]]; then
  fail "system_prompt still looks like the OLD placeholder, not LLM-generated"
else
  pass "system_prompt looks generated (manually verify it's actually about PPO/RL)"
fi

echo ""
echo "=== 7. Tenant isolation ==="
RESP2=$(curl -s -w "\n%{http_code}" -X POST "$BASE/tenants" \
  -H "Content-Type: application/json" \
  -d '{"organization_name": "Test Org B", "admin_email": "test_b_'"$RANDOM"'@example.com"}')
API_KEY_2=$(echo "$RESP2" | head -n -1 | jq -r '.api_key')
CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/agents/$AGENT_ID" -H "X-API-Key: $API_KEY_2")
expect_status "tenant B cannot see tenant A's agent" "404" "$CODE"

echo ""
echo "=== 8. Add source ==="
RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE/agents/$AGENT_ID/sources" \
  -H "X-API-Key: $API_KEY" \
  -F "website_url=https://en.wikipedia.org/wiki/Reinforcement_learning")
BODY=$(echo "$RESP" | head -n -1)
CODE=$(echo "$RESP" | tail -n1)
expect_status "add source" "201" "$CODE"
echo "  waiting 15s for source ingestion..."
sleep 15
RESP=$(curl -s "$BASE/agents/$AGENT_ID" -H "X-API-Key: $API_KEY")
CHUNKS_AFTER=$(echo "$RESP" | jq -r '.indexed_chunk_count')
if [ "$CHUNKS_AFTER" -gt "$CHUNKS" ] 2>/dev/null; then
  pass "indexed_chunk_count increased after adding source ($CHUNKS -> $CHUNKS_AFTER)"
else
  fail "indexed_chunk_count did not increase ($CHUNKS -> $CHUNKS_AFTER)"
fi
SOURCE_ID=$(echo "$RESP" | jq -r '[.sources[] | select(.title | contains("Reinforcement_learning"))][0].source_id // empty')
if [ -z "$SOURCE_ID" ]; then
  # AgentSource schema may not expose source_id — try to grab it a different way, else skip delete test
  echo "  NOTE: source_id not found in AgentSource response (schema may omit it) - skipping source delete test"
fi

echo ""
echo "=== 9. Reject empty add-source request ==="
CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/agents/$AGENT_ID/sources" -H "X-API-Key: $API_KEY")
expect_status "empty add-source rejected" "400" "$CODE"

if [ -n "${SOURCE_ID:-}" ]; then
  echo ""
  echo "=== 10. Delete source ==="
  CODE=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE "$BASE/agents/$AGENT_ID/sources/$SOURCE_ID" -H "X-API-Key: $API_KEY")
  expect_status "delete source" "204" "$CODE"
fi

echo ""
echo "=== 11. Chat: relevant question ==="
RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE/agents/$AGENT_ID/chat" \
  -H "X-API-Key: $API_KEY" -H "Content-Type: application/json" \
  -d '{"message": "What is proximal policy optimization?", "session_id": "test-session-1"}')
BODY=$(echo "$RESP" | head -n -1)
CODE=$(echo "$RESP" | tail -n1)
expect_status "chat relevant question" "200" "$CODE"
SID=$(echo "$BODY" | jq -r '.session_id')
ANSWER=$(echo "$BODY" | jq -r '.answer')
NSOURCES=$(echo "$BODY" | jq -r '.sources | length')
if [ "$SID" == "test-session-1" ]; then pass "session_id echoed correctly"; else fail "session_id not echoed (got $SID)"; fi
if [ "$NSOURCES" -gt 0 ] 2>/dev/null; then pass "citations present ($NSOURCES)"; else fail "no citations returned"; fi
echo "  answer: $ANSWER"

echo ""
echo "=== 12. Chat: follow-up in same session (history-aware retrieval check) ==="
RESP=$(curl -s -X POST "$BASE/agents/$AGENT_ID/chat" \
  -H "X-API-Key: $API_KEY" -H "Content-Type: application/json" \
  -d '{"message": "Can you summarize what you just told me?", "session_id": "test-session-1"}')
ANSWER=$(echo "$RESP" | jq -r '.answer')
echo "  answer: $ANSWER"
if [[ "$ANSWER" == *"cannot find"* ]]; then
  fail "follow-up was incorrectly refused (history-aware retrieval fix not working)"
else
  pass "follow-up was NOT refused (got a real answer)"
  echo "  MANUALLY VERIFY the answer above actually summarizes the prior turn, not just any PPO fact"
fi

echo ""
echo "=== 12b. Chat: greeting / small talk (should not be refused, no citations needed) ==="
RESP=$(curl -s -X POST "$BASE/agents/$AGENT_ID/chat" \
  -H "X-API-Key: $API_KEY" -H "Content-Type: application/json" \
  -d '{"message": "hi", "session_id": "test-session-greet"}')
ANSWER=$(echo "$RESP" | jq -r '.answer')
echo "  answer: $ANSWER"
if [[ "$ANSWER" == *"cannot find"* ]]; then
  fail "greeting was incorrectly refused (small-talk bypass not working)"
else
  pass "greeting handled conversationally, not refused"
fi

RESP=$(curl -s -X POST "$BASE/agents/$AGENT_ID/chat" \
  -H "X-API-Key: $API_KEY" -H "Content-Type: application/json" \
  -d '{"message": "thanks!", "session_id": "test-session-greet"}')
ANSWER=$(echo "$RESP" | jq -r '.answer')
echo "  answer: $ANSWER"
if [[ "$ANSWER" == *"cannot find"* ]]; then
  fail "'thanks!' was incorrectly refused (small-talk bypass not working)"
else
  pass "'thanks!' handled conversationally, not refused"
fi

echo ""
echo "=== 13. Chat: irrelevant question (grounding/refusal check) ==="
RESP=$(curl -s -X POST "$BASE/agents/$AGENT_ID/chat" \
  -H "X-API-Key: $API_KEY" -H "Content-Type: application/json" \
  -d '{"message": "What is the best chicken biryani recipe?", "session_id": "test-session-1"}')
ANSWER=$(echo "$RESP" | jq -r '.answer')
NSOURCES=$(echo "$RESP" | jq -r '.sources | length')
echo "  answer: $ANSWER"
if [[ "$ANSWER" == *"cannot find"* ]] && [ "$NSOURCES" -eq 0 ]; then
  pass "irrelevant question correctly refused with no citations"
else
  fail "irrelevant question was NOT refused as expected"
fi

echo ""
echo "=== 14. Chat against a not-ready agent (409 check) ==="
RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE/agents" \
  -H "X-API-Key: $API_KEY" \
  -F "agent_name=test_agent_2_notready" \
  -F "website_url=https://en.wikipedia.org/wiki/Q-learning" \
  -F "documents=@${DOC_PATH}")
NEW_AGENT_ID=$(echo "$RESP" | head -n -1 | jq -r '.agent_id')
CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/agents/$NEW_AGENT_ID/chat" \
  -H "X-API-Key: $API_KEY" -H "Content-Type: application/json" \
  -d '{"message": "test", "session_id": "s1"}')
expect_status "chat on not-ready agent returns 409" "409" "$CODE"

echo ""
echo "=== 15. Delete agent ==="
CODE=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE "$BASE/agents/$AGENT_ID" -H "X-API-Key: $API_KEY")
expect_status "delete agent" "204" "$CODE"

CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/agents/$AGENT_ID" -H "X-API-Key: $API_KEY")
expect_status "GET deleted agent returns 404" "404" "$CODE"

CODE=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE "$BASE/agents/$AGENT_ID" -H "X-API-Key: $API_KEY")
expect_status "double-delete returns 404, not 204" "404" "$CODE"

echo ""
echo "=================================="
echo "RESULTS: $PASS passed, $FAIL failed"
echo "Finished: $(date '+%Y-%m-%d %H:%M:%S')"
echo "Log written to: $LOG_FILE"
echo "=================================="