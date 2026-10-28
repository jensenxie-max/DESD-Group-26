# Sprint 1 Repository Sync and Evidence Register

Checked on **28 October 2026** against the saved Camunda exports, local Git history, authenticated GitHub repository/issue data and the supplied 2026-27 Assessment Brief.

## Baseline evidence

| Check | Evidence / result |
|---|---|
| Repository | `jensenxie-max/DESD-Group-26`; private; default branch `main` |
| Previous remote baseline | `5b674ab2ba10f1d9168f4cbb8e254420ad7f5feb` contained README and requirements workbook only |
| Model source | [Canonical BPMN](../../models/strategic/Strategic-BPMN.bpmn), exported from the current saved Camunda diagram |
| Readable model | [Canonical PNG](../../models/strategic/Strategic-BPMN.png) |
| Scope and planning | [Repository edition of the saved Camunda notes](README.md) |
| Model version | `Sprint 1 - Reviewed baseline 2026-10-28` |
| Camunda README version | `Sprint 1 - Completion check 2026-10-28` |
| Model checks | Camunda Design: Problems 0; XML parse, unique IDs, references, flow diagrams and node connections checked locally |
| Group/tutor approval | Not recorded; issues #4 and #5 remain open |
| Existing project board | [DESD Group 26 - Sprint 1](https://github.com/users/jensenxie-max/projects/2), private; verified in the signed-in browser on 28 October 2026; marking-team access not verified |

SHA-256 of the exported BPMN: `cbd2cb85d0bc5185fc845061fa100368e10019079de7fb212abebf4ea017f8ca`.

SHA-256 of the exported PNG: `70ccf993785d72d176b71cb0dc2ad42887acfed986655be99d6d95d9208dec0b`.

## Corrections in this synchronization

- Store the latest cloud model and image under the existing repository convention `models/strategic/`.
- Replace the stale README status stating that strategic modelling is still in progress with the actual saved-baseline status and open review actions.
- Link the cloud diagram, cloud README, local model, requirements and backlog.
- Correct issue #3's workbook reference from `.xlsx` to the tracked `.xlsm` file.
- Update model/scope/review issues with artifact links and explicit completion criteria; keep pending human reviews open.
- The earlier sync changed the video/ZIP instructions using only the general PDF. That interpretation is superseded by the module-team Sprint 1 announcement supplied on 28 October. Issues #6/#7 are restored to video preparation and the 29 October ZIP deadline, with the announcement as the governing source.
- Keep a single tracked model copy. Ignore working exports and intermediate model-generation files without deleting those local files.
- Verify the existing board in the signed-in browser, move partially completed task #7 to In Progress, and fill the empty board description/README with scope, links and status rules.

## Verified board state

The private board linked from this repository contains the seven existing issues. After synchronization:

| Column | Issues | Reason |
|---|---|---|
| Todo | #4, #5, #6 | Tutor discussion, real group review and recording the selected video still require group activity |
| In Progress | #2, #7 | Model/export preparation is complete, while group review/contribution evidence and marking-team access checks remain open |
| Done | #1, #3 | Preserve the existing completed setup and initial-requirements tasks |

The board now has a scope description, artifact links and status rules. Issue titles updated from the corrected repository issues. The [saved board screenshot](board-2026-10-28.png) records the observed state; it does not prove marking-team access or completed student contributions.

GitHub API Projects permission remains unavailable with the current credential; browser access was sufficient to verify and update the existing board without expanding token permissions.

## Remaining human checks

| Action | Tracking / completion evidence |
|---|---|
| Review the full enterprise model and F1/F2 scope together | [#5](https://github.com/jensenxie-max/DESD-Group-26/issues/5); use the [review template](../../meetings/Sprint-1-Review-Template.md), record actual attendees/findings |
| Obtain tutor agreement on both functions | [#4](https://github.com/jensenxie-max/DESD-Group-26/issues/4); record the actual decision and any boundary changes |
| Verify marking-team repository and board access | [#7](https://github.com/jensenxie-max/DESD-Group-26/issues/7); the [existing board](https://github.com/users/jensenxie-max/projects/2) was checked while signed in as the owner; access by the marking team still requires confirmation |
| Record actual student contributions | Link genuine commits, review notes and sprint participation; agree/sign the required Contribution Matrix when appropriate |
| Record the selected Sprint 1 video | [#6](https://github.com/jensenxie-max/DESD-Group-26/issues/6); all members introduce themselves and present; MP4 maximum 10 minutes; Standup 3 attended separately |
| Submit the mandatory Sprint 1 ZIP | [#7](https://github.com/jensenxie-max/DESD-Group-26/issues/7); links document, MP4 and slides if used; before 29 October 2026, 14:00 UK time |
| Check for later module announcements | Confirm the actual sprint-review arrangements and any changed submission instructions with the module team |

These are open checks, not evidence that reviews or approvals have taken place.

## Current assessment submission instructions

The module-team announcement supplied by the user on 28 October 2026 is now the governing source for Sprint 1 review arrangements. See the [requirements record](submission-instructions.md).

- Every group submits one ZIP to Blackboard before **Thursday, 29 October 2026, 14:00 UK time**, regardless of presentation format.
- The group selected **Option B: pre-recorded MP4, maximum 10 minutes**. All members must present with clear audio/video and introduce their full name/student ID.
- The ZIP contains the repository/project-management links document, MP4, and slides if used. Written report not required; slides optional.
- Show technical progress and project management, including Kanban, allocation, planning and tracking. Video groups still attend Standup 3, marked separately.
- In-class presentation is an alternative only after whole-group agreement and arranging it with tutors during the practical session in the week commencing 26 October. In-class members must be physically present and submit their ZIP before presenting.
- Repository and board access by the marking team remains to be verified; no public exposure or collaborator change is made by this update.
- The 10 December Task 1 final date in the older general brief is distinct from this Sprint 1 deadline.

The prior PDF-only change to video/ZIP tasks was premature and is corrected in the current README, board notes and issues. Earlier Git commits retain the historical wording; it is not the current submission instruction.

## Contribution and change provenance

The 28 October model preparation and repository synchronization were performed with assistant support in this session. The Git account submitting the baseline identifies the committer, not proof that all model content was independently authored by that student. Planned names in the backlog remain planned owners. Group review, tutor agreement and individual student contribution must be supported by their own evidence.

Earlier repository history and the existing requirements workbook are retained. No completed review meeting, tutor approval, member contribution percentage or signature is created by this synchronization.

## Export and sync procedure

1. Open the existing Camunda diagram and confirm the intended latest saved version.
2. After changes, review its Design problems and inspect the full exported diagram.
3. Save a named Camunda version, then download BPMN XML and a PNG of that same version.
4. Replace only `models/strategic/Strategic-BPMN.bpmn` and `models/strategic/Strategic-BPMN.png` with the new exports.
5. Update the repository scope/plan notes when requirements or decisions changed; cloud and repository README documents are separate copies.
6. Review `git status` and the diff. Commit only the intended files with an accurate change description, then push normally. If the remote has changed, fetch and integrate those changes before pushing; do not force-push.
7. Update the relevant issue and board status according to real completion, and verify the pushed commit in GitHub.

No automatic cloud-to-GitHub synchronization is configured.
