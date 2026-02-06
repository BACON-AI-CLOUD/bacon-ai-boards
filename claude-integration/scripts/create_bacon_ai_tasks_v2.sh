#!/bin/bash
# =============================================================================
# BACON-AI 12-Phase Framework Task Creator for Focalboard (v2)
#
# Improved version with:
# - Zero-padded sequential numbering (P00, P01... T001, T002...)
# - Due dates spread across project timeline
# - Estimated hours for each task
# - Proper sort order for Focalboard views
#
# Naming Convention:
#   Phase headers: "P00 - Phase Name" to "P12 - Phase Name"
#   Task items:    "T001 - Task Description" to "Txxx - Task Description"
#
# This ensures alphanumeric sorting works correctly:
#   P00 < P01 < P02 ... < P10 < P11 < P12
#   T001 < T002 < T003 ... < T099 < T100
# =============================================================================

set -e

# Configuration
FOCALBOARD_URL="http://localhost:8000"
AUTH_TOKEN="k77tg84g87pd6tjk7rdho1kqs9h"
BOARD_ID="bd5mw98s3cjftjnef77q8c4oone"

# Property IDs
STATUS_PROP_ID="a972dc7a-5f4c-45d2-8044-8c28c69717f1"
PRIORITY_PROP_ID="d3d682bf-e074-49d9-8df5-7320921c2d23"
ESTIMATED_HOURS_PROP_ID="a8daz81s4xjgke1ww6cwik5w7ye"
DUE_DATE_PROP_ID="a3zsw7xs8sxy7atj8b6totp3mby"

# Status option IDs
STATUS_NOT_STARTED="ayz81h9f3dwp7rzzbdebesc7ute"

# Priority option IDs
PRIORITY_HIGH="d3bfb50f-f569-4bad-8a3a-dd15c3f60101"
PRIORITY_MEDIUM="87f59784-b859-4c24-8ebe-17c766e081dd"
PRIORITY_LOW="98a57627-0f76-471d-850d-91f3ed9fd213"

# Task counter - global variable
TASK_NUM=1

# Function to calculate due date (days from start)
calc_due_date() {
    local days=$1
    local timestamp=$(( $(date +%s) + (days * 86400) ))
    echo "{\"from\":${timestamp}000}"
}

# Function to create a card with all properties
create_card() {
    local title="$1"
    local icon="$2"
    local priority="$3"
    local hours="$4"
    local due_days="$5"

    local due_date=$(calc_due_date $due_days)

    local json=$(jq -n \
        --arg title "$title" \
        --arg icon "$icon" \
        --arg status_prop "$STATUS_PROP_ID" \
        --arg status_val "$STATUS_NOT_STARTED" \
        --arg priority_prop "$PRIORITY_PROP_ID" \
        --arg priority_val "$priority" \
        --arg hours_prop "$ESTIMATED_HOURS_PROP_ID" \
        --arg hours_val "$hours" \
        --arg date_prop "$DUE_DATE_PROP_ID" \
        --argjson date_val "$due_date" \
        '{
            title: $title,
            icon: $icon,
            properties: {
                ($status_prop): $status_val,
                ($priority_prop): $priority_val,
                ($hours_prop): $hours_val,
                ($date_prop): $date_val
            }
        }')

    curl -s -X POST "${FOCALBOARD_URL}/api/v2/boards/${BOARD_ID}/cards?disable_notify=true" \
        -H "Content-Type: application/json" \
        -H "Accept: application/json" \
        -H "X-Requested-With: XMLHttpRequest" \
        -H "Authorization: Bearer ${AUTH_TOKEN}" \
        -d "$json" > /dev/null

    echo "  Created: $title"
}

# Function to create task with auto-incrementing number
create_task() {
    local desc="$1"
    local icon="$2"
    local priority="$3"
    local hours="$4"
    local due_days="$5"

    local task_id=$(printf "T%03d" $TASK_NUM)
    TASK_NUM=$((TASK_NUM + 1))

    create_card "${task_id} ── ${desc}" "$icon" "$priority" "$hours" "$due_days"
}

