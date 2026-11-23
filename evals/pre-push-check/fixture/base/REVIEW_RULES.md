# Review rules

Learned from 214 review comments on 87 PRs in acme/payments (2026-01-01 – 2026-10-31) by reviewer-memory.
Edit freely: these are the team's rules now, not the tool's.

## R01 · Inject the clock
- **Rule:** Production code gets the current time from an injected `java.time.Clock`; never `Instant.now()`, `LocalDate.now()` or `System.currentTimeMillis()` directly.
- **Why:** Cut-off and fee logic must be testable at fixed times; two incidents came from untestable month-end code.
- **Applies to:** `src/main/**/*.java`
- **Look for:** `Instant.now()`, `LocalDate.now()`, `LocalDateTime.now()`, `System.currentTimeMillis()` without a `Clock` argument.
- **Severity:** must
- **Evidence:** 19 comments

## R02 · Money is BigDecimal
- **Rule:** Amounts, fees and rates are `BigDecimal` with an explicit scale and `RoundingMode`; never `double` or `float`.
- **Why:** Binary floating point loses cents; reconciliation flagged rounding drift.
- **Applies to:** `src/main/**/*.java`
- **Look for:** `double`/`float` fields, parameters or returns for amounts, fees, rates; `BigDecimal.valueOf(double)` on computed values; `setScale` without a `RoundingMode`.
- **Severity:** must
- **Evidence:** 23 comments

## R03 · Log ids, not customer data
- **Rule:** Log identifiers (payment id, account id); never whole request/response objects, IBANs or names.
- **Why:** Logs are shipped to a shared platform without PII clearance.
- **Applies to:** `src/main/**/*.java`
- **Look for:** Logging a DTO/request object (its `toString()` contains IBANs and names), or IBAN/name fields directly.
- **Severity:** must
- **Evidence:** 11 comments

## R04 · Controllers talk to services
- **Rule:** REST controllers call services only; never repositories directly.
- **Why:** Validation and transactions live in the service layer.
- **Applies to:** `src/main/**/*Controller.java`
- **Look for:** A `*Repository` field or call in a controller.
- **Severity:** should
- **Evidence:** 8 comments
