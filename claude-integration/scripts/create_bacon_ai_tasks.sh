#!/bin/bash
# =============================================================================
# BACON-AI 12-Phase Framework Task Creator for Focalboard
#
# This script demonstrates how to use the Focalboard REST API to create
# cards representing the complete BACON-AI 12-Phase Framework.
#
# Prerequisites:
# - Focalboard running on localhost:8000
# - Valid authentication token
# - Board ID for the BACON-AI board
#
# API Authentication:
# - Header: Authorization: Bearer <token>
# - Header: X-Requested-With: XMLHttpRequest (required for CSRF protection)
# =============================================================================

# Configuration
FOCALBOARD_URL="http://localhost:8000"
AUTH_TOKEN="k77tg84g87pd6tjk7rdho1kqs9h"
BOARD_ID="bd5mw98s3cjftjnef77q8c4oone"

# Property IDs (from board cardProperties)
STATUS_PROP_ID="a972dc7a-5f4c-45d2-8044-8c28c69717f1"
PRIORITY_PROP_ID="d3d682bf-e074-49d9-8df5-7320921c2d23"

# Status option IDs
STATUS_NOT_STARTED="ayz81h9f3dwp7rzzbdebesc7ute"
STATUS_IN_PROGRESS="ar6b8m3jxr3asyxhr8iucdbo6yc"
STATUS_BLOCKED="afi4o5nhnqc3smtzs1hs3ij34dh"
STATUS_COMPLETED="adeo5xuwne3qjue83fcozekz8ko"

# Priority option IDs
PRIORITY_HIGH="d3bfb50f-f569-4bad-8a3a-dd15c3f60101"
PRIORITY_MEDIUM="87f59784-b859-4c24-8ebe-17c766e081dd"
PRIORITY_LOW="98a57627-0f76-471d-850d-91f3ed9fd213"

# Function to create a card
create_card() {
    local title="$1"
    local icon="$2"
    local priority="$3"

    local json=$(jq -n \
        --arg title "$title" \
        --arg icon "$icon" \
        --arg status_prop "$STATUS_PROP_ID" \
        --arg status_val "$STATUS_NOT_STARTED" \
        --arg priority_prop "$PRIORITY_PROP_ID" \
        --arg priority_val "$priority" \
        '{
            title: $title,
            icon: $icon,
            properties: {
                ($status_prop): $status_val,
                ($priority_prop): $priority_val
            }
        }')

    curl -s -X POST "${FOCALBOARD_URL}/api/v2/boards/${BOARD_ID}/cards?disable_notify=true" \
        -H "Content-Type: application/json" \
        -H "Accept: application/json" \
        -H "X-Requested-With: XMLHttpRequest" \
        -H "Authorization: Bearer ${AUTH_TOKEN}" \
        -d "$json"

    echo ""
}

echo "=== Creating BACON-AI 12-Phase Framework Tasks ==="
echo ""

# Phase 0: Verification (Critical Pre-Phase)
echo "Creating Phase 0 tasks..."
create_card "Phase 0: Verification (Critical Pre-Phase)" "🔍" "$PRIORITY_HIGH"
create_card "0.1 Query lessons learned database for similar problems" "📚" "$PRIORITY_HIGH"
create_card "0.2 Web search for current best practices (2025/2026)" "🌐" "$PRIORITY_HIGH"
create_card "0.3 Consult external AI models (GPT-5, Gemini, Grok)" "🤖" "$PRIORITY_HIGH"
create_card "0.4 Document current state and assumptions" "📝" "$PRIORITY_HIGH"
create_card "0.5 Validate problem is not already solved" "✅" "$PRIORITY_HIGH"

# Phase 1: Problem Definition
echo "Creating Phase 1 tasks..."
create_card "Phase 1: Problem Definition (Design Thinking)" "🎯" "$PRIORITY_HIGH"
create_card "1.1 Create empathy map (user needs, pains, gains)" "💭" "$PRIORITY_HIGH"
create_card "1.2 Define problem statement using 5W+1H framework" "❓" "$PRIORITY_HIGH"
create_card "1.3 Apply Six Thinking Hats for perspective review" "🎩" "$PRIORITY_HIGH"
create_card "1.4 Document success criteria and constraints" "📋" "$PRIORITY_HIGH"
create_card "1.5 Get stakeholder approval on problem definition" "✔️" "$PRIORITY_HIGH"