echo "=== Creating BACON-AI 12-Phase Framework Tasks (v2) ==="
echo "Project Start: $(date)"
echo ""

# ==============================================================================
# PHASE 0: Verification (Days 1-2)
# ==============================================================================
echo "Creating Phase 0: Verification..."
create_card "P00 ── Phase 0: Verification (Critical Pre-Phase)" "🔍" "$PRIORITY_HIGH" "8" "2"
create_task "Query lessons learned database" "📚" "$PRIORITY_HIGH" "1" "1"
create_task "Web search current best practices" "🌐" "$PRIORITY_HIGH" "2" "1"
create_task "Consult external AI models" "🤖" "$PRIORITY_HIGH" "2" "2"
create_task "Document current state and assumptions" "📝" "$PRIORITY_HIGH" "2" "2"
create_task "Validate problem not already solved" "✅" "$PRIORITY_HIGH" "1" "2"

# ==============================================================================
# PHASE 1: Problem Definition (Days 3-5)
# ==============================================================================
echo "Creating Phase 1: Problem Definition..."
create_card "P01 ── Phase 1: Problem Definition (Design Thinking)" "🎯" "$PRIORITY_HIGH" "12" "5"
create_task "Create empathy map" "💭" "$PRIORITY_HIGH" "3" "3"
create_task "Define problem using 5W+1H framework" "❓" "$PRIORITY_HIGH" "2" "4"
create_task "Apply Six Thinking Hats review" "🎩" "$PRIORITY_HIGH" "2" "4"
create_task "Document success criteria and constraints" "📋" "$PRIORITY_HIGH" "3" "5"
create_task "Get stakeholder approval" "✔️" "$PRIORITY_HIGH" "2" "5"

# ==============================================================================
# PHASE 2: Data Gathering (Days 6-8)
# ==============================================================================
echo "Creating Phase 2: Data Gathering..."
create_card "P02 ── Phase 2: Data Gathering (Systems Thinking)" "📊" "$PRIORITY_HIGH" "16" "8"
create_task "Create context map of system boundaries" "🗺️" "$PRIORITY_HIGH" "3" "6"
create_task "Conduct stakeholder analysis" "👥" "$PRIORITY_HIGH" "3" "6"
create_task "Collect data from all sources" "📥" "$PRIORITY_HIGH" "4" "7"
create_task "Review existing documentation" "📖" "$PRIORITY_HIGH" "4" "8"
create_task "Identify data gaps and plan collection" "🔎" "$PRIORITY_HIGH" "2" "8"

# ==============================================================================
# PHASE 3: Analysis (Days 9-12)
# ==============================================================================
echo "Creating Phase 3: Analysis..."
create_card "P03 ── Phase 3: Analysis (TRIZ + Systems Thinking)" "🔬" "$PRIORITY_HIGH" "20" "12"
create_task "Create causal loop diagrams" "🔄" "$PRIORITY_HIGH" "4" "9"
create_task "Apply TRIZ contradiction matrix" "⚡" "$PRIORITY_HIGH" "4" "10"
create_task "Identify patterns from data" "🔍" "$PRIORITY_HIGH" "4" "11"
create_task "Deep analysis (mindmaps, diagrams)" "🧠" "$PRIORITY_HIGH" "6" "12"
create_task "QA review with confidence levels" "✅" "$PRIORITY_MEDIUM" "2" "12"

# ==============================================================================
# PHASE 4: Solution Generation (Days 13-16)
# ==============================================================================
echo "Creating Phase 4: Solution Generation..."
create_card "P04 ── Phase 4: Solution Generation (TRIZ 40 Principles)" "💡" "$PRIORITY_HIGH" "16" "16"
create_task "Apply TRIZ 40 Inventive Principles" "🛠️" "$PRIORITY_HIGH" "4" "13"
create_task "Parallel agent generation (5-10 agents)" "🤖" "$PRIORITY_HIGH" "4" "14"
create_task "Collective discussion for more ideas" "💬" "$PRIORITY_HIGH" "3" "15"
create_task "Compile master solution list (min 20)" "📝" "$PRIORITY_HIGH" "3" "16"
create_task "Enforce NO EVALUATION rule" "🚫" "$PRIORITY_MEDIUM" "2" "16"

