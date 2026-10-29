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

The [tutor-confirmation task #4](https://github.com/jensenxie-max/DESD-Group-26/issues/4) is marked complete. Add the tutor decision and any scope changes to the written record before detailed implementation.

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
- Model review (#5) and tutor confirmation (#4) are marked complete in GitHub. Brief review findings and the tutor decision still need a written record. The group-provided contribution matrix is available in `docs/sprint-1/`.
- The [Sprint 1 board](https://github.com/users/jensenxie-max/projects/2) opens without signing in. Repository and board public access were verified on 29 October 2026.
- Video recording is complete according to the group. Blackboard upload has not yet been confirmed.
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