# Phase 2: Data Gathering
echo "Creating Phase 2 tasks..."
create_card "Phase 2: Data Gathering (Systems Thinking)" "📊" "$PRIORITY_HIGH"
create_card "2.1 Create context map of system boundaries" "🗺️" "$PRIORITY_HIGH"
create_card "2.2 Conduct stakeholder analysis" "👥" "$PRIORITY_HIGH"
create_card "2.3 Collect relevant data from all sources" "📥" "$PRIORITY_HIGH"
create_card "2.4 Review existing documentation and code" "📖" "$PRIORITY_HIGH"
create_card "2.5 Identify data gaps and plan collection" "🔎" "$PRIORITY_HIGH"

# Phase 3: Analysis
echo "Creating Phase 3 tasks..."
create_card "Phase 3: Analysis (TRIZ + Systems Thinking)" "🔬" "$PRIORITY_HIGH"
create_card "3.1 Create causal loop diagrams" "🔄" "$PRIORITY_HIGH"
create_card "3.2 Apply TRIZ contradiction matrix" "⚡" "$PRIORITY_HIGH"
create_card "3.3 Identify patterns from collected data" "🔍" "$PRIORITY_HIGH"
create_card "3.4 Use deep analysis tools (mindmaps, diagrams)" "🧠" "$PRIORITY_HIGH"
create_card "3.5 QA review with confidence levels" "✅" "$PRIORITY_MEDIUM"

# Phase 4: Solution Generation
echo "Creating Phase 4 tasks..."
create_card "Phase 4: Solution Generation (TRIZ 40 Principles)" "💡" "$PRIORITY_HIGH"
create_card "4.1 Apply TRIZ 40 Inventive Principles" "🛠️" "$PRIORITY_HIGH"
create_card "4.2 Parallel agent generation (5-10 agents)" "🤖" "$PRIORITY_HIGH"
create_card "4.3 Collective discussion to generate more ideas" "💬" "$PRIORITY_HIGH"
create_card "4.4 Compile master solution list (min 20 solutions)" "📝" "$PRIORITY_HIGH"
create_card "4.5 Enforce NO EVALUATION rule (ideas only)" "🚫" "$PRIORITY_MEDIUM"

# Phase 5: Evaluation
echo "Creating Phase 5 tasks..."
create_card "Phase 5: Evaluation (Multi-Criteria Analysis)" "⚖️" "$PRIORITY_HIGH"
create_card "5.1 Apply feasibility filtering to all solutions" "🔍" "$PRIORITY_HIGH"
create_card "5.2 Create multi-criteria scoring matrix" "📊" "$PRIORITY_HIGH"
create_card "5.3 Apply Six Thinking Hats (Yellow/Black)" "🎩" "$PRIORITY_HIGH"
create_card "5.4 Conduct weighted voting by agents" "🗳️" "$PRIORITY_HIGH"
create_card "5.5 Identify top 3 solutions with scores" "🏆" "$PRIORITY_HIGH"

# Phase 6: Consensus Voting
echo "Creating Phase 6 tasks..."
create_card "Phase 6: Consensus Voting (Multi-Model + Human)" "🗳️" "$PRIORITY_HIGH"
create_card "6.1 Collect votes from 10 BACON-AI agents" "🤖" "$PRIORITY_HIGH"
create_card "6.2 Consult external AI models (GPT-5, Gemini, Claude API, Grok)" "🌐" "$PRIORITY_HIGH"
create_card "6.3 Get human vote from Colin (final authority)" "👤" "$PRIORITY_HIGH"
create_card "6.4 Calculate consensus percentage" "📊" "$PRIORITY_HIGH"
create_card "6.5 Apply decision rules (>70% proceed, <50% parallel swarms)" "📋" "$PRIORITY_MEDIUM"

# Phase 7: Design Excellence
echo "Creating Phase 7 tasks..."
create_card "Phase 7: Design Excellence (Architectural Quality)" "🏗️" "$PRIORITY_HIGH"
create_card "7.1 Create Architecture Decision Records (ADRs)" "📄" "$PRIORITY_HIGH"
create_card "7.2 Draw system architecture diagrams" "📐" "$PRIORITY_HIGH"
create_card "7.3 Define component responsibilities" "🧩" "$PRIORITY_HIGH"
create_card "7.4 Identify design patterns to apply" "🔧" "$PRIORITY_MEDIUM"
create_card "7.5 Specify quality attributes (performance, security)" "⭐" "$PRIORITY_MEDIUM"