# ==============================================================================
# PHASE 5: Evaluation (Days 17-19)
# ==============================================================================
echo "Creating Phase 5: Evaluation..."
create_card "P05 ── Phase 5: Evaluation (Multi-Criteria Analysis)" "⚖️" "$PRIORITY_HIGH" "12" "19"
create_task "Apply feasibility filtering" "🔍" "$PRIORITY_HIGH" "2" "17"
create_task "Create multi-criteria scoring matrix" "📊" "$PRIORITY_HIGH" "3" "18"
create_task "Apply Six Thinking Hats (Yellow/Black)" "🎩" "$PRIORITY_HIGH" "2" "18"
create_task "Conduct weighted voting by agents" "🗳️" "$PRIORITY_HIGH" "3" "19"
create_task "Identify top 3 solutions with scores" "🏆" "$PRIORITY_HIGH" "2" "19"

# ==============================================================================
# PHASE 6: Consensus Voting (Days 20-21)
# ==============================================================================
echo "Creating Phase 6: Consensus Voting..."
create_card "P06 ── Phase 6: Consensus Voting (Multi-Model + Human)" "🗳️" "$PRIORITY_HIGH" "8" "21"
create_task "Collect votes from BACON-AI agents" "🤖" "$PRIORITY_HIGH" "2" "20"
create_task "Consult external AI models" "🌐" "$PRIORITY_HIGH" "2" "20"
create_task "Get human vote (final authority)" "👤" "$PRIORITY_HIGH" "1" "21"
create_task "Calculate consensus percentage" "📊" "$PRIORITY_HIGH" "1" "21"
create_task "Apply decision rules" "📋" "$PRIORITY_MEDIUM" "2" "21"

# ==============================================================================
# PHASE 7: Design Excellence (Days 22-25)
# ==============================================================================
echo "Creating Phase 7: Design Excellence..."
create_card "P07 ── Phase 7: Design Excellence (Architecture)" "🏗️" "$PRIORITY_HIGH" "16" "25"
create_task "Create Architecture Decision Records" "📄" "$PRIORITY_HIGH" "4" "22"
create_task "Draw system architecture diagrams" "📐" "$PRIORITY_HIGH" "4" "23"
create_task "Define component responsibilities" "🧩" "$PRIORITY_HIGH" "3" "24"
create_task "Identify design patterns to apply" "🔧" "$PRIORITY_MEDIUM" "3" "24"
create_task "Specify quality attributes" "⭐" "$PRIORITY_MEDIUM" "2" "25"

# ==============================================================================
# PHASE 8: Implementation Planning (Days 26-28)
# ==============================================================================
echo "Creating Phase 8: Implementation Planning..."
create_card "P08 ── Phase 8: Implementation Planning (Execution)" "📋" "$PRIORITY_HIGH" "12" "28"
create_task "Create Work Breakdown Structure" "📝" "$PRIORITY_HIGH" "3" "26"
create_task "Create dependency graph (Gantt)" "📊" "$PRIORITY_HIGH" "3" "26"
create_task "Allocate resources (team, tools)" "👥" "$PRIORITY_HIGH" "2" "27"
create_task "Document risk mitigation plan" "⚠️" "$PRIORITY_MEDIUM" "2" "27"
create_task "Define success criteria & acceptance" "✅" "$PRIORITY_HIGH" "2" "28"

