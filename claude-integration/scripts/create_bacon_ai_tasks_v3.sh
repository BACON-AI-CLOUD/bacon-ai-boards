#!/bin/bash
# =============================================================================
# BACON-AI 12-Phase Framework Task Creator for Focalboard (v3)
#
# IMPROVED NAMING CONVENTION:
#   Phase headers: "P00 ── Phase 0: Verification"
#   Task items:    "P00-T01 ── Task Description"
#
# This ensures:
#   1. Alphanumeric sorting works: P00 < P00-T01 < P00-T02 < P01 < P01-T01
#   2. Tasks are visually grouped under their parent phase
#   3. Dependencies and relationships are clear
#
# Project Timeline:
#   Start Date: Monday, February 3, 2026
#   Duration: 52 days (~10 weeks)
#   End Date: ~March 27, 2026
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

# Project start date: Monday, February 3, 2026
# Using seconds since epoch for Feb 3, 2026 00:00:00 UTC
PROJECT_START_EPOCH=1738540800

# Current phase for task numbering
CURRENT_PHASE=""
PHASE_TASK_NUM=0
TOTAL_TASKS=0

# Function to calculate due date (days from project start)
calc_due_date() {
    local days=$1
    local timestamp=$(( PROJECT_START_EPOCH + (days * 86400) ))
    echo "{\"from\":${timestamp}000}"
}

# Function to format date for display
format_date() {
    local days=$1
    date -d "@$((PROJECT_START_EPOCH + (days * 86400)))" "+%b %d, %Y"
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

    echo "  ✓ $title"
}

# Function to create a phase header
create_phase() {
    local phase_num="$1"
    local phase_name="$2"
    local icon="$3"
    local hours="$4"
    local due_days="$5"

    CURRENT_PHASE=$(printf "P%02d" $phase_num)
    PHASE_TASK_NUM=0

    local title="${CURRENT_PHASE} ── Phase ${phase_num}: ${phase_name}"
    create_card "$title" "$icon" "$PRIORITY_HIGH" "$hours" "$due_days"
}

# Function to create a task linked to current phase
create_task() {
    local desc="$1"
    local icon="$2"
    local priority="$3"
    local hours="$4"
    local due_days="$5"

    PHASE_TASK_NUM=$((PHASE_TASK_NUM + 1))
    TOTAL_TASKS=$((TOTAL_TASKS + 1))

    local task_id=$(printf "%s-T%02d" "$CURRENT_PHASE" "$PHASE_TASK_NUM")
    local title="${task_id} ── ${desc}"

    create_card "$title" "$icon" "$priority" "$hours" "$due_days"
}

echo "═══════════════════════════════════════════════════════════════════════════"
echo "       BACON-AI 12-Phase Framework Task Creator (v3 - Improved Naming)"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
echo "Project Timeline:"
echo "  Start Date: $(format_date 0)"
echo "  End Date:   $(format_date 52)"
echo "  Duration:   52 days (~10 weeks)"
echo ""
echo "Naming Convention:"
echo "  Phases: P00, P01, P02 ... P12"
echo "  Tasks:  P00-T01, P00-T02, P01-T01, P01-T02 ..."
echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""

# ==============================================================================
# PHASE 0: Verification (Days 0-2)
# ==============================================================================
echo "📍 Creating Phase 0: Verification..."
create_phase 0 "Verification (Critical Pre-Phase)" "🔍" "8" "2"
create_task "Query lessons learned database" "📚" "$PRIORITY_HIGH" "1" "0"
create_task "Web search current best practices" "🌐" "$PRIORITY_HIGH" "2" "1"
create_task "Consult external AI models" "🤖" "$PRIORITY_HIGH" "2" "1"
create_task "Document current state and assumptions" "📝" "$PRIORITY_HIGH" "2" "2"
create_task "Validate problem not already solved" "✅" "$PRIORITY_HIGH" "1" "2"

# ==============================================================================
# PHASE 1: Problem Definition (Days 3-5)
# ==============================================================================
echo "📍 Creating Phase 1: Problem Definition..."
create_phase 1 "Problem Definition (Design Thinking)" "🎯" "12" "5"
create_task "Create empathy map" "💭" "$PRIORITY_HIGH" "3" "3"
create_task "Define problem using 5W+1H framework" "❓" "$PRIORITY_HIGH" "2" "4"
create_task "Apply Six Thinking Hats review" "🎩" "$PRIORITY_HIGH" "2" "4"
create_task "Document success criteria and constraints" "📋" "$PRIORITY_HIGH" "3" "5"
create_task "Get stakeholder approval" "✔️" "$PRIORITY_HIGH" "2" "5"

