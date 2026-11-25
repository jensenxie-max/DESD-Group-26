# Bristol Regional Food Network — Group 26

**Module:** UFCFTR-30-3 Distributed and Enterprise Software Development

## Project Overview

This project analyses and develops enterprise business processes for the Bristol Regional Food Network.

Our selected use case is **Use Case 1: Producer Product Listing and Inventory Management**. It supports accurate product information, stock management and seasonal availability.

The project progresses from strategic analysis and BPMN modelling to operational processes, Camunda automation and supporting software.

## Team and Planned Responsibilities

| Member | Student ID | Planned Responsibilities |
|---|---|---|
| Jiaqi Xie | 25028285 | Project coordination, requirements analysis, joint BPMN modelling, product validation and publishing, and overall integration |
| Yunze Yu | 25028284 | Joint BPMN modelling, inventory and availability, Camunda configuration and integration |
| Jilong Cheng | 25028281 | Work with Jiaqi on product requirement checks, review notes and later forms, testing and documentation |
| Haodong Yang | 25061288 | Work with Yunze on inventory requirement checks, review notes and later data handling, testing and documentation |

Jiaqi Xie and Yunze Yu jointly lead strategic and operational BPMN modelling.

The planned working pairs are Jiaqi Xie with Jilong Cheng, and Yunze Yu with Haodong Yang. Assignments describe intended work; completed contributions are recorded separately and attributed to the members who performed them.

## Sprint 1 Objectives

- Analyse the enterprise and its organisational responsibilities.
- Develop a strategic BPMN model covering the overall enterprise.
- Identify and scope two candidate major functionalities.
- Maintain an initial product backlog and sprint plan.
- Review the model against the case study and requirements.
- Maintain version-control and contribution evidence.
- Prepare the Sprint 1 review and submission.

## Project Links

