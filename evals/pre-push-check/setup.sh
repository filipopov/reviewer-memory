#!/usr/bin/env bash
# A repo whose main branch follows the team rules, and a feature branch with one commit to check:
# FeeCalculator breaks R01 (Instant.now()) and R02 (double money), PaymentService breaks R03 (logs the whole
# request incl. IBANs and names), and the PaymentController change is compliant (R04 must not be flagged).
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
git init -q -b main .
git config core.autocrlf false
git config user.email dev@example.com
git config user.name dev
cp -R "$HERE/fixture/base/." .
git add -A && git commit -qm "Payments service"
git checkout -qb feature/fees
cp -R "$HERE/fixture/change/." .
git add -A && git commit -qm "Add weekend fees"
