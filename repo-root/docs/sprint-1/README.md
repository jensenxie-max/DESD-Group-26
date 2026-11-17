# Sprint 1 Scope, Backlog and Plan — Group 26

**Module:** UFCFTR-30-3 Distributed and Enterprise Software Development
**Selected Use Case:** Use Case 1 — Producer Product Listing and Inventory Management

Repository edition, synchronized from the saved Camunda README on 28 October 2026. See the [project overview](../../README.md), [model files](../../models/strategic/) and [submission checklist](submission-checklist.md). This edition includes repository-specific status updates; the Camunda README remains a separate saved document.

## Project Overview

This project supports strategic and operational BPMN modelling and subsequent Camunda process automation for the Bristol Regional Food Network.

The strategic model covers the overall enterprise. Detailed operational models will focus on two functionalities within the selected use case, subject to tutor agreement.

## Sprint 1 Objectives

- Analyse major business processes, participants and responsibilities.
- Develop a strategic BPMN model of the overall enterprise.
- Represent key business interactions and external services.
- Identify and scope two candidate major functionalities.
- Review the model against the case study and requirements.
- Export BPMN files and readable diagrams to GitHub.

## Candidate Major Functionalities

1. Product validation and publishing.
2. Inventory and seasonal availability management.

Tutor-confirmation task #4 is awaiting tutor confirmation. F1/F2 remain candidate functionalities. Record the actual decision and any scope changes after confirmation is received, before detailed implementation begins.

## Team and Planned Responsibilities

| Member | Student ID | Planned Responsibilities |
|---|---|---|
| Jiaqi Xie | 25028285 | Project coordination and requirements analysis; joint BPMN lead; lead for product validation and publishing |
| Yunze Yu | 25028284 | Joint BPMN lead; lead for inventory and availability; Camunda configuration and integration |
| Jilong Cheng | 25028281 | Work with Jiaqi on product requirement checks, review notes and later forms, testing and documentation |
| Haodong Yang | 25061288 | Work with Yunze on inventory requirement checks, review notes and later data handling, testing and documentation |

## Current Status

