SPRINT 3 WEEK 1 RUNTIME

Run from the repository root using Python 3.10+:

    $env:PYTHONPATH = 'src'
    python -m sprint3_runtime health
    python -m sprint3_runtime deploy
    python -m sprint3_runtime worker

To rerun the actual-engine validation suite (with a fresh isolated database):

    python -m sprint3_runtime demo --date 2026-11-26

The suite deploys the current Sprint 3 resources and creates real process
instances. It completes human tasks through REST. Its output is separate from
manual Tasklist UI evidence and does not overwrite the manual walkthrough DB.

Use the already configured Camunda engine. This package does not install or
start the engine. Run-Sprint3.cmd at the repository root provides the manual
demonstration entry point when the engine package is available.

Models and forms: models/sprint3/execution-manifest.json.
Database: work/sprint3-runtime.sqlite3. Optional --db, --url and --manifest
arguments go before the subcommand. All commands and workers in one exercise
must use the same database. Use a fresh database when the engine is reset.

Sprint 3 process IDs end in _S3; messages start with 'S3 '; service job types
are desd.s3.business and desd.s3.message. Sprint 2 files and deployments retain
their original contracts. An S3 worker does not consume Sprint 2 jobs.

In another terminal while the worker runs:

    python -m sprint3_runtime start-f1 --date 2026-11-26

Complete Submit product details in actual Tasklist. For certification recovery,
submit an organic claim with certificate reference DEMO-UNAVAILABLE. Marketplace
then creates Review pending verification, a real user task. In that task select
retry and a named simulated result, or cancel. Retry returns to the verification
service task; it does not bypass validation or directly publish. Cancel closes
the follow-up and ends without publication. Follow-up events are stored.

After publication, use the product ID returned by the start command:

    python -m sprint3_runtime start-f2 --date 2026-11-26 --product-id PRODUCT-ID

Complete the actual stock form, then inspect:

    python -m sprint3_runtime inspect

Missing product and owner mismatch now return context_rejected through an
actual cross-pool message. They clear any supplied old product/stock context.
Producer does not enter the stock form after rejection. Invalid integration
contracts and corrupt stored data remain technical incidents requiring repair.
These ownership checks use supplied classroom identity; they do not provide
production authentication or prevent forgery of a trusted caller's identity.

Other commands:

    python -m sprint3_runtime tasks --instance-key INSTANCE-KEY
    python -m sprint3_runtime sample --date 2026-11-26
    python -m sprint3_runtime seed --date 2026-11-26
    python -m sprint3_runtime order --date 2026-11-26 --deduction 2 --change-id ORDER-ID
    python -m sprint3_runtime season --date 2026-12-01

REST completion of a review user task is also explicit:

    python -m sprint3_runtime follow-up-complete --task-key TASK-KEY --decision retry --outcome verified --notes 'Actual observation'

This command is API interaction with a real user task, not a manual Tasklist UI
recording. Use Tasklist to verify the form itself.

Delivery observations and recovery:

    python -m sprint3_runtime outbox

The worker commits a message intent before publication, records in_flight,
and records accepted after the broker returns success. Replaying an accepted
send job does not publish again. A lost response or crash before accepted is
recorded leaves an uncertain/in_flight record and a visible incident. The
worker does not infer acceptance from an HTTP 400 or blindly resend. An
operator must inspect the receiving process/transport evidence, then record
the actual decision:

    python -m sprint3_runtime reconcile-message --operation-id job:JOB-KEY --resolution accepted --evidence 'Verified receiver instance and matching request'

Use --resolution not_sent only after verifying it was not accepted. Then repair
and resolve the engine incident in Operate. Reconciliation does not itself
resolve the engine incident. There is no global exactly-once transaction across
SQLite and Camunda. The operation journal protects replay of committed local
business writes; transport ambiguity remains an explicit operational decision.

Certification is still a local fixture: DEMO-VALID / DEMO-INVALID /
DEMO-UNAVAILABLE, optionally overridden by an explicit follow-up result.
No real certification authority is called. Confirmed order and producer identity
are supplied demonstration inputs. Seasonal checks use explicit invocation.
Stock units, inclusive date boundaries and explicit businessDate reuse the
Sprint 2 business policies. Category-specific food-information rules, production
identity, automated seasonal scheduling and broader external integrations remain
separate decisions. See the actual Sprint 3 evidence for tested execution scope.