# ==============================================================================
# PHASE 2: Data Gathering (Days 6-8)
# ==============================================================================
echo "📍 Creating Phase 2: Data Gathering..."
create_phase 2 "Data Gathering (Systems Thinking)" "📊" "16" "8"
create_task "Create context map of system boundaries" "🗺️" "$PRIORITY_HIGH" "3" "6"
create_task "Conduct stakeholder analysis" "👥" "$PRIORITY_HIGH" "3" "6"
create_task "Collect data from all sources" "📥" "$PRIORITY_HIGH" "4" "7"
create_task "Review existing documentation" "📖" "$PRIORITY_HIGH" "4" "8"
create_task "Identify data gaps and plan collection" "🔎" "$PRIORITY_HIGH" "2" "8"

# ==============================================================================
# PHASE 3: Analysis (Days 9-12)
# ==============================================================================
echo "📍 Creating Phase 3: Analysis..."
create_phase 3 "Analysis (TRIZ + Systems Thinking)" "🔬" "20" "12"
create_task "Create causal loop diagrams" "🔄" "$PRIORITY_HIGH" "4" "9"
create_task "Apply TRIZ contradiction matrix" "⚡" "$PRIORITY_HIGH" "4" "10"
create_task "Identify patterns from data" "🔍" "$PRIORITY_HIGH" "4" "11"
create_task "Deep analysis (mindmaps, diagrams)" "🧠" "$PRIORITY_HIGH" "6" "12"
create_task "QA review with confidence levels" "✅" "$PRIORITY_MEDIUM" "2" "12"

# ==============================================================================
# PHASE 4: Solution Generation (Days 13-16)
# ==============================================================================
echo "📍 Creating Phase 4: Solution Generation..."
create_phase 4 "Solution Generation (TRIZ 40 Principles)" "💡" "16" "16"
create_task "Apply TRIZ 40 Inventive Principles" "🛠️" "$PRIORITY_HIGH" "4" "13"
create_task "Parallel agent generation (5-10 agents)" "🤖" "$PRIORITY_HIGH" "4" "14"
create_task "Collective discussion for more ideas" "💬" "$PRIORITY_HIGH" "3" "15"
create_task "Compile master solution list (min 20)" "📝" "$PRIORITY_HIGH" "3" "16"
create_task "Enforce NO EVALUATION rule" "🚫" "$PRIORITY_MEDIUM" "2" "16"

# ==============================================================================
# PHASE 5: Evaluation (Days 17-19)
# ==============================================================================
echo "📍 Creating Phase 5: Evaluation..."
create_phase 5 "Evaluation (Multi-Criteria Analysis)" "⚖️" "12" "19"
create_task "Apply feasibility filtering" "🔍" "$PRIORITY_HIGH" "2" "17"
create_task "Create multi-criteria scoring matrix" "📊" "$PRIORITY_HIGH" "3" "18"
create_task "Apply Six Thinking Hats (Yellow/Black)" "🎩" "$PRIORITY_HIGH" "2" "18"
create_task "Conduct weighted voting by agents" "🗳️" "$PRIORITY_HIGH" "3" "19"
create_task "Identify top 3 solutions with scores" "🏆" "$PRIORITY_HIGH" "2" "19"

# ==============================================================================
# PHASE 6: Consensus Voting (Days 20-21)
# ==============================================================================
echo "📍 Creating Phase 6: Consensus Voting..."
create_phase 6 "Consensus Voting (Multi-Model + Human)" "🗳️" "8" "21"
create_task "Collect votes from BACON-AI agents" "🤖" "$PRIORITY_HIGH" "2" "20"
create_task "Consult external AI models" "🌐" "$PRIORITY_HIGH" "2" "20"
create_task "Get human vote (final authority)" "👤" "$PRIORITY_HIGH" "1" "21"
create_task "Calculate consensus percentage" "📊" "$PRIORITY_HIGH" "1" "21"
create_task "Apply decision rules" "📋" "$PRIORITY_MEDIUM" "2" "21"

# ==============================================================================
# PHASE 7: Design Excellence (Days 22-25)
# ==============================================================================
echo "📍 Creating Phase 7: Design Excellence..."
create_phase 7 "Design Excellence (Architecture)" "🏗️" "16" "25"
create_task "Create Architecture Decision Records" "📄" "$PRIORITY_HIGH" "4" "22"
create_task "Draw system architecture diagrams" "📐" "$PRIORITY_HIGH" "4" "23"
create_task "Define component responsibilities" "🧩" "$PRIORITY_HIGH" "3" "24"
create_task "Identify design patterns to apply" "🔧" "$PRIORITY_MEDIUM" "3" "24"
create_task "Specify quality attributes" "⭐" "$PRIORITY_MEDIUM" "2" "25"