- Project and initial requirements documentation established.
- Strategic BPMN saved in Camunda and exported. The model-review task #5 is marked complete; brief review findings still need recording.
- F1/F2 are awaiting tutor confirmation (#4); tutor approval has not yet been obtained.
- Detailed automation and supporting code are planned for later sprints.

## Version Control and Review

[GitHub repository](https://github.com/jensenxie-max/DESD-Group-26)

| Location | Contents |
|---|---|
| `models/` | BPMN source files and readable exports |
| `docs/` | Requirements, scope and supporting analysis |
| `meetings/` | Review feedback, decisions and tutor feedback |

Record model changes, review findings and revisions in the repository. Identify the actual contributors to individual and joint work.

## Two Candidate Major Functionalities

### F1 — Product validation and publishing

- Trigger: a registered producer submits product details.
- Inputs: name, description, category, price, quantity, availability period, farm origin and relevant harvest date, allergen, certification and best-before information.
- Scope: validate mandatory information; request corrections; verify an organic claim through an external or simulated service; publish only after successful validation; communicate the outcome.
- Exceptions to develop: invalid/missing fields, rejected certification, unavailable verification service and producer correction/resubmission.
- Output: a validated published product or a clear unresolved/rejected outcome, with enough status information for follow-up.
- Excludes: customer checkout, payment settlement and quality-incident case management.
- Planned lead/reviewer pair: Jiaqi Xie / Jilong Cheng; joint BPMN review with Yunze Yu.

### F2 — Inventory and seasonal availability management

- Trigger: a producer changes quantity/seasonal availability; a confirmed order supplies a quantity change.
- Scope: update stock and availability; make zero-stock products unavailable; make replenished products available only while still within the availability period; synchronise customer-facing status.
- Exceptions to develop: invalid quantities or dates, stale/concurrent updates, failed persistence and unavailable dependencies. Concurrency handling and automatic seasonal-expiry checks are design proposals to validate.
- Output: consistent quantity and sale-availability status for customer-facing ordering.
- Excludes: full order/payment implementation, settlement and incident investigation.
- Planned lead/reviewer pair: Yunze Yu / Haodong Yang; joint BPMN review with Jiaqi Xie.

**Tracker status: [tutor-confirmation task #4](https://github.com/jensenxie-max/DESD-Group-26/issues/4) is awaiting tutor confirmation. F1/F2 have not yet been confirmed by the tutor.**

## Requirement Traceability

| Source | Requirement | Strategic coverage / follow-up |
|---|---|---|
| Assessment Brief pp.3–5, p.14 | Whole-enterprise strategic BPMN, responsibilities, external interactions and two substantial candidates | Six lanes, four external parties and F1/F2 highlighted. Task #4 awaits tutor confirmation. Task #5 marked complete; written findings to add |
| Case Study pp.1–2; Use Cases p.1 | Product information, conditional organic checks, correction/failure handling | F1; detailed alternative paths in the later operational model |
| Case Study pp.1–2; Use Cases p.1 | Quantity and seasonal availability, zero stock, replenishment | F2; confirm expiry/concurrency assumptions |
| Case Study pp.1–2 | Multi-vendor responsibilities and minimum 48-hour preparation lead time | Order/fulfilment area; lead-time rule recorded in task documentation |
| Case Study p.2 | Weekly settlements, audit trail and 5% commission | Finance area; payment systems must be sandbox/simulated |
| Case Study p.2; Use Cases p.3 | Link customers/products/producers/orders and communicate quality concerns | Quality/traceability area; conditional suspension and failed-notification follow-up documented |
| Case Study p.2 | Surplus discounts, recipes/storage/farm stories and postcode-based food miles | Community/sustainability area |

Reference files: `Case_Study_-_v2.pdf`; `Task_1_-_Use_Cases.pdf`; `UFCFTR-30-3_-First_Sit_-_Task_1(1).pdf`. The module-team announcement supplied on 28 October governs the review format and ZIP deadline; see the [submission checklist](submission-checklist.md).

## Initial Product Backlog

Owners below are planned responsibilities. A drafted artefact is not evidence of completed student contribution or an approved deliverable.

| ID | Priority | Backlog item | Planned owner / reviewer | Completion criteria | Status |
|---|---|---|---|---|---|
| S1-01 | Must | Review enterprise requirements and stakeholders | Jiaqi / Jilong | Each principal requirement has a source and an owner; assumptions are listed | Draft mapped. Review task #5 marked complete; findings to add |
| S1-02 | Must | Strategic BPMN of the whole enterprise | Jiaqi + Yunze / all members | Major areas and external interactions represented; diagram readable; modeling checks reviewed | Baseline saved and exported. Review task #5 marked complete; findings to add |
| S1-03 | Must | Scope F1 and F2 | Jiaqi + Yunze / module team | Boundaries, triggers, outcomes and exceptions documented; tutor decision recorded | Scope drafted. Awaiting tutor confirmation (#4); record the decision after confirmation is received |
| S1-04 | Must | Review BPMN semantics and coverage | Jilong + Haodong / joint BPMN leads | Review notes identify gaps and record their resolution | Marked complete in issue #5. Add reviewers, date and brief findings |
| S1-05 | Must | Repository and project-board evidence | Jiaqi / all members | BPMN and readable export stored, board links accessible, meaningful actual contributions recorded | Model files saved; repository and board publicly accessible; group contribution matrix uploaded |
| S1-06 | Must | Sprint review video and ZIP | All members | All members introduce themselves and demonstrate progress/project management in MP4 <=10 min; links and video in one ZIP before 29 October 14:00 UK | Recording: complete (group reported). Blackboard upload: not yet confirmed |
| S2-01 | Must | i* SD and SR models | Joint BPMN leads / all members | Goals, dependencies and rationale trace to strategic/operational choices | Planned |
| S2-02 | Must | Detailed operational BPMN for F1 | Jiaqi / Jilong | Correction, certification failure/outage and publication paths traced end to end | Planned; obtain and record tutor confirmation before detailed implementation |
| S2-03 | Must | Detailed operational BPMN for F2 | Yunze / Haodong | Zero stock, replenishment, season boundaries and update failures represented | Planned; obtain and record tutor confirmation before detailed implementation |
| S2-04 | Must | Initial executable processes and Forms | Function leads / paired reviewers | User tasks, variables, gateways and initial services can be demonstrated | Planned after operational modelling |
| S3-01 | Must | End-to-end integration and exception testing | All members | Both functions run; test evidence covers normal and exception paths | Planned |
| S3-02 | Should | Evaluate legal, ethical, social and professional issues | All members | Issues linked to concrete data/service/design choices and explained in Q&A | Planned |

## Sprint 1 Completion Plan

1. Review source requirements and assumptions together; resolve unclear business boundaries.
2. Walk through the strategic diagram row by row. Check external messages, responsibility allocation and the connections described in the reading guide.
3. Review F1/F2 against the selected use case. Take scope proposals to the module team and record the actual decision.
4. Record review findings with an owner and resolution, then revise the model where justified.
5. Export BPMN XML and PNG/SVG, add them to the repository with an accurate change description, and link the current project board.
6. The group reports that the Option B video is recorded. Check the actual MP4 is no longer than 10 minutes, all members introduce their full name/student ID and present their contribution, and technical progress and Kanban planning/tracking are covered. Attend Standup 3 separately.
7. Add the MP4, repository/board links document and slides if used to one ZIP; check marking-team access and upload to Blackboard before 29 October 2026, 14:00 UK time.

Sprint 1 group-mark criteria: strategic BPMN 50%; business analysis/scope/planning 30%; progress/version control/professional practice 20%. Sprint 1 contributes 20% of the Task 1 Group Mark. i* models may start now but are summatively evaluated in Sprint 2. Full executable automation is a later-sprint objective.

## GitHub Task Mapping

| Backlog item | GitHub task / evidence |
|---|---|
| S1-01 | [Requirements preparation #3](https://github.com/jensenxie-max/DESD-Group-26/issues/3), [requirements workbook](../Use-Case-1-Requirements.xlsm) and scope/traceability above |
| S1-02 | [Strategic model #2](https://github.com/jensenxie-max/DESD-Group-26/issues/2) and [model files](../../models/strategic/) |
| S1-03 | [Tutor scope agreement #4](https://github.com/jensenxie-max/DESD-Group-26/issues/4) |
| S1-04 | [Group model review #5](https://github.com/jensenxie-max/DESD-Group-26/issues/5) and actual review findings recorded on that issue |
| S1-05 | [Repository/access checks #7](https://github.com/jensenxie-max/DESD-Group-26/issues/7) and [submission checklist](submission-checklist.md) |
| S1-06 | [Video presentation #6](https://github.com/jensenxie-max/DESD-Group-26/issues/6) |

## Sprint 1 Camunda Completion Check — 28 October 2026

The Camunda preparation work is complete for the current Sprint 1 baseline. This status covers model content, project documentation, visual checks, saved versions and export preparation. It does not certify tutor approval, student contribution, repository submission or a completed assessed sprint review.

| Sprint 1 item | Camunda evidence | Result |
|---|---|---|
| Strategic model of the overall enterprise | Six responsibility lanes, 18 high-level activities, four external participants and message exchanges | Prepared |
| Organisational responsibilities and interactions | Lane names, participant boundaries, task documentation and strategic reading guide | Prepared |
| Relationships between principal processes | Reading-guide mapping of catalogue/stock, orders, settlement, traceability and community information | Documented; detailed integration is a later-sprint task |
| Two candidate major functionalities | F1/F2 highlighted in the diagram; boundaries, inputs, outcomes and exception scope in README | Prepared. Awaiting tutor confirmation (#4) |
| Initial backlog and Sprint plan | 12 prioritised items with proposed owners, completion criteria, status and review sequence | Prepared |
| Visual and structural review | Order-outcome and quality-notification message routes adjusted to avoid activities/end events; narrow labels repositioned | Corrected |
| Model validation | Camunda Design panel reported Problems 0 after the corrected model was uploaded | Passed at strategic-model level |
| Model history | Sprint 1 - Reviewed baseline 2026-10-28 | Saved |
| External submission/evidence | Model exports saved; repository and board publicly accessible; group contribution matrix uploaded. Task #5 marked complete, with written findings to add. Task #4 awaits tutor confirmation | Blackboard upload not yet confirmed |


## Sprint 1 Contribution Record

The current [group-provided contribution matrix](Group-26-Sprint-1-Contribution-Matrix.docx) contains the component allocations, overall allocation, discussion details and entered signature fields supplied by the group. The uploaded file is unchanged. The earlier For-Review document is a superseded draft.

The group reports that the video is recorded. Use the [submission checklist](submission-checklist.md) to assemble the actual MP4 and links into the final Blackboard ZIP.

## Review and Access Status

| Item | Current status | Record to keep |
|---|---|---|
| Group model review | [Issue #5](https://github.com/jensenxie-max/DESD-Group-26/issues/5) marked complete | Names of reviewers, date, model version, main findings and changes |
| Tutor confirmation of F1/F2 | [Issue #4](https://github.com/jensenxie-max/DESD-Group-26/issues/4): awaiting tutor confirmation | After confirmation: tutor name, actual date, decision and any scope changes |
| Repository and board access | Public access verified on 29 October 2026 | Both links open without signing in |
| Video | Recording complete according to the group | Actual MP4, with duration and playback checked |
| Blackboard submission | Upload not yet confirmed | Submission receipt |

Group model review (#5) is marked complete; add a short note showing what the group checked. Tutor confirmation (#4) remains pending. Record the tutor decision and any scope changes after confirmation is received.
