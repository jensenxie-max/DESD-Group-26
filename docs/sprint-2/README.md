# Sprint 2 — repository index, 19 November 2026

The [Blackboard requirements](review-requirements-2026-11-17.txt) cover SD/SR (30%), two operational BPMN models (35%), initial Camunda automation (25%), and progress/traceability/version control (10%).

| Area | Result | Evidence |
|---|---|---|
| SD/SR | Readable SVG/PNG and editable sources; technical review passed | [Model review](model-review-2026-11-18.md), [models](../../models/istar/README.md) |
| Model consistency | Responsibility, flows, reachability and cross-model references checked | [Traceability](traceability.md), [audit](evidence/model-review-2026-11-18.json) |
| Real execution | F1/F2 normal and selected alternative paths executed on local Camunda 8.10.9 | [Runtime validation](runtime-validation-2026-11-18.md) |
| Manual interaction | Actual Tasklist forms completed; stock 10 → 6 | [Tasklist run](../../review-evidence/runtime-2026-11-18/tasklist-user-run.json) |
| Verification | Captured local checks and saved engine evidence; delivered-file hashes aligned on 19 November | [Result](evidence/implementation-check-2026-11-18.json), [test output](evidence/implementation-tests-2026-11-18.txt) |

Deploy executable BPMN and Forms from `models/operational/`. Cloud Camunda diagrams retain the saved responsibility design; local execution configuration and run history do not sync to the cloud editor. Token simulation provides an additional way to explain the diagram.

## Manual demonstration

On this Windows computer, double-click `Run-Sprint2.cmd` at the repository root and keep its window open. It uses the installed Camunda Run package, deploys both models and three Forms, then waits for actual Tasklist input.

1. Log in to local Tasklist with `demo` / `demo`.
2. Open `Submit product details` → **Assign to me**. Keep sample quantity 10 and no organic claim → **Complete Task**.
3. Open `Enter stock and sale dates` → **Assign to me**. Set **New quantity** to 6 → **Complete Task**.
4. Show the completed instances in Operate and the resulting product quantity/version.

See [runtime instructions](../../src/sprint2_runtime/README.txt) and [scenario validation](runtime-validation-2026-11-18.md). Automated integration cases complete real user tasks through REST; manual Tasklist evidence is recorded separately.

## GitHub files

The four individual upload packages have been checked against the repository: their 103 distinct paths are present. See [each member's files](individual-files-2026-11-18.txt) for the upload allocation. The packages under `outputs/` are local working artifacts and are not tracked repository dependencies.

The repository contains model exports, Forms, code, tests and captured verification evidence. Run `python tools/verify_sprint2_delivery.py` to repeat local checks and validate saved engine results. The packaging command `python tools/package_sprint2_review.py --check` applies only where the original local upload packages are also available. Earlier dated baselines remain historical snapshots.

## Group review and delivery

Use the [10-minute walkthrough](review-walkthrough.txt). The group-provided [Sprint 2 contribution matrix](Contribution-Matrix.docx) is stored unchanged. The [contribution record](contribution-record.md) indexes its allocations and corresponding deliverables; personal review dates, findings and conclusions remain to be recorded by the members. [Technical review](i-star-review-checklist.md), personal student review and tutor approval are separate records.

Include [submission-links.txt](submission-links.txt) in the final group ZIP. The group confirmed completion of video recording on 19 November. Blackboard upload and the submission receipt have not been confirmed. The group still checks repository/board access and submits the final ZIP with its MP4. These GitHub packages are not the final Blackboard video ZIP.

Prototype boundaries: local certification fixtures; supplied producer identity/order confirmation; manually invoked seasonal checks; local SQLite/customer-availability projection. Category-specific food information, production authentication and robust recovery remain later decisions.

Video status was updated after the supplied contribution matrix was prepared. The matrix is retained unchanged, including its preparation-stage wording; the latest recording status is the group confirmation above.