# Phase 8: Implementation Planning
echo "Creating Phase 8 tasks..."
create_card "Phase 8: Implementation Planning (Execution Details)" "📋" "$PRIORITY_HIGH"
create_card "8.1 Create Work Breakdown Structure (WBS)" "📝" "$PRIORITY_HIGH"
create_card "8.2 Create dependency graph (Gantt chart)" "📊" "$PRIORITY_HIGH"
create_card "8.3 Allocate resources (team, compute, tools)" "👥" "$PRIORITY_HIGH"
create_card "8.4 Document risk mitigation plan" "⚠️" "$PRIORITY_MEDIUM"
create_card "8.5 Define success criteria and acceptance tests" "✅" "$PRIORITY_HIGH"

# Phase 9: TDD Build
echo "Creating Phase 9 tasks..."
create_card "Phase 9: TDD Build (Test-Driven Development)" "🧪" "$PRIORITY_HIGH"
create_card "9.1 Establish test baseline (run all existing tests)" "📊" "$PRIORITY_HIGH"
create_card "9.2 RED: Write failing test first" "🔴" "$PRIORITY_HIGH"
create_card "9.3 GREEN: Write minimum code to pass test" "🟢" "$PRIORITY_HIGH"
create_card "9.4 REFACTOR: Improve code quality (all tests pass)" "🔵" "$PRIORITY_HIGH"
create_card "9.5 Progress through V-Model (TUT→FUT→SIT→UAT)" "📈" "$PRIORITY_HIGH"
create_card "9.6 Verify >90% code coverage" "✅" "$PRIORITY_MEDIUM"

# Phase 10: Change Management
echo "Creating Phase 10 tasks..."
create_card "Phase 10: Change Management (User Adoption)" "📣" "$PRIORITY_MEDIUM"
create_card "10.1 Create user training materials (guides, docs)" "📚" "$PRIORITY_MEDIUM"
create_card "10.2 Prepare demo video/walkthrough script" "🎬" "$PRIORITY_MEDIUM"
create_card "10.3 Set up feedback collection mechanism" "💬" "$PRIORITY_MEDIUM"
create_card "10.4 Execute communication plan" "📢" "$PRIORITY_MEDIUM"
create_card "10.5 Track adoption metrics (usage, satisfaction, NPS)" "📊" "$PRIORITY_MEDIUM"

# Phase 11: Deployment
echo "Creating Phase 11 tasks..."
create_card "Phase 11: Deployment (Production Rollout)" "🚀" "$PRIORITY_HIGH"
create_card "11.1 Complete pre-deployment checklist" "📋" "$PRIORITY_HIGH"
create_card "11.2 Run deployment automation script" "⚙️" "$PRIORITY_HIGH"
create_card "11.3 Execute health checks" "🏥" "$PRIORITY_HIGH"
create_card "11.4 Verify monitoring and alerting" "📡" "$PRIORITY_HIGH"
create_card "11.5 Run smoke tests in production" "🧪" "$PRIORITY_HIGH"
create_card "11.6 Get UAT approval from Colin" "✔️" "$PRIORITY_HIGH"

# Phase 12: SSC Retrospective
echo "Creating Phase 12 tasks..."
create_card "Phase 12: SSC Retrospective (Organizational Learning)" "🔄" "$PRIORITY_HIGH"
create_card "12.1 Collect human feedback (Colin's perspective)" "👤" "$PRIORITY_HIGH"
create_card "12.2 Run agent SSC retrospective (Stop/Start/Continue)" "🤖" "$PRIORITY_HIGH"
create_card "12.3 Update SE-Agent trajectory memory" "🧠" "$PRIORITY_HIGH"
create_card "12.4 Add lessons learned to database (min 3)" "📚" "$PRIORITY_HIGH"
create_card "12.5 Document proven patterns (min 4)" "📝" "$PRIORITY_MEDIUM"
create_card "12.6 Assess organizational impact" "📊" "$PRIORITY_MEDIUM"
create_card "12.7 Execute dissemination plan" "📣" "$PRIORITY_MEDIUM"

echo ""
echo "=== All BACON-AI 12-Phase Framework Tasks Created ==="
echo ""
echo "Summary of API Usage:"
echo "  Endpoint: POST /api/v2/boards/{boardID}/cards"
echo "  Auth: Authorization: Bearer <token>"
echo "  CSRF: X-Requested-With: XMLHttpRequest"
echo ""
echo "To view tasks:"
echo "  curl -s -X GET '${FOCALBOARD_URL}/api/v2/boards/${BOARD_ID}/cards' \\"
echo "    -H 'Authorization: Bearer ${AUTH_TOKEN}' \\"
echo "    -H 'X-Requested-With: XMLHttpRequest' | jq '.'"
