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
- [Repository issues](https://github.com/jensenxie-max/DESD-Group-26/issues) and [Sprint 1 project board](https://github.com/users/jensenxie-max/projects/2) (marking-team access still to verify)

Camunda and GitHub do not automatically synchronize. Follow the [export and sync procedure](docs/sprint-1/sync-and-review.md#export-and-sync-procedure) after future model changes.

## Candidate Major Functionalities

1. **Product validation and publishing**
2. **Inventory and seasonal availability management**

Both proposals require agreement from the module team before detailed implementation begins.

## Repository Organisation

| Path | Purpose |
|---|---|
| `README.md` | Project overview, planned responsibilities and progress |
| [`docs/Use-Case-1-Requirements.xlsm`](docs/Use-Case-1-Requirements.xlsm) | Existing requirements workbook |
| [`docs/sprint-1/README.md`](docs/sprint-1/README.md) | Strategic scope, traceability, backlog and sprint plan |
| [`docs/sprint-1/sync-and-review.md`](docs/sprint-1/sync-and-review.md) | Baseline evidence, open checks and synchronization instructions |
| [`models/strategic/`](models/strategic/) | Current strategic BPMN source, readable PNG and opening instructions |
| [`meetings/Sprint-1-Review-Template.md`](meetings/Sprint-1-Review-Template.md) | Unfilled group-review and tutor-decision template |

The strategic model has one canonical repository location: `models/strategic/`. Local working exports under `outputs/` are not a second tracked copy.

## Current Progress

- Git repository and existing requirements workbook retained.
- Current strategic BPMN baseline exported from Camunda and stored under `models/strategic/`.
- Six business responsibility lanes, four external participants, 18 high-level tasks and F1/F2 candidate scope prepared.
- Camunda Design reported **Problems 0** for the saved strategic baseline on 28 October 2026. This does not certify business approval or executable readiness.
- Scope, source traceability, a 12-item prioritised backlog and Sprint 1 plan are available in [`docs/sprint-1/README.md`](docs/sprint-1/README.md).
- Group review, tutor agreement and actual individual contribution evidence remain open.
- The existing [Sprint 1 board](https://github.com/users/jensenxie-max/projects/2) was checked in the signed-in browser: Todo 3 (#4/#5/#6), In Progress 2 (#2/#7), Done 2 (#1/#3). Marking-team access still needs verification.
- Later operational modelling and automation remain planned work.

## Planned Later Development

- i* Strategic Dependency and Strategic Rationale models.
- Two detailed operational BPMN models.
- Executable Camunda processes and Forms.
- Supporting business logic, interfaces and data handling.
- Alternative flows, exception handling and integration testing.

## Working Practices

- Use Todo, In Progress and Done to reflect actual progress.
- Define an owner and completion criteria for each task.
- Update the owner if another member takes over the work.
- Record actual contributors through Git commits and review notes.
- Identify each person's activities when work is completed jointly.
- Save review findings and record how they were addressed.
- Keep planned responsibilities separate from completed contributions.

## Submission Checks

**Sprint 1: submit a single ZIP to Blackboard before Thursday, 29 October 2026, 14:00 UK time. The group has selected Option B: pre-recorded MP4 video, maximum 10 minutes.**

The module-team Sprint 1 submission announcement supplied on 28 October overrides the earlier general-PDF-only interpretation. The ZIP must contain the repository/project-management links document, the MP4, and slides if used. All members must appear and present with clear audio/video, introducing their full name and student ID. Demonstrate both the actual work and project management: the Kanban board, allocation, planning and tracking. Standup 3 must still be attended and is marked separately for video groups. A written report is not required; slides are optional.

See the [current submission requirements](docs/sprint-1/submission-instructions.md), [links document](docs/sprint-1/submission-links.txt) and [recording checklist](docs/sprint-1/video-checklist.md). A local preparation ZIP is available under `outputs/sprint-1-submission/`; it is a draft until the recorded MP4 and any used slides have been added and checked.

The repository and board are private. Confirm marking-team access before submitting. Group review, tutor agreement on F1/F2 and genuine contribution evidence remain open. The 10 December date in the general brief is the Task 1 final deadline, not the Sprint 1 ZIP deadline. No Blackboard upload, video recording or access change is recorded as completed by this update.
