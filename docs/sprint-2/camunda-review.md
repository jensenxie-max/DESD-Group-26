# Camunda review — 18 November 2026

The tutor feedback asked for clear task ownership in the correct participant pool and internal responsibility lane. The reviewed design is saved in `review-evidence/responsibilities-2026-11-17/`. Executable copies in `models/operational/` preserve those nodes, pools, lanes, flows and layout, and add runtime configuration.

| Model | Flow nodes / sequence flows | Result |
|---|---|---|
| F1 | 30 / 32 | Publication, information correction, certificate correction and verification-pending paths executed |
| F2 | 42 / 45 | Producer edits, invalid input, order exhaustion/duplicate, commit conflict, restock and seasonal availability executed |
| Strategic | 30 / 24 | Responsibility, reachability and cross-model checks passed; retained as enterprise design |

See [model review](model-review-2026-11-18.md) and [actual runtime evidence](runtime-validation-2026-11-18.md).

F1 separates Producer and Marketplace processes and shows the certification participant. Producer supplies/corrects details; Marketplace validates, checks a claimed certificate, publishes or records follow-up, and returns a result.

F2 separates Producer entry/results from Marketplace inventory work. Producer requests receive stock context before the form. Order and seasonal messages go directly to Marketplace and bypass the producer form. Sequence flows stay inside each process; worker message publication/correlation implements cross-participant exchanges.

Every node in a process with lanes is assigned once. Sequence/message endpoints, start reachability and a route to an end are checked. Structural checks support business review; actual instance/job/state evidence is recorded separately.

## Outcomes checked

- Invalid F1 details/certificate return to correction. Before successful correction, no product or customer projection exists. Unavailable verification records follow-up without publishing.
- Negative/fractional stock and reversed dates are rejected. Product/version/projection stay unchanged; commit and synchronization are not executed.
- Exhausting stock disables sale. Duplicate orders do not deduct twice. Stale-version commits preserve concurrent changes and record follow-up. Restock inside the sales period restores availability; positive stock outside it stays unavailable.

Cloud `Design → Token simulation` demonstrates tokens. Real execution uses local deployment, Tasklist, workers and Operate. Problems 0 alone is not runtime proof.

## Prototype boundaries

The certification task calls local fixture responses; no real authority is contacted. Producer identity and confirmed orders are supplied inputs. Seasonal checks use explicit invocation.

Invalid initial product/owner/source contracts can create an incident before Producer receives context; the CLI checks these before starting. Production authentication, external integration and robust transport recovery remain later work.
