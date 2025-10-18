#!/usr/bin/env bash
set -euo pipefail

# Requires: gh auth login (already set for you)
upsert() { gh label create "$1" --color "$2" --description "$3" 2>/dev/null || gh label edit "$1" --color "$2" --description "$3"; }

upsert "type:bug"        "d73a4a" "Bugs / defects"
upsert "type:feature"    "a2eeef" "Feature requests / enhancements"
upsert "type:chore"      "c5def5" "Refactors, CI, deps, housekeeping"

upsert "priority:high"   "b60205" "Fix soon; blocks important work"
upsert "priority:medium" "fbca04" "Important, not urgent"
upsert "priority:low"    "0e8a16" "Nice to have"

upsert "status:triage"   "cfd3d7" "New issues awaiting triage"
upsert "status:blocked"  "5319e7" "Blocked by external or upstream"
upsert "status:ready"    "36a64f" "Groomed and ready to pick up"
echo "✅ Labels synced."
