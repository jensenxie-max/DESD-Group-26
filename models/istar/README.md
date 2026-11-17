# Enterprise i* SD and SR

**Status: draft for group review, 17 November 2026.** These are two views of one model. The five actors come from the existing strategic BPMN and the requirements; they are not a tutor-prescribed list.

| File | Use |
|---|---|
| [SD.svg](SD.svg) / [SD.png](SD.png) | Whole-enterprise Strategic Dependency view; SVG remains clear when zoomed |
| [SR.svg](SR.svg) / [SR.png](SR.png) | Strategic Rationale view; all five actors are expanded and all six marketplace capability areas are shown |
| [SD-SR.drawio](SD-SR.drawio) | Editable two-page diagram; open in diagrams.net using **File → Open from → Device** |
| [enterprise-model.json](enterprise-model.json) | Canonical actor, element, dependency, relationship and assumption data |
| [validation.json](validation.json) | Static semantic and cross-model reference checks |
| [Traceability](../../docs/sprint-2/traceability.md) | Requirement → SD/SR → strategic BPMN → F1/F2 mapping |

## How to read the models

An SD dependency is read **depender → dependum → dependee**. For example, D01 means the marketplace relies on the producer for product data; D02 means the producer relies on the marketplace for publication. Dependency direction is not data-flow direction.

The SR adds each actor's intentions. Goals use ovals, tasks hexagons, resources rectangles, and qualities/softgoals cloud shapes. Internal relationships remain inside one actor. AND refinement requires all children; OR refinement offers a means of achieving a parent. A resource's needed-by link points to its task. A help/hurt contribution points to a quality.

Both views intentionally retain actor-level dependency endpoints. They do not claim that one internal task is the complete reason or implementation for a dependency. The `rationale` property and traceability table explain the relationship. D13 applies to claimed organic certification; D11 and D17 apply to a reported concern.

The producer rationale now expresses regional market access, low learning/administration effort and dependable income. Order preparation is a separate goal that applies only after an order has been accepted. The customer rationale expresses convenience, reliable supply and low multi-supplier administration; reporting a concern is separate from routine purchase preparation. It is not an AND prerequisite for ordinary shopping.

In F1, the certification requirement is OR-refined into **confirm no organic claim** and **verify a claimed certificate**. These are context-specific means of satisfying that requirement. The OR relationship does not prescribe an execution sequence or ask an unclaimed product to undergo verification. The verification task, rather than the no-claim alternative, carries the trust-versus-listing-time contribution links.

Notation follows the [iStar 2.0 Language Guide](https://arxiv.org/html/1605.07767v3), especially sections 4–7. The SVG uses D-shaped dependency markers. The editable diagrams.net copy uses a labelled `D` and an open directional arrow because the native editor does not provide the same marker.

## Scope and evidence

The model covers catalogue, inventory, orders/fulfilment, finance, quality/traceability, and community/sustainability. F1 and F2 provide detailed operational evidence for the first two areas. The remaining areas are enterprise context, not additional Sprint 2 automation claims.

Customer/community buyer aggregates the case's three segments:

- Individuals and families: convenient access to local food despite limited farm-shop opening hours.
- Community institutions: reliable and consistent supply for catering.
- Independent restaurants and cafes: less administration when dealing with multiple suppliers.

The source register in `enterprise-model.json` distinguishes the workbook, directly read Blackboard case text, existing strategic/operational files and design judgements. The case specifies at least 48 hours of producer preparation lead time, weekly settlements and 5% commission. The certification-service interaction comes from Use Case 1, not from treating the case's certification indicator as an independent verification requirement.

The F1 trust-versus-speed and F2 accuracy-versus-immediate-completion contributions are reasoned trade-offs, not measured performance claims. Pending certification, version checks and atomic persistence are existing prototype decisions. The separate [18 November runtime evidence](../../review-evidence/runtime-2026-11-18/) records actual Camunda 8.10.9 scenarios; the [model review](../../docs/sprint-2/model-review-2026-11-18.md) records the static ownership, route and cross-model checks. Certification uses named simulated results, and a seasonal recheck is manually triggered. These checks do not establish a production integration or a measured usability outcome.

## Editing and regeneration

For semantic changes, edit `enterprise-model.json`, then run:

```powershell
python models/istar/render_models.py
python models/istar/validate_models.py
```

`prepare_model.py` creates the original review baseline. Do not rerun it after changing the JSON unless deliberately restoring that baseline. SVG/drawio are generated from the JSON plus layout code. Edits made directly in diagrams.net are not imported back into the JSON; keep the chosen source consistent before regenerating.

## Decisions still needed

1. Check whether the group has existing SD/SR source files that should be preserved or merged.
2. Record the actual tutor decision on F1/F2 scope if it was agreed after the stored Sprint 1 baseline.
3. Review the trust/speed and correctness/completion trade-offs.
4. Agree stock units, date boundaries/time zone and verification failure follow-up in the operational design.

No team review, individual contribution, deployment or tutor approval is claimed by these files.
