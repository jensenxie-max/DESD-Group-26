# Sprint 2 — current files, 18 November 2026

The [Blackboard requirements](review-requirements-2026-11-17.txt) cover SD/SR (30%), two operational BPMN models (35%), initial Camunda automation (25%), and progress/traceability/version control (10%).

| Area | Result | Evidence |
|---|---|---|
| SD/SR | Readable SVG/PNG and editable sources; technical review passed | [Model review](model-review-2026-11-18.md), [models](../../models/istar/README.md) |
| Model consistency | Responsibility, flows, reachability and cross-model references checked | [Traceability](traceability.md), [audit](evidence/model-review-2026-11-18.json) |
| Real execution | F1/F2 normal and selected alternative paths executed on local Camunda 8.10.9 | [Runtime validation](runtime-validation-2026-11-18.md) |
| Manual interaction | Actual Tasklist forms completed; stock 10 → 6 | [Tasklist run](../../review-evidence/runtime-2026-11-18/tasklist-user-run.json) |
| Verification | Current local checks and saved engine evidence | [Result](evidence/implementation-check-2026-11-18.json), [test output](evidence/implementation-tests-2026-11-18.txt) |

Deploy executable BPMN and Forms from `models/operational/`. Cloud Camunda diagrams retain the saved responsibility design; local execution configuration and run history do not sync to the cloud editor. Token simulation provides an additional way to explain the diagram.

## Manual demonstration

On this Windows computer, double-click `Run-Sprint2.cmd` at the repository root and keep its window open. It uses the installed Camunda Run package, deploys both models and three Forms, then waits for actual Tasklist input.

1. Log in to local Tasklist with `demo` / `demo`.
2. Open `Submit product details` → **Assign to me**. Keep sample quantity 10 and no organic claim → **Complete Task**.
3. Open `Enter stock and sale dates` → **Assign to me**. Set **New quantity** to 6 → **Complete Task**.
4. Show the completed instances in Operate and the resulting product quantity/version.

See [runtime instructions](../../src/sprint2_runtime/README.txt) and [scenario validation](runtime-validation-2026-11-18.md). Automated integration cases complete real user tasks through REST; manual Tasklist evidence is recorded separately.

## GitHub files

Use the four packages in `outputs/sprint2-github-2026-11-18/`. Extract your ZIP, open `repo-root`, and upload its **contents** at the shared repository root, preserving paths. See [each member's files](individual-files-2026-11-18.txt).

Packages contain model exports, Forms, code, tests and current verification evidence. Verify source/copy/ZIP hashes with `python tools/package_sprint2_review.py --check`. Earlier dated records and 17 November packages are historical snapshots.

## Group review and delivery

Use the [10-minute walkthrough](review-walkthrough.txt). Each member records actual work in [contribution-record.md](contribution-record.md). [Technical review](i-star-review-checklist.md), personal student review and tutor approval are separate records.

Include [submission-links.txt](submission-links.txt) in the final group ZIP. The group still checks remote access after upload, rehearses, records the MP4 if using video, and performs Blackboard submission. These GitHub packages are not the final Blackboard video ZIP.

Prototype boundaries: local certification fixtures; supplied producer identity/order confirmation; manually invoked seasonal checks; local SQLite/customer-availability projection. Category-specific food information, production authentication and robust recovery remain later decisions.