# ==============================================================================
# PHASE 9: TDD Build (Days 29-42 - 2 weeks)
# ==============================================================================
echo "Creating Phase 9: TDD Build..."
create_card "P09 ── Phase 9: TDD Build (Test-Driven Development)" "🧪" "$PRIORITY_HIGH" "80" "42"
create_task "Establish test baseline" "📊" "$PRIORITY_HIGH" "4" "29"
create_task "RED: Write failing tests first" "🔴" "$PRIORITY_HIGH" "24" "35"
create_task "GREEN: Write code to pass tests" "🟢" "$PRIORITY_HIGH" "32" "40"
create_task "REFACTOR: Improve code quality" "🔵" "$PRIORITY_HIGH" "12" "42"
create_task "V-Model progression (TUT→FUT→SIT→UAT)" "📈" "$PRIORITY_HIGH" "6" "42"
create_task "Verify >90% code coverage" "✅" "$PRIORITY_MEDIUM" "2" "42"

# ==============================================================================
# PHASE 10: Change Management (Days 43-46)
# ==============================================================================
echo "Creating Phase 10: Change Management..."
create_card "P10 ── Phase 10: Change Management (User Adoption)" "📣" "$PRIORITY_MEDIUM" "16" "46"
create_task "Create user training materials" "📚" "$PRIORITY_MEDIUM" "4" "43"
create_task "Prepare demo video/walkthrough" "🎬" "$PRIORITY_MEDIUM" "4" "44"
create_task "Set up feedback collection" "💬" "$PRIORITY_MEDIUM" "2" "44"
create_task "Execute communication plan" "📢" "$PRIORITY_MEDIUM" "3" "45"
create_task "Track adoption metrics" "📊" "$PRIORITY_MEDIUM" "3" "46"

# ==============================================================================
# PHASE 11: Deployment (Days 47-49)
# ==============================================================================
echo "Creating Phase 11: Deployment..."
create_card "P11 ── Phase 11: Deployment (Production Rollout)" "🚀" "$PRIORITY_HIGH" "12" "49"
create_task "Complete pre-deployment checklist" "📋" "$PRIORITY_HIGH" "2" "47"
create_task "Run deployment automation" "⚙️" "$PRIORITY_HIGH" "2" "47"
create_task "Execute health checks" "🏥" "$PRIORITY_HIGH" "2" "48"
create_task "Verify monitoring and alerting" "📡" "$PRIORITY_HIGH" "2" "48"
create_task "Run smoke tests in production" "🧪" "$PRIORITY_HIGH" "2" "49"
create_task "Get UAT approval" "✔️" "$PRIORITY_HIGH" "2" "49"

# ==============================================================================
# PHASE 12: SSC Retrospective (Days 50-52)
# ==============================================================================
echo "Creating Phase 12: SSC Retrospective..."
create_card "P12 ── Phase 12: SSC Retrospective (Learning)" "🔄" "$PRIORITY_HIGH" "12" "52"
create_task "Collect human feedback" "👤" "$PRIORITY_HIGH" "2" "50"
create_task "Run agent SSC (Stop/Start/Continue)" "🤖" "$PRIORITY_HIGH" "2" "50"
create_task "Update SE-Agent trajectory memory" "🧠" "$PRIORITY_HIGH" "2" "51"
create_task "Add lessons to database (min 3)" "📚" "$PRIORITY_HIGH" "2" "51"
create_task "Document proven patterns (min 4)" "📝" "$PRIORITY_MEDIUM" "2" "51"
create_task "Assess organizational impact" "📊" "$PRIORITY_MEDIUM" "1" "52"
create_task "Execute dissemination plan" "📣" "$PRIORITY_MEDIUM" "1" "52"

echo ""
echo "=== All BACON-AI Tasks Created Successfully ==="
echo ""
FINAL_TASK=$((TASK_NUM - 1))
echo "Summary:"
echo "  - 13 Phase headers (P00-P12)"
echo "  - ${FINAL_TASK} Task items (T001-T$(printf '%03d' $FINAL_TASK))"
echo "  - Project duration: 52 days (~10 weeks)"
echo "  - Total estimated hours: ~260 hours"
echo ""
echo "Naming Convention:"
echo "  P00-P12: Phase headers (sort alphabetically before T*)"
echo "  T001-T${FINAL_TASK}: Sequential task numbers"
echo ""
echo "View in Focalboard at: http://localhost:8000"
