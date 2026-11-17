SPRINT 2 CAMUNDA RUNTIME

Current validation — 18 November 2026
The executable models were deployed to local Camunda Run 8.10.9. Seven
real-engine scenarios and two manual Tasklist walkthroughs completed.
See docs/sprint-2/runtime-validation-2026-11-18.md for instances and outcomes.

For the simple Windows walkthrough, double-click Run-Sprint2.cmd at the
repository root. Keep the console open. It starts the installed official
Windows Camunda Run package when needed, deploys the models/Forms, starts F1,
waits for manual Tasklist input, then starts F2. It never completes user tasks.
Default package location:
%USERPROFILE%\Downloads\camunda8-run-8.10-windows-x86_64\c8run-8.10.9
Set CAMUNDA_RUN_DIR if the extracted package is elsewhere. Python 3.10+ is
required. Tasklist/Operate are at http://localhost:8080; local demo login is
demo / demo. Cloud school login is separate.

In Tasklist: Assign to me -> complete F1 with quantity 10 and no organic claim;
then Assign to me -> complete F2 with New quantity 6. The final state is written
to work/manual-demo-latest.json. Read it or inspect the completed instances in
Operate. New runs use unique product/request IDs; do not close a walkthrough
halfway and start another unless you intend to leave the earlier task waiting.

The command-line package below expects an already running engine. Its demo
command includes its own worker; do not run a second worker during that command.

Prerequisites
An accessible Camunda 8.10 engine must already be running. This package does not
install or start Camunda. Python 3.10+ is sufficient; no third-party Python
packages are required. Run commands from the repository root in PowerShell.

    $env:PYTHONPATH = 'src'
    $env:CAMUNDA_REST_URL = 'http://127.0.0.1:8080/v2'

If the selected engine requires authentication, set CAMUNDA_TOKEN, or
CAMUNDA_USERNAME and CAMUNDA_PASSWORD, in your local environment. Do not commit
credentials. The client does not acquire or refresh OAuth tokens itself.

Prepare and deploy
    python -m sprint2_runtime health
    python -m sprint2_runtime deploy

Deploy reads models/operational/execution-manifest.json and sends both BPMN
resources and all three forms in a single request. A successful deployment is
not evidence that a process instance has run successfully.

Real engine exercises
    python -m sprint2_runtime demo --date 2026-11-18 --scenario happy
    python -m sprint2_runtime demo --date 2026-11-18 --scenario correction
    python -m sprint2_runtime demo --date 2026-11-18 --scenario organic
    python -m sprint2_runtime demo --date 2026-11-18 --scenario pending
    python -m sprint2_runtime demo --date 2026-11-18 --scenario invalid-certificate
    python -m sprint2_runtime demo --date 2026-11-18 --scenario invalid-input
    python -m sprint2_runtime demo --date 2026-11-18 --scenario boundaries

Each command creates unique real process instances, activates actual jobs,
completes actual Camunda user tasks through REST, and checks engine completion
and stored results. The demo command drives its own worker. It is bounded by
--timeout (default 90 seconds per awaited step). The JSON result is only printed
as successful when all assertions pass. Worker logs go to stderr. Preserve the
JSON and engine screenshots after a successful run. These commands are not a
recording of someone manually using the forms in Tasklist; check that UI too.

happy: F1 publication followed by F2 producer stock change and availability sync.
correction: invalid F1 details -> correction user task -> resubmit -> publication.
invalid-certificate: DEMO-INVALID -> correction -> DEMO-VALID -> reverification.
invalid-input: negative/fractional stock and reversed dates rejected by services.
organic: explicit DEMO-VALID mock certificate -> publication -> F2 stock change.
pending: DEMO-UNAVAILABLE mock certificate -> persisted follow-up, no publication.
boundaries: happy path, then real F2 order depletion, duplicate-order rejection,
an intervening version change while a producer form is open, conflict follow-up,
successful restock and an out-of-season check while stock is still positive.

Manual Tasklist demonstration
In one terminal:
    python -m sprint2_runtime worker
