# Sprint 3 — week one technical baseline

This iteration extends product listing and inventory management. Sprint 2 models, code and dated evidence remain unchanged. Use the resources under `models/sprint3/` and the `sprint3_runtime` package for this iteration.

## Start and demonstrate

Python 3.10+ and the configured Camunda Run 8.10.9 installation are required. Double-click `Run-Sprint3.cmd` on the configured Windows computer. It deploys both processes and all four Forms, starts the worker and waits for actual Tasklist input. Login to local Tasklist with the configured demo account. Complete product submission, then change the new stock task from 10 to 6. Inspect completed instances in Operate and `work/sprint3-manual-latest.json`.

To include the verification follow-up form:

```powershell
$env:PYTHONPATH = 'src'
python tools/run_sprint3_manual.py --pending
```

Submit the simulated organic claim `DEMO-UNAVAILABLE`. The marketplace creates a verification follow-up user task. Select retry with a controlled simulated provider result, or cancel. Retry invokes verification again; cancellation closes the request without publication. An invalid retry still requires producer correction.

For CLI usage, variables, message recovery and configuration, see [runtime instructions](../../src/sprint3_runtime/README.txt).

## Week-one behaviour

- F1 records the pending follow-up, its responsible business role, timestamps and state transitions. Successful reverification/publication resolves it; cancellation closes it without creating a published product.
- F2 missing-product and owner-mismatch cases return a context-rejection message. The producer process finishes instead of waiting indefinitely for stock context. Rejected responses contain no stored product data and cannot reach stock persistence.
- Processes end in `_S3`; message names begin with `S3 `; worker types are `desd.s3.business` and `desd.s3.message`. This isolates the iteration from existing Sprint 2 deployments.
- The business-operation journal replays committed results after worker restart. The transport outbox records prepared, in-flight, accepted and uncertain delivery states. An ambiguous delivery requires operator verification; an HTTP 400 is not treated as proof of acceptance.
- F1/F2 diagrams use the same executable resources that are deployed locally. Their SVG exports are presentation views, not execution evidence.

## Reproduce checks

```powershell
$env:PYTHONPATH = 'src'
python tools/build_sprint3_models.py --check
python -m unittest discover -s tests -v
python tools/run_sprint3_validation.py --date 2026-11-26
python tools/verify_sprint3_delivery.py
```

The validation command deploys current resources and creates real instances using a fresh local database. Actual user tasks are completed through REST. This is separate from manually completing Forms in Tasklist. The recovery case deliberately exits a worker process after SQLite commit but before job completion, then uses a new worker to finish the expired job.

[Engine summary](evidence/engine-validation.json), [delivery check](evidence/delivery-check.json), [traceability](traceability.md) and [LESP decisions](lesp-decisions.md) describe the recorded scope. `verify_sprint3_delivery.py` reads saved engine records and reruns local checks; it does not rerun engine scenarios.

The 26 November check passed 87 Python tests and 12 real-engine scenarios containing 75 assertions. The engine source hashes identify the Sprint 3 runtime Python files and BPMN/Form resources; they do not cover every reused Sprint 2 dependency or the validation harness.

The separate [Tasklist walkthrough](evidence/tasklist-manual.json) used the actual UI to submit a product, retry verification with the simulated verified fixture, and change quantity from 10 to 6 (version 1). The [follow-up screenshot](evidence/tasklist-follow-up.jpg) shows the conditional result field and review notes. This UI run preceded the explicit verification-merge gateway refinement; the final gateway version was then deployed and passed all 12 engine scenarios. No human usability study is asserted.

## Cloud models

The [Sprint 3 week-one folder](https://hub.camunda.io/workspaces/6cff561b-29d5-4c4a-9bc7-dc15b15e3de3/projects/82f487f8-5865-49bb-8455-733bf3af2b7c/folders/86263f2b-fd25-4bcb-8c99-a69f94431008) contains both diagrams and four Forms. [F1](https://hub.camunda.io/diagrams/f736c0da-54fd-4605-9364-578acc0b2c96--f1-sprint3) and [F2](https://hub.camunda.io/diagrams/334bc78a-0daf-487c-8aa5-cc8d9fd39aad--f2-sprint3) each showed Problems 0 in the cloud modeling check. Cloud import is separate from the local engine deployment recorded above. The superseded initial F1 import is retained in the separate Import history folder.

## Reproducibility and retained limits

Keep each worker and its associated engine instances on the same database. The manual and validation entry points share an exercise lock: finish one before starting the other. Stop a separately launched CLI worker before either harness. New validation runs use unique request/product IDs and a fresh store. Resetting the engine requires a fresh matching database because job keys can be reused. Running separate workers against different databases for the same job type is unsupported.

Certification remains a controlled fixture. Selecting a result in the follow-up form represents a simulated provider response, not approval from a real certifier. Producer identity and confirmed orders are supplied classroom inputs; ownership comparison is not authentication. Seasonal checks remain explicitly triggered. Category-specific food-information rules and stock-unit policies need business confirmation.

The controlled interruption case verifies one failure window. It does not establish a distributed exactly-once transaction, comprehensive network recovery or production failover. A transport incident remains visible until the underlying condition is repaired and its evidence reviewed. No independent member review or final assessment submission is asserted by this technical package.
