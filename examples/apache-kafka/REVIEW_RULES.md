# Review rules

Learned from 750 review comments on 228 PRs in apache/kafka (2026-10-29 – 2026-11-23) by reviewer-memory.
Edit freely: these are the team's rules now, not the tool's.

## R01 · Tests must fail without the fix
- **Rule:** Every new or changed test must fail when the production change is reverted. Set up state (configs, existing groups, mutable inputs, non-default flags) so the bug path is actually reached.
- **Why:** Reviewers repeatedly reverted the fix locally and found the new tests still passed, e.g. a non-transactional store where READ_COMMITTED and READ_UNCOMMITTED see the same data, or an immutable input that makes a defensive-copy test vacuous.
- **Applies to:** `**/src/test/**`
- **Look for:** Tests that only assert "nothing crashed"; tests whose setup bypasses the changed branch (new group instead of existing one, feature flag off, mock that fails regardless of version); `assertNotSame`-style checks that always hold; immutable `Map.of`/`Set.of` inputs passed to copy-semantics tests.
- **Severity:** must
- **Evidence:** 12 comments, e.g. [#24071](https://github.com/apache/kafka/pull/24071#discussion_r4615842191), [#24253](https://github.com/apache/kafka/pull/24253#discussion_r4600361195), [#24319](https://github.com/apache/kafka/pull/24319#discussion_r4644420594), [#22864](https://github.com/apache/kafka/pull/22864#discussion_r4524304955), [#23688](https://github.com/apache/kafka/pull/23688#discussion_r4585079887), [#23507](https://github.com/apache/kafka/pull/23507#discussion_r4459310697), [#22155](https://github.com/apache/kafka/pull/22155#discussion_r4585931776), [#24002](https://github.com/apache/kafka/pull/24002#discussion_r4540249481)

## R02 · Cover every new branch, including error and edge paths
- **Rule:** Add tests for each new branch the change introduces: error/rethrow paths, sentinel values, empty vs. non-empty, the "other" group type or config value, and the exact scenario from the JIRA.
- **Why:** Only the happy path is usually tested; reviewers ask for the failure path that keeps a fix narrow, the second loop iteration, or the case described in the ticket.
- **Applies to:** `**/src/test/**`
- **Look for:** A new `if`/`catch`/`switch` arm in main code with no test touching it; a PR fixing a JIRA scenario whose tests use a simpler scenario; only one partition/member/entry per test when the logic iterates.
- **Severity:** should
- **Evidence:** 9 comments, e.g. [#24193](https://github.com/apache/kafka/pull/24193#discussion_r4611580353), [#24002](https://github.com/apache/kafka/pull/24002#discussion_r4540249514), [#22423](https://github.com/apache/kafka/pull/22423#discussion_r4424573379), [#24113](https://github.com/apache/kafka/pull/24113#discussion_r4513043629), [#24121](https://github.com/apache/kafka/pull/24121#discussion_r4553547227), [#23859](https://github.com/apache/kafka/pull/23859#discussion_r4541883345), [#24247](https://github.com/apache/kafka/pull/24247#discussion_r4631532180)

## R03 · Assert the whole result in one assertion
- **Rule:** Assert complete responses, records, assignments and lists with a single `assertEquals` against an expected object, rather than checking individual fields or skipping the response.
- **Why:** Partial assertions miss regressions (e.g. a member's epoch or assignment that is never checked); whole-object assertions also document the expected state.
- **Applies to:** `**/src/test/**/*.java`, `**/src/test/**/*.scala`
- **Look for:** Multiple `assertEquals` on fields of the same object; `.isEmpty()` checks where `assertEquals(Map.of(), …)` works; unverified return values of `processTasks()`/heartbeats; delete/alter tests that don't verify the side effect happened.
- **Severity:** should
- **Evidence:** 7 comments, e.g. [#24315](https://github.com/apache/kafka/pull/24315#discussion_r4640986424), [#24071](https://github.com/apache/kafka/pull/24071#discussion_r4615842531), [#23530](https://github.com/apache/kafka/pull/23530#discussion_r4513077240), [#24113](https://github.com/apache/kafka/pull/24113#discussion_r4513043635), [#23688](https://github.com/apache/kafka/pull/23688#discussion_r4585079933), [#24065](https://github.com/apache/kafka/pull/24065#discussion_r4438290156)

## R04 · Use JUnit parameterization instead of loops or copy-pasted tests
- **Rule:** When tests differ only by input, use `@ParameterizedTest` with `@EnumSource`, `@ValueSource`, `@CsvSource` or `@MethodSource`, not a loop over a list or near-identical test methods.
- **Why:** Each case is reported separately, and duplication goes away.
- **Applies to:** `**/src/test/**`
- **Look for:** `for` loops over test inputs inside a `@Test`; two or more test methods whose bodies differ by one value or call; iterating `Enum.values()` inside a test.
- **Severity:** should
- **Evidence:** 7 comments, e.g. [#24338](https://github.com/apache/kafka/pull/24338#discussion_r4664409410), [#24247](https://github.com/apache/kafka/pull/24247#discussion_r4629235818), [#24252](https://github.com/apache/kafka/pull/24252#discussion_r4585655849), [#24023](https://github.com/apache/kafka/pull/24023#discussion_r4457983950), [#24015](https://github.com/apache/kafka/pull/24015#discussion_r4420791462), [#24204](https://github.com/apache/kafka/pull/24204#discussion_r4568127411)

## R05 · New integration tests go in Java `@ClusterTest`s in the right module
- **Rule:** Write new integration tests in Java with `@ClusterTest`, in `clients-integration-tests`, `server` or the owning module, not in Scala `core` tests. Don't use Scala `TestUtils` from Java tests.
- **Why:** The project is migrating off Scala and `core`; new Scala-coupled tests add migration work.
- **Applies to:** `core/src/test/**`, `**/src/test/**/*.java`
- **Look for:** New test methods in `core/src/test/scala/**`; `import kafka.utils.TestUtils` in a Java file; new Java tests under `core/` that don't depend on core; mock-heavy unit tests where reviewers want a real cluster check.
- **Severity:** should
- **Evidence:** 6 comments, e.g. [#24065](https://github.com/apache/kafka/pull/24065#discussion_r4434877800), [#24295](https://github.com/apache/kafka/pull/24295#discussion_r4614245410), [#24295](https://github.com/apache/kafka/pull/24295#discussion_r4614233338), [#23489](https://github.com/apache/kafka/pull/23489#discussion_r4645362360), [#24141](https://github.com/apache/kafka/pull/24141#discussion_r4578825698), [#24327](https://github.com/apache/kafka/pull/24327#discussion_r4663613686)

## R06 · Reuse existing test helpers; extract repeated setup
- **Rule:** Before adding a test helper, check the test class, its `*TestContext`, and shared test utils for an existing one. Extract setup repeated three or more times into a helper or `@AfterEach`.
- **Why:** Reviewers keep finding new helpers that duplicate existing ones (often AI-generated), and repeated blocks across tests.
- **Applies to:** `**/src/test/**`
- **Look for:** New private helpers whose bodies match an existing helper; the same anonymous class or `try/finally` block copied into several tests; helpers in a test class that belong in `GroupMetadataManagerTestContext` or a shared fixture.
- **Severity:** should
- **Evidence:** 8 comments, e.g. [#24187](https://github.com/apache/kafka/pull/24187#discussion_r4544740731), [#24187](https://github.com/apache/kafka/pull/24187#discussion_r4544666278), [#24305](https://github.com/apache/kafka/pull/24305#discussion_r4621053109), [#24240](https://github.com/apache/kafka/pull/24240#discussion_r4598172664), [#24240](https://github.com/apache/kafka/pull/24240#discussion_r4598172660), [#24133](https://github.com/apache/kafka/pull/24133#discussion_r4538276059), [#24092](https://github.com/apache/kafka/pull/24092#discussion_r4482341565)

## R07 · Keep test setup minimal and explicit
- **Rule:** Don't change defaults in shared test contexts. Set the config explicitly in the tests that need it, and drop setup the test doesn't need: an unused `ClusterInstance`, an extra consumer, `MockitoExtension` with no mocks, properties already in `@ClusterTestDefaults`.
- **Why:** Hidden defaults make tests run in a mode that nothing in the test shows. Unneeded setup hides what the test is about.
- **Applies to:** `**/src/test/**`
- **Look for:** Edits to `*TestContext` builders that change a config default; unused `ClusterInstance cluster` parameters; redundant `serverProperties`; `@ExtendWith(MockitoExtension.class)` without `@Mock`.
- **Severity:** should
- **Evidence:** 7 comments, e.g. [#23688](https://github.com/apache/kafka/pull/23688#discussion_r4585079896), [#23994](https://github.com/apache/kafka/pull/23994#discussion_r4597121638), [#23994](https://github.com/apache/kafka/pull/23994#discussion_r4438063537), [#22252](https://github.com/apache/kafka/pull/22252#discussion_r4477531353), [#22992](https://github.com/apache/kafka/pull/22992#discussion_r4597861989), [#24071](https://github.com/apache/kafka/pull/24071#discussion_r4615842327)

## R08 · One scenario per test, and use `assertThrows` with exact types
- **Rule:** Use `assertThrows` (and check the message or exact class when it matters) instead of `try { …; fail(); } catch`. Split independent scenarios into separate tests so one failure doesn't hide another.
- **Why:** `assertThrows` with a supertype passes on the wrong exception. Combined tests stop at the first failure.
- **Applies to:** `**/src/test/**/*.java`
- **Look for:** `fail(` inside `try` blocks; `assertThrows(SuperType.class, …)` where a subtype could also be thrown; one test method exercising two unrelated APIs.
- **Severity:** should
- **Evidence:** 8 comments, e.g. [#24336](https://github.com/apache/kafka/pull/24336#discussion_r4670104681), [#24022](https://github.com/apache/kafka/pull/24022#discussion_r4432248088), [#24112](https://github.com/apache/kafka/pull/24112#discussion_r4493630984), [#24172](https://github.com/apache/kafka/pull/24172#discussion_r4616379816), [#22252](https://github.com/apache/kafka/pull/22252#discussion_r4477557383), [#24069](https://github.com/apache/kafka/pull/24069#discussion_r4455916966), [#24226](https://github.com/apache/kafka/pull/24226#discussion_r4592012403)

## R09 · Comments explain why, not what, and not how callers use it
- **Rule:** Comments and Javadoc should explain intent and non-obvious reasons. Don't restate the code, guess at likelihood, or describe how callers use a class or parameter (that belongs at the call site). Add a short "why" comment for non-obvious choices: a hardcoded value, an error remap, a needed stub, avoiding a for-each loop.
- **Why:** Reviewers repeatedly flag verbose, AI-style comments that restate code or tie a callee to its callers and go stale, and they also ask for the missing "why" on surprising code.
- **Applies to:** `**/*.java`, `**/*.scala`
- **Look for:** Javadoc on a record/param explaining what the caller does with it; comments paraphrasing the next line; repeated method-level comments; hardcoded `false`/magic values or remapped errors with no comment.
- **Severity:** should
- **Evidence:** 14 comments, e.g. [#23969](https://github.com/apache/kafka/pull/23969#discussion_r4594379997), [#23969](https://github.com/apache/kafka/pull/23969#discussion_r4594395283), [#24166](https://github.com/apache/kafka/pull/24166#discussion_r4608059299), [#23790](https://github.com/apache/kafka/pull/23790#discussion_r4546953917), [#24216](https://github.com/apache/kafka/pull/24216#discussion_r4565860133), [#23837](https://github.com/apache/kafka/pull/23837#discussion_r4482345910), [#24166](https://github.com/apache/kafka/pull/24166#discussion_r4608042688), [#24327](https://github.com/apache/kafka/pull/24327#discussion_r4663613652), [#21281](https://github.com/apache/kafka/pull/21281#discussion_r4623901774), [#24028](https://github.com/apache/kafka/pull/24028#discussion_r4448784835)

## R10 · Update Javadoc and docs when behavior changes
- **Rule:** When a change alters what a method, config or tool does, update its Javadoc, scaladoc, config description and surrounding comments in the same PR.
- **Why:** Stale docs ("compares member epoch with group epoch", "prints an error", "returns Empty") were flagged across many PRs.
- **Applies to:** `*`
- **Look for:** Changed method bodies whose Javadoc or `@return` still describes the old behavior; changed semantics (stdout→stderr, nullability, exclusivity of offsets) with no doc diff; outdated field comments next to changed fields.
- **Severity:** should
- **Evidence:** 11 comments, e.g. [#24108](https://github.com/apache/kafka/pull/24108#discussion_r4513055581), [#24321](https://github.com/apache/kafka/pull/24321#discussion_r4643431204), [#24241](https://github.com/apache/kafka/pull/24241#discussion_r4669777350), [#24041](https://github.com/apache/kafka/pull/24041#discussion_r4428171210), [#24085](https://github.com/apache/kafka/pull/24085#discussion_r4481164018), [#23522](https://github.com/apache/kafka/pull/23522#discussion_r4482117333), [#23639](https://github.com/apache/kafka/pull/23639#discussion_r4541207766), [#22467](https://github.com/apache/kafka/pull/22467#discussion_r4541926768)

## R11 · Public API, protocol and config changes must match the KIP and stay compatible
- **Rule:** Public classes, method signatures, error names, config names/docs and message JSON changes must match an accepted KIP. New abstract methods on public interfaces (e.g. `Admin`) need `default` implementations, deprecated overrides need `@Deprecated(since, forRemoval)`, and internal-only constructors/accessors must not be public.
- **Why:** Kafka's public API is governed by KIPs; mismatched names or new public surface trigger KIP requests, and non-default interface methods break third-party implementations with `AbstractMethodError`.
- **Applies to:** `clients/src/main/**`, `**/src/main/resources/common/message/*.json`, `**/*Config.java`
- **Look for:** New `public` classes/methods in `org.apache.kafka.clients`/`common` not in a KIP; names that differ from the KIP text; new abstract interface methods; message JSON field additions; config doc strings that diverge from the KIP table; missing `@Deprecated` on public overrides.
- **Severity:** must
- **Evidence:** 12 comments, e.g. [#22531](https://github.com/apache/kafka/pull/22531#discussion_r4667588017), [#23828](https://github.com/apache/kafka/pull/23828#discussion_r4652239380), [#24261](https://github.com/apache/kafka/pull/24261#discussion_r4666032070), [#23763](https://github.com/apache/kafka/pull/23763#discussion_r4483864295), [#24168](https://github.com/apache/kafka/pull/24168#discussion_r4601227556), [#23115](https://github.com/apache/kafka/pull/23115#discussion_r4526073887), [#24116](https://github.com/apache/kafka/pull/24116#discussion_r4539822448), [#23843](https://github.com/apache/kafka/pull/23843#discussion_r4445444331), [#24248](https://github.com/apache/kafka/pull/24248#discussion_r4582064312)

## R12 · Gate on MetadataVersion and feature levels, with safe fallbacks
- **Rule:** Behavior that depends on a protocol or record version must check the specific capability (`metadataVersion.partitionChangeRecordVersion() >= 3`, finalized feature levels, `latestVersion(false)`), account for unstable API versions, and fall back to a minimum version rather than throwing when a supplier has no value.
- **Why:** Mixed-version clusters and clients that don't negotiate versions break when code assumes the latest MV. A throwing version supplier can drop assignments.
- **Applies to:** `server/**`, `server-common/**`, `metadata/**`, `tools/**`, `transaction-coordinator/**`, `core/**`
- **Look for:** Hardcoded request/record versions; `oldestVersion()`/`latestVersion()` without the unstable flag; tool logic that assumes broker-side features exist; overly broad MV helper names; suppliers without fallback.
- **Severity:** must
- **Evidence:** 8 comments, e.g. [#24005](https://github.com/apache/kafka/pull/24005#discussion_r4429726749), [#24034](https://github.com/apache/kafka/pull/24034#discussion_r4587687011), [#24208](https://github.com/apache/kafka/pull/24208#discussion_r4568559694), [#24208](https://github.com/apache/kafka/pull/24208#discussion_r4621300445), [#23965](https://github.com/apache/kafka/pull/23965#discussion_r4511997043), [#23965](https://github.com/apache/kafka/pull/23965#discussion_r4458026915), [#24000](https://github.com/apache/kafka/pull/24000#discussion_r4421632983), [#21735](https://github.com/apache/kafka/pull/21735#discussion_r4499082245)

## R13 · Call out user-visible behavior changes in the PR description and upgrade notes
- **Rule:** The PR description becomes the commit message. It must list every behavior change, including side effects (dropped sensors, changed retry timing, stdout→stderr, metric semantics), and keep the description in sync with the final diff. User-visible changes also need an upgrade-guide line.
- **Why:** Reviewers repeatedly found behavior changes that weren't in the description, or descriptions that still mentioned removed code.
- **Applies to:** `*`
- **Look for:** Diffs that change defaults, timing, output streams, metric meanings or error codes with no matching PR-description or `docs/**/upgrade.md` change.
- **Severity:** should
- **Evidence:** 8 comments, e.g. [#22423](https://github.com/apache/kafka/pull/22423#discussion_r4424436375), [#23991](https://github.com/apache/kafka/pull/23991#discussion_r4562729624), [#22864](https://github.com/apache/kafka/pull/22864#discussion_r4525986586), [#22992](https://github.com/apache/kafka/pull/22992#discussion_r4566859162), [#24121](https://github.com/apache/kafka/pull/24121#discussion_r4553547254), [#24228](https://github.com/apache/kafka/pull/24228#discussion_r4600733744), [#24070](https://github.com/apache/kafka/pull/24070#discussion_r4514141301)

## R14 · Keep PRs focused and rebased
- **Rule:** Revert unrelated edits, keep changes minimal in files you only touch in passing, rebase on trunk to drop already-merged diffs, and don't duplicate a change that another open PR makes. File follow-up JIRAs for adjacent issues instead.
- **Why:** Unrelated changes make review harder and cause conflicts between parallel PRs.
- **Applies to:** `*`
- **Look for:** Import reshuffles or reformatting in untouched files; behavior-neutral fast paths bundled with a bug fix; diffs identical to recently merged commits; edits overlapping another open PR.
- **Severity:** should
- **Evidence:** 7 comments, e.g. [#22252](https://github.com/apache/kafka/pull/22252#discussion_r4477513548), [#24327](https://github.com/apache/kafka/pull/24327#discussion_r4668205508), [#24239](https://github.com/apache/kafka/pull/24239#discussion_r4667323340), [#24195](https://github.com/apache/kafka/pull/24195#discussion_r4564073388), [#24193](https://github.com/apache/kafka/pull/24193#discussion_r4640842847), [#23803](https://github.com/apache/kafka/pull/23803#discussion_r4561200141), [#23664](https://github.com/apache/kafka/pull/23664#discussion_r4539746351)

## R15 · Log at the right level, with useful and accurate messages
- **Rule:** Keep the exception message (`e.getMessage()`), but don't log full stack traces on paths that repeat per request. Log names, not objects (`assignor.name()`). Avoid doubled periods and duplicate logs. Use WARN for surprising-but-handled races and DEBUG/TRACE for frequent ones. Guard expensive debug messages.
- **Why:** Repeated stack traces flood broker logs, messages that drop the cause hamper debugging, and chatty warnings fire on every emit.
- **Applies to:** `**/src/main/**`
- **Look for:** `log.warn(..., e)` in fetch/heartbeat paths; logs that print an object's `toString` instead of its name; messages ending in `.` before an appended exception message; a WARN inside a per-record loop; a swallowed exception with no log.
- **Severity:** should
- **Evidence:** 12 comments, e.g. [#24172](https://github.com/apache/kafka/pull/24172#discussion_r4642803444), [#24172](https://github.com/apache/kafka/pull/24172#discussion_r4616302714), [#24319](https://github.com/apache/kafka/pull/24319#discussion_r4644420543), [#23688](https://github.com/apache/kafka/pull/23688#discussion_r4586153759), [#23763](https://github.com/apache/kafka/pull/23763#discussion_r4483839057), [#24015](https://github.com/apache/kafka/pull/24015#discussion_r4419046855), [#24106](https://github.com/apache/kafka/pull/24106#discussion_r4513483159), [#24053](https://github.com/apache/kafka/pull/24053#discussion_r4555020864), [#22319](https://github.com/apache/kafka/pull/22319#discussion_r4490566904)

## R16 · No defensive dead code; fail fast on bugs and bad config
- **Rule:** Don't add null checks, `getOrDefault` fallbacks or silent branches for states that can't happen. Let caller bugs surface (e.g. an NPE), validate config strictly instead of downgrading to a log, and end `if/else` chains over types with `else throw new IllegalArgumentException`.
- **Why:** Defensive code hides root causes, and silent fallthrough mis-handles new enum values.
- **Applies to:** `**/src/main/**`
- **Look for:** `if (x == null) return` on non-nullable fields; `getOrDefault` with an illegal default; validation exceptions replaced by warnings; final `else` branches that assume the last type.
- **Severity:** should
- **Evidence:** 7 comments, e.g. [#24256](https://github.com/apache/kafka/pull/24256#discussion_r4636553019), [#24058](https://github.com/apache/kafka/pull/24058#discussion_r4506878813), [#24058](https://github.com/apache/kafka/pull/24058#discussion_r4510853999), [#22513](https://github.com/apache/kafka/pull/22513#discussion_r4667559605), [#23990](https://github.com/apache/kafka/pull/23990#discussion_r4449462798), [#22252](https://github.com/apache/kafka/pull/22252#discussion_r4477540552), [#24247](https://github.com/apache/kafka/pull/24247#discussion_r4629606950)

## R17 · Restore the interrupt flag
- **Rule:** When catching `InterruptedException` (or a broad `Exception` that can include it), call `Thread.currentThread().interrupt()` or rethrow it as an interruption.
- **Why:** Swallowing it hides shutdown requests and can turn into endless retries.
- **Applies to:** `**/src/main/**/*.java`
- **Look for:** `catch (InterruptedException e)` or `catch (Exception e)` around `future.get()` without re-interrupting.
- **Severity:** must
- **Evidence:** 2 comments, [#24098](https://github.com/apache/kafka/pull/24098#discussion_r4497144666), [#24110](https://github.com/apache/kafka/pull/24110#discussion_r4480960383)

## R18 · Single source of truth: reuse existing utilities and constants
- **Rule:** Reuse existing validators, helpers and constants (`Topic.validate`, `UnifiedLog.searchOffsetInLocalLog`, shared metric-name constants) instead of re-implementing them, and don't copy magic numbers into several modules.
- **Why:** Duplicated logic drifts apart. Hardcoded copies weaken tests and invite inconsistency.
- **Applies to:** `**/src/main/**`
- **Look for:** New private validation or parsing that mirrors an existing utility; the same literal constant in more than one module; copied loops from another class; two near-identical private methods.
- **Severity:** should
- **Evidence:** 10 comments, e.g. [#23663](https://github.com/apache/kafka/pull/23663#discussion_r4516062913), [#23663](https://github.com/apache/kafka/pull/23663#discussion_r4646219506), [#24223](https://github.com/apache/kafka/pull/24223#discussion_r4600015208), [#24269](https://github.com/apache/kafka/pull/24269#discussion_r4598100223), [#24078](https://github.com/apache/kafka/pull/24078#discussion_r4464108841), [#24028](https://github.com/apache/kafka/pull/24028#discussion_r4429339351), [#24308](https://github.com/apache/kafka/pull/24308#discussion_r4645180226), [#23843](https://github.com/apache/kafka/pull/23843#discussion_r4445539696), [#23792](https://github.com/apache/kafka/pull/23792#discussion_r4418507340)

## R19 · Apply fixes consistently across sibling implementations
- **Rule:** When fixing consumer, share or streams groups, `kafka-consumer-groups` or `kafka-streams-groups`, a log dump tool or a formatter, apply the same fix, message wording, exception type and tests to the sibling paths, or file a JIRA for them.
- **Why:** Kafka has parallel code paths per group type and per tool, and reviewers expect them to behave the same.
- **Applies to:** `group-coordinator/**`, `tools/**`, `server-common/**`
- **Look for:** A change in `ConsumerGroup*` with no matching `StreamsGroup*`/`ShareGroup*` change; exception messages or types that differ from the sibling's; formatter output that differs between console consumer and `DumpLogSegments`.
- **Severity:** should
- **Evidence:** 9 comments, e.g. [#24030](https://github.com/apache/kafka/pull/24030#discussion_r4426788574), [#24112](https://github.com/apache/kafka/pull/24112#discussion_r4666066836), [#24153](https://github.com/apache/kafka/pull/24153#discussion_r4518288581), [#24172](https://github.com/apache/kafka/pull/24172#discussion_r4642776020), [#24193](https://github.com/apache/kafka/pull/24193#discussion_r4611580332), [#24077](https://github.com/apache/kafka/pull/24077#discussion_r4455223901), [#23514](https://github.com/apache/kafka/pull/23514#discussion_r4641237487), [#23706](https://github.com/apache/kafka/pull/23706#discussion_r4455162312)

## R20 · Assignors must be deterministic
- **Rule:** Comparators used in assignors must end with a unique tie-breaker (e.g. `processId`), and results must not depend on `HashMap` iteration order.
- **Why:** Non-deterministic assignments cause needless task movement and flaky tests.
- **Applies to:** `group-coordinator/src/main/**/assignor/**`, `group-coordinator/src/main/**/streams/**`
- **Look for:** `Comparator.comparing(...)` chains without a final unique key; iteration over `HashMap`/`HashSet` that feeds assignment decisions.
- **Severity:** should
- **Evidence:** 3 comments, [#23482](https://github.com/apache/kafka/pull/23482#discussion_r4438132418), [#24090](https://github.com/apache/kafka/pull/24090#discussion_r4499299381), [#24269](https://github.com/apache/kafka/pull/24269#discussion_r4599403058)

## R21 · Avoid needless work on hot paths
- **Rule:** On heartbeat, fetch, record and restore paths, skip work when it isn't needed (feature disabled, empty set), apply filters where the other filters are applied, avoid per-record copies and allocations, and don't do linear lookups inside loops.
- **Why:** Coordinator and broker paths run per heartbeat or per record, so small costs add up.
- **Applies to:** `group-coordinator/src/main/**`, `streams/src/main/**`, `clients/src/main/**`, `storage/src/main/**`, `tools/src/main/**`
- **Look for:** Iterating all members when a feature flag is off; `Map.copyOf` on non-JDK maps assumed free; header/record copies on every record; `list.contains` inside loops; filtering large group lists after building them.
- **Severity:** should
- **Evidence:** 9 comments, e.g. [#24071](https://github.com/apache/kafka/pull/24071#discussion_r4602076014), [#24195](https://github.com/apache/kafka/pull/24195#discussion_r4551887101), [#22155](https://github.com/apache/kafka/pull/22155#discussion_r4585931767), [#24294](https://github.com/apache/kafka/pull/24294#discussion_r4642935451), [#23638](https://github.com/apache/kafka/pull/23638#discussion_r4614799015), [#22864](https://github.com/apache/kafka/pull/22864#discussion_r4524304613), [#24193](https://github.com/apache/kafka/pull/24193#discussion_r4640843250), [#24239](https://github.com/apache/kafka/pull/24239#discussion_r4653623580)

## R22 · Be explicit about threads and shared state
- **Rule:** Lambdas that run on another thread must capture locals with distinct names, not fields. Shared caches must update related state under the same lock. Fix real concurrency issues instead of adding SpotBugs exclusions.
- **Why:** Shadowed fields read from the wrong thread, and unsynchronized ref-counts close resources still in use, with no test catching either.
- **Applies to:** `**/src/main/**/*.java`
- **Look for:** Locals that shadow fields captured by executor lambdas; counters updated outside the lock that guards the map; new entries in `gradle/spotbugs-exclude.xml`.
- **Severity:** must
- **Evidence:** 4 comments, [#23688](https://github.com/apache/kafka/pull/23688#discussion_r4585079905), [#22759](https://github.com/apache/kafka/pull/22759#discussion_r4644054014), [#24169](https://github.com/apache/kafka/pull/24169#discussion_r4573007204), [#24115](https://github.com/apache/kafka/pull/24115#discussion_r4499295934)

## R23 · Use modern Java idioms
- **Rule:** Prefer switch expressions, `Map.of`/`List.of`/`List.copyOf`, immutable collections for fields that never change, `Map` over `Properties`, `ArgumentCaptor.captor()` over `@SuppressWarnings("unchecked")`, and `StandardCharsets`.
- **Why:** These are shorter and safer, and they are the style reviewers suggest again and again.
- **Applies to:** `**/*.java`
- **Look for:** Long `if/else` or old-style `switch` mapping values; `new ArrayList<>(…)` copies where `List.copyOf` works; `ArgumentCaptor.forClass` with unchecked suppression; `getBytes()` without a charset; new `Properties` usage.
- **Severity:** should
- **Evidence:** 8 comments, e.g. [#23830](https://github.com/apache/kafka/pull/23830#discussion_r4493703441), [#24239](https://github.com/apache/kafka/pull/24239#discussion_r4653575154), [#24071](https://github.com/apache/kafka/pull/24071#discussion_r4615842476), [#24093](https://github.com/apache/kafka/pull/24093#discussion_r4579014282), [#24295](https://github.com/apache/kafka/pull/24295#discussion_r4671299881), [#23663](https://github.com/apache/kafka/pull/23663#discussion_r4651739743), [#23663](https://github.com/apache/kafka/pull/23663#discussion_r4651744468)

## R24 · Formatting: one argument per line, 100-char lines, spotless
- **Rule:** When arguments or parameters don't fit on one line, put each on its own line with the closing parenthesis on its own line. Keep Javadoc lines at 100 characters or fewer, and run `./gradlew spotlessApply`.
- **Why:** This keeps diffs small and readable, and reviewers ask for it consistently.
- **Applies to:** `**/*.java`
- **Look for:** Wrapped argument lists with several arguments per continuation line; Javadoc lines over 100 characters; misordered imports.
- **Severity:** should
- **Evidence:** 7 comments, e.g. [#23514](https://github.com/apache/kafka/pull/23514#discussion_r4641237496), [#24071](https://github.com/apache/kafka/pull/24071#discussion_r4615842399), [#24166](https://github.com/apache/kafka/pull/24166#discussion_r4591807261), [#23924](https://github.com/apache/kafka/pull/23924#discussion_r4560560676), [#23899](https://github.com/apache/kafka/pull/23899#discussion_r4593901500), [#24253](https://github.com/apache/kafka/pull/24253#discussion_r4588399727)

## R25 · Names must say what the thing is and does
- **Rule:** Method and test names must match their behavior: imperative verbs for actions (`move`, not `moved`), counts named as counts, suppliers named `…Supplier`, single-letter generic type parameters, and test names that match the scenario and sibling tests.
- **Why:** Misleading names (e.g. `taskNo` for a count, a supplier named as a version, "expired" for deleteRecords) caused confusion in several reviews.
- **Applies to:** `**/*.java`, `**/*.scala`
- **Look for:** Past-tense method names for mutators; variables holding suppliers without the `Supplier` suffix; descriptive generic names like `<RequestData>`; tests renamed or added whose names don't match what they assert.
- **Severity:** should
- **Evidence:** 9 comments, e.g. [#23924](https://github.com/apache/kafka/pull/23924#discussion_r4560884641), [#23924](https://github.com/apache/kafka/pull/23924#discussion_r4561001627), [#23965](https://github.com/apache/kafka/pull/23965#discussion_r4457883761), [#23965](https://github.com/apache/kafka/pull/23965#discussion_r4458006455), [#24327](https://github.com/apache/kafka/pull/24327#discussion_r4668354152), [#24028](https://github.com/apache/kafka/pull/24028#discussion_r4445610716), [#22864](https://github.com/apache/kafka/pull/22864#discussion_r4524304367), [#24181](https://github.com/apache/kafka/pull/24181#discussion_r4540899027)