In another terminal:
    python -m sprint2_runtime start-f1 --date 2026-11-18 --product-id demo-listing-1
Complete the F1 form in Tasklist. Then:
    python -m sprint2_runtime start-f2 --date 2026-11-18 --product-id demo-listing-1
Complete the F2 form in Tasklist. Inspect persisted state:
    python -m sprint2_runtime inspect

start-f2 rejects an unknown product or a mismatched owner before creating a
process. Bypassing that CLI check can still cause an incident at F2_Load. There
is no automatic producer rejection path for a load/configuration failure in
the current model; correct the incident or cancel the affected instances.

Optional F2 preparation and integration messages
    python -m sprint2_runtime seed --date 2026-11-18
    python -m sprint2_runtime order --date 2026-11-18 --deduction 2 --change-id order-1
    python -m sprint2_runtime season --date 2026-12-01

The seed command only creates a SQLite fixture; it does not run Camunda. The
order/season commands publish real engine messages and need an active worker.
They use the current stored version unless --expected-version is provided.
Repeat an order with the same --change-id to exercise duplicate detection.
The default seeded product is demo-carrots, owned by demo-producer.

Storage and reliability
Default database: work/sprint2-runtime.sqlite3 (ignored by Git).
Select another store with --db PATH before the subcommand. Use the same store
for the worker, seed, start-f2, integration commands and inspection. Preserve
that store with the same engine data; a completely reset engine needs a fresh
runtime database because engine job keys may be reused.

SQLite transactions enforce optimistic version checks and persist stock,
publication state and sale availability together. A job-result journal prevents
a retried completed business operation from writing twice. A duplicate order
detected during a competing commit is acknowledged without a second deduction.
The customer availability table is a local projection, not a live customer site.

Transient activation failures use backoff. Authentication/configuration errors
are visible failures. Business contract errors produce zero-retry incidents;
other job failures reduce retries. Sending uses requestId correlation, a one-hour
message TTL and jobKey as messageId. This is not an exactly-once transaction
across SQLite and Camunda: if the broker accepts a message but its response is
lost, a retry may receive a duplicate rejection. The precise HTTP recovery path
must be checked against the running 8.10 engine; ordinary 400 responses are not
treated as success. Do not change requestId while a request is in progress.

Business boundaries
Certification uses explicit mock fixtures: DEMO-VALID, DEMO-INVALID and
DEMO-UNAVAILABLE. Unknown references are invalid in the fixture adapter. No real
certification provider is contacted. --verification-outcome on start-f1 can
select a mock response explicitly.
Producer identity and order confirmation are trusted demo inputs, not identity
authentication or payment verification. Category-specific allergen, harvest and
best-before applicability remains the existing contract's open design question.
businessDate is explicit; inclusive sale-date boundaries and integer stock units
follow the existing sprint2_demo rules. No production timezone policy is assumed.

Validation boundary
    python -m unittest discover -s tests -p 'test_sprint2_runtime*.py' -v

Local tests cover SQLite persistence, concurrent version conflicts, retry
idempotency, duplicate orders, invalid inputs, pending certification, sale dates,
message filtering, explicit incidents and transient activation recovery. They
do not claim engine integration or manual form interaction.

API schemas were checked against the official Camunda docs tag 8.10.16, files
jobs.yaml, messages.yaml, process-instances.yaml, user-tasks.yaml, keys.yaml and
deployments.yaml under:
https://github.com/camunda/camunda-docs/tree/8.10.16/api/camunda/version-8.10

Checked shapes include POST /jobs/activation (requestTimeout=-1), job completion
and failure, message publication, instance creation by processDefinitionId and
version=-1, user-task search filters/items/CREATED, task completion, instance
COMPLETED/hasIncident and multipart resource deployment. Optional job leases are
not requested, so this client does not send a jobLeaseToken. Static schema
agreement is not proof of deployment or execution. Actual engine verification
was captured on 18 November; use the current runtime-validation document for
recorded scope and results.