# ==============================================================================
# PHASE 8: Implementation Planning (Days 26-28)
# ==============================================================================
echo "📍 Creating Phase 8: Implementation Planning..."
create_phase 8 "Implementation Planning (Execution)" "📋" "12" "28"
create_task "Create Work Breakdown Structure" "📝" "$PRIORITY_HIGH" "3" "26"
create_task "Create dependency graph (Gantt)" "📊" "$PRIORITY_HIGH" "3" "26"
create_task "Allocate resources (team, tools)" "👥" "$PRIORITY_HIGH" "2" "27"
create_task "Document risk mitigation plan" "⚠️" "$PRIORITY_MEDIUM" "2" "27"
create_task "Define success criteria & acceptance" "✅" "$PRIORITY_HIGH" "2" "28"

# ==============================================================================
# PHASE 9: TDD Build (Days 29-42 - 2 weeks)
# ==============================================================================
echo "📍 Creating Phase 9: TDD Build..."
create_phase 9 "TDD Build (Test-Driven Development)" "🧪" "80" "42"
create_task "Establish test baseline" "📊" "$PRIORITY_HIGH" "4" "29"
create_task "RED: Write failing tests first" "🔴" "$PRIORITY_HIGH" "24" "35"
create_task "GREEN: Write code to pass tests" "🟢" "$PRIORITY_HIGH" "32" "40"
create_task "REFACTOR: Improve code quality" "🔵" "$PRIORITY_HIGH" "12" "42"
create_task "V-Model progression (TUT→FUT→SIT→UAT)" "📈" "$PRIORITY_HIGH" "6" "42"
create_task "Verify >90% code coverage" "✅" "$PRIORITY_MEDIUM" "2" "42"

# ==============================================================================
# PHASE 10: Change Management (Days 43-46)
# ==============================================================================
echo "📍 Creating Phase 10: Change Management..."
create_phase 10 "Change Management (User Adoption)" "📣" "16" "46"
create_task "Create user training materials" "📚" "$PRIORITY_MEDIUM" "4" "43"
create_task "Prepare demo video/walkthrough" "🎬" "$PRIORITY_MEDIUM" "4" "44"
create_task "Set up feedback collection" "💬" "$PRIORITY_MEDIUM" "2" "44"
create_task "Execute communication plan" "📢" "$PRIORITY_MEDIUM" "3" "45"
create_task "Track adoption metrics" "📊" "$PRIORITY_MEDIUM" "3" "46"

# ==============================================================================
# PHASE 11: Deployment (Days 47-49)
# ==============================================================================
echo "📍 Creating Phase 11: Deployment..."
create_phase 11 "Deployment (Production Rollout)" "🚀" "12" "49"
create_task "Complete pre-deployment checklist" "📋" "$PRIORITY_HIGH" "2" "47"
create_task "Run deployment automation" "⚙️" "$PRIORITY_HIGH" "2" "47"
create_task "Execute health checks" "🏥" "$PRIORITY_HIGH" "2" "48"
create_task "Verify monitoring and alerting" "📡" "$PRIORITY_HIGH" "2" "48"
create_task "Run smoke tests in production" "🧪" "$PRIORITY_HIGH" "2" "49"
create_task "Get UAT approval" "✔️" "$PRIORITY_HIGH" "2" "49"

# ==============================================================================
# PHASE 12: SSC Retrospective (Days 50-52)
# ==============================================================================
echo "📍 Creating Phase 12: SSC Retrospective..."
create_phase 12 "SSC Retrospective (Learning)" "🔄" "12" "52"
create_task "Collect human feedback" "👤" "$PRIORITY_HIGH" "2" "50"
create_task "Run agent SSC (Stop/Start/Continue)" "🤖" "$PRIORITY_HIGH" "2" "50"
create_task "Update SE-Agent trajectory memory" "🧠" "$PRIORITY_HIGH" "2" "51"
create_task "Add lessons to database (min 3)" "📚" "$PRIORITY_HIGH" "2" "51"
create_task "Document proven patterns (min 4)" "📝" "$PRIORITY_MEDIUM" "2" "51"
create_task "Assess organizational impact" "📊" "$PRIORITY_MEDIUM" "1" "52"
create_task "Execute dissemination plan" "📣" "$PRIORITY_MEDIUM" "1" "52"

echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo "                          CREATION COMPLETE!"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
echo "Summary:"
echo "  • 13 Phase headers (P00-P12)"
echo "  • ${TOTAL_TASKS} Task items"
echo "  • Project duration: 52 days (~10 weeks)"
echo "  • Total estimated hours: ~260 hours"
echo ""
echo "Naming Convention Examples:"
echo "  P00 ── Phase 0: Verification"
echo "    P00-T01 ── Query lessons learned database"
echo "    P00-T02 ── Web search current best practices"
echo "  P01 ── Phase 1: Problem Definition"
echo "    P01-T01 ── Create empathy map"
echo "    P01-T02 ── Define problem using 5W+1H framework"
echo ""
echo "View in Focalboard at: http://localhost:8000"
echo ""
