# Sprint 2 model review — 18 November 2026

**Result: technical checks passed, with the prototype boundaries below.** No business-flow or pool/lane correction was required by this review. The saved models, exact requirement mappings and key alternative routes agree. Real-engine evidence is linked separately from static checks. This review does not record a tutor scope decision or a review performed by named group members.

## Reviewed files and requirements

- SD and SR: `models/istar/enterprise-model.json`, the two SVG/PNG views, and editable `SD-SR.drawio`.
- Strategic baseline: `models/strategic/Strategic-BPMN.bpmn`.
- F1/F2 design baselines: the saved responsibility exports under `review-evidence/responsibilities-2026-11-17/`.
- Executable F1/F2: `models/operational/`, including the three task forms and execution manifest.
- R1–R10 from the requirements workbook, the saved Blackboard case text, and the 20-row requirement-to-model register. The included [case text](../../review-evidence/requirements-2026-11-18/case-study-preview.txt) replaces an ephemeral working-directory reference. The original Blackboard URL is retained in the source register.

The [machine-readable review](evidence/model-review-2026-11-18.json) includes file hashes, lane membership, message endpoints, alternative paths and exact validation results.

## Ownership and BPMN structure

| Model | Participants | Internal lanes | Flow nodes / sequence flows | Result |
|---|---:|---:|---:|---|
| Strategic | 5 | 6 | 30 / 24 | Pass |
| F1 design and executable | 3 | 2 | 30 / 32 | Pass |
| F2 design and executable | 2 | 2 | 42 / 45 | Pass |

F1 submission and correction tasks belong to the **Producer** pool. Validation, publication, certification-service invocation and outcome communication belong to the Marketplace's **Catalogue and producer support** lane. Initial sale availability belongs to its **Inventory and availability** lane. The verification participant is external; its internal implementation is hidden.

F2 stock/date entry belongs to the **Producer** pool. Loading, input checks, order deductions, sale assessment, persistence, availability synchronisation and follow-up belong to the Marketplace's **Inventory and availability** lane. The names of finance, warehouse and customer-service departments in the supplied teacher feedback were examples of responsibility allocation; they do not require adding unrelated F1/F2 departments.

All sequence flows stay inside their process. All message flows cross participant boundaries. All process flow nodes are reachable from a start and can reach an end. Nodes in processes with lanes are assigned exactly once, and their diagram bounds lie inside the assigned lane. No duplicate IDs, dangling flow references, inconsistent incoming/outgoing declarations or invalid event-gateway targets were found. The executable generator preserves the design baseline's IDs, graph, participants, lane membership and diagram layout.

The strategic and saved cloud responsibility models remain non-executable design baselines. Use the separate **operational BPMN and forms** for deployment. The executable versions contain 7 F1 and 15 F2 FEEL conditions, native user-task forms and worker/message configuration.

## SD/SR and cross-model consistency

The SD and SR contain the same **5 actors and 19 dependencies**. The SR adds **67 intentional elements and 64 internal links**. Relationship typing, same-actor internal links, dependency actors/endpoints, AND/OR refinement consistency and absence of refinement cycles pass. Customer concern reporting and producer accepted-order preparation remain separate conditional goals. Resolving certification is OR-refined into no-claim and verification alternatives, so an unclaimed product is not required to undergo verification.

All 20 traceability rows resolve to actual SD/SR, strategic and F1/F2 element IDs. R1–R10 are present. Enterprise context covers orders, 48-hour preparation lead time, weekly settlements, 5% commission, quality/traceability, community information and sustainability; those areas are not claimed as extra F1/F2 automation.

SD/SR PNGs were visually inspected. No missing or overlapping principal element labels were identified. The SR is dense at whole-page scale: use its SVG and zoom into the relevant actor/capability during a presentation.

## Alternative paths and real execution evidence

Static route checks cover F1 correction/resubmission, invalid certification, unavailable verification/pending, publication, and F2 invalid input, rejected/duplicate order, available/unavailable, commit success/failure, producer outcomes and integration outcomes. Static reachability is supplemented by these actual engine records:

| Real-engine scenario | Checks passed | Evidence |
|---|---:|---|
| F1 publication and F2 stock 10 → 6 | 3 | [happy](../../review-evidence/runtime-2026-11-18/happy-engine.json) |
| Invalid F1 details → correction task → resubmission → publication | 6 | [correction](../../review-evidence/runtime-2026-11-18/correction-engine.json) |
| Invalid simulated certificate → correction → reverification | 7 | [invalid certificate](../../review-evidence/runtime-2026-11-18/invalid-certificate-engine.json) |
| Negative stock, fractional stock and reversed dates rejected without persistence/projection changes | 15 | [invalid input](../../review-evidence/runtime-2026-11-18/invalid-input-engine.json) |
| Valid simulated organic claim | 3 | [organic](../../review-evidence/runtime-2026-11-18/organic-engine.json) |
| Unavailable simulated verification → unpublished and persisted follow-up | 2 | [pending](../../review-evidence/runtime-2026-11-18/pending-engine.json) |
| Zero stock, duplicate order, stale-version conflict, restock and out-of-season availability | 9 | [boundaries](../../review-evidence/runtime-2026-11-18/boundaries-engine.json) |

These seven scenario files contain **45 passing assertions**. Automated scenario tasks were completed through the engine API; the separate [Tasklist walkthrough](../../review-evidence/runtime-2026-11-18/tasklist-ui-run.json) records the manual UI route. Neither execution method implies a real certification provider or a deployed checkout/payment system.

## Retained boundaries and decisions

- Stock uses whole units, sale dates include both endpoints, and an explicit business date drives eligibility. These are existing prototype policies; fractional-weight products would require a unit-policy decision.
- Harvest date, allergens and best-before fields are collected where relevant. The requirements do not settle all category-specific applicability rules; this review does not invent a universal mandatory-field policy.
- Certification uses named simulated provider results. Unavailable verification records a pending follow-up; it does not claim automatic retry or eventual external verification.
- Producer identity and confirmed-order inputs are trusted demo inputs. Account authentication, checkout and payment validation are outside this prototype.
- The seasonal route is exercised by an explicit trigger. A recurring timer/scheduler is not claimed.
- SQLite version checks, transaction persistence and customer-availability projection support this initial implementation. Production failover, network failure recovery and end-to-end exactly-once guarantees remain outside these checks.
- A missing/corrupt stored product, invalid source or invalid initial owner context can raise an incident before the normal F2 input branch; graceful recovery for every setup/integration error is not claimed.

## Reproduce

```powershell
python models/istar/validate_models.py
python tools/build_sprint2_executable.py --check
python tools/review_sprint2_models.py
```

The last command checks saved model structure and the linked scenario records. Use the runtime CLI described under `src/sprint2_runtime/` to rerun engine scenarios; this static audit itself does not start the engine or create process instances.