- [Camunda strategic BPMN](https://hub.camunda.io/diagrams/0e4d3877-3211-460d-b58e-656a9d09e7f3--strategic-bpmn-bristol-food-network)
- [Camunda project README](https://hub.camunda.io/readmes/1e2f8e97-d53d-43ec-af65-957c8362ca3e--readme/)
- [BPMN source](models/strategic/Strategic-BPMN.bpmn) and [full-resolution diagram](models/strategic/Strategic-BPMN.png)
- [Repository issues](https://github.com/jensenxie-max/DESD-Group-26/issues) and [Sprint 1 project board](https://github.com/users/jensenxie-max/projects/2) (public access verified on 29 October 2026)

Camunda and GitHub are maintained separately. After model changes, export the BPMN source and readable diagram to `models/strategic/` and commit the corresponding documentation.

## Candidate Major Functionalities

1. **Product validation and publishing**
2. **Inventory and seasonal availability management**

The [tutor-confirmation task #4](https://github.com/jensenxie-max/DESD-Group-26/issues/4) is Closed, while its description still says confirmation is pending. Record the actual tutor decision, date and agreed scope to resolve this inconsistency. The later feedback accepts the process logic and asks for clearer task ownership; the cloud diagrams now separate participant pools and responsibility lanes accordingly.

## Repository Organisation

| Path | Purpose |
|---|---|
| `README.md` | Project overview, planned responsibilities and progress |
| [`docs/Use-Case-1-Requirements.xlsm`](docs/Use-Case-1-Requirements.xlsm) | Existing requirements workbook |
| [`docs/sprint-1/README.md`](docs/sprint-1/README.md) | Strategic scope, traceability, backlog and sprint plan |
| [`docs/sprint-1/Group-26-Sprint-1-Contribution-Matrix.docx`](docs/sprint-1/Group-26-Sprint-1-Contribution-Matrix.docx) | Group-provided Sprint 1 contribution matrix |
| [`models/strategic/`](models/strategic/) | Current strategic BPMN source, readable PNG and opening instructions |
| [`docs/sprint-1/submission-checklist.md`](docs/sprint-1/submission-checklist.md) | Video ZIP contents, access checks and contribution matrix completion |

The strategic model has one canonical repository location: `models/strategic/`. Local working exports under `outputs/` are not a second tracked copy.

## Current Progress

- Git repository and existing requirements workbook retained.
- Current strategic BPMN baseline exported from Camunda and stored under `models/strategic/`.
- Six business responsibility lanes, four external participants, 18 high-level tasks and F1/F2 candidate scope prepared.
- Camunda Design reported **Problems 0** for the saved strategic baseline on 28 October 2026. This does not certify business approval or executable readiness.
- Scope, source traceability, a 12-item prioritised backlog and Sprint 1 plan are available in [`docs/sprint-1/README.md`](docs/sprint-1/README.md).
- Model review (#5) is marked complete in GitHub. The scope-approval record in #4 is inconsistent and still needs the actual decision recorded. The group-provided Sprint 1 contribution matrix is available in `docs/sprint-1/`.
- The [Sprint 1 board](https://github.com/users/jensenxie-max/projects/2) opens without signing in. Repository and board public access were verified on 29 October 2026.
- Video recording is complete according to the group. Blackboard upload has not yet been confirmed.
- F1/F2 operational drafts now exist in Camunda; the saved 11 November exports remain non-executable. The strategic model in `models/strategic/` is still the Sprint 1 repository baseline.

### Sprint 2 implementation on 18 November 2026

The [Sprint 2 board](https://github.com/users/jensenxie-max/projects/4) tracks SD/SR, F1, F2, automation and the two verification tasks. [Current files and instructions](docs/sprint-2/README.md), [Blackboard requirements](docs/sprint-2/review-requirements-2026-11-17.txt) and [submission links](docs/sprint-2/submission-links.txt) are prepared.

The [operational models](models/operational/README.txt) preserve the saved responsibility revision and add execution configuration, 22 gateway conditions, cross-pool message correlation and three deployment-bound Forms. Real deployment and F1/F2 execution succeeded on local Camunda Run 8.10.9. The normal path publishes a product, then changes stock 10 → 6; correction, certification, invalid input, depletion, duplicate order, version conflict and seasonal paths also have recorded results. See [runtime validation](docs/sprint-2/runtime-validation-2026-11-18.md).

Double-click [Run-Sprint2.cmd](Run-Sprint2.cmd) for a manual Tasklist walkthrough on the configured Windows computer. The [runtime package](src/sprint2_runtime/README.txt) implements worker jobs and SQLite persistence around the existing business-rule modules. Certification is a fixture adapter; identity/order confirmation are supplied inputs and seasonal checks are invoked explicitly.

The [SD/SR models](models/istar/README.md), [technical model review](docs/sprint-2/model-review-2026-11-18.md) and [traceability register](docs/sprint-2/traceability.md) cover the enterprise context and selected functionality. [Current verification](docs/sprint-2/evidence/implementation-check-2026-11-18.json) records 58 Python tests and 45 passing engine assertions across seven scenarios.

Four individual GitHub upload packages are available under `outputs/sprint2-github-2026-11-18/`; see [who uploads what](docs/sprint-2/individual-files-2026-11-18.txt). These files have been prepared locally. Remote upload, each member's own review/contribution, final video and Blackboard submission remain group actions.

### Earlier preparation on 11 November 2026

See the [Thursday preparation pack](docs/sprint-2/README.md) for four individual work cards, F1/F2 field contracts, a node-specific Camunda review and a local Python business-rule example with tests. These preparation materials still need individual review and actual work records.

Three Camunda Forms are now saved and linked: F1 submission, F1 correction, and F2 stock and sale dates. F2 also has a new producer input task. Form Preview checks and variable-mapping checks passed; current exports and preview evidence are in `review-evidence/forms-2026-11-11/`.

These earlier files were preparation and Form Preview evidence. They do not prove engine execution; use the 18 November implementation and verification records for current progress.

## Planned Later Development

- Broader integration and production authentication.
- External certification/order adapters and automatic scheduling.
- Robust failure recovery and wider integration testing.
- Food-category rules and unit policies agreed by the group.

## Sprint 3 — week one

Use [the Sprint 3 technical baseline](docs/sprint-3/README.md) and [new executable models](models/sprint3/README.md). This iteration adds verification follow-up recovery/cancellation, safe stock-context rejection, explicit message-delivery observations and a controlled worker-process interruption test. Sprint 2 resources and dated evidence remain unchanged. Start the manual walkthrough with [Run-Sprint3.cmd](Run-Sprint3.cmd). Current checks and real-engine records are under [Sprint 3 evidence](docs/sprint-3/evidence/engine-validation.json).

## Working Practices

- Use Todo, In Progress and Done to reflect actual progress.
- Define an owner and completion criteria for each task.
- Update the owner if another member takes over the work.
- Record actual contributors through Git commits and review notes.
- Identify each person's activities when work is completed jointly.
- Save review findings and record how they were addressed.
