# Week-one implementation traceability

The selected F1/F2 scope and R1–R10 requirement references remain those used in Sprint 2. The rows below extend the existing analysis to the new implementation and executable checks. New process IDs use `_S3`; node IDs are retained where the behaviour is unchanged.

| Requirement or design concern | Stakeholder / strategic link | Operational route | Implementation | Execution evidence |
|---|---|---|---|---|
| R4: invalid product details require correction | D01/D02; CAT_T1; Task_F1 | F1_Validate → F1_Correction → F1_Edit → F1_ReceiveCorrected | Existing listing rules reused by S3 BusinessHandlers | correction-engine.json |
| R5/R6: a claimed certificate is verified before publication | D13/D09; CAT_T_VERIFY/CAT_Q1; Task_F1 | F1_Verify → F1_Result → F1_Publish | S3 BusinessHandlers._handle delegates the validated publication rule | organic-engine.json; invalid-certificate-engine.json |
| R10: unavailable verification and follow-up | D13; CAT_Q1/CAT_Q2; Task_F1/Task_CatalogResponse | F1_Pending → F1_ReviewPending → retry to F1_Verify, or F1_ClosePending → cancellation outcome | src/sprint3_runtime/business.py; Store.set_follow_up; follow_up_events | pending-retry-engine.json; pending-cancel-engine.json; pending-invalid-correction-engine.json |
| R7: stock/date update uses the product context | D03/D04; INV_T1/INV_R; Task_F2 | F2_Load → context gateway → F2_SendContext → F2_EnterStockChange | S3 BusinessHandlers F2_Load and existing inventory rules | happy-engine.json |
| Context rejection before a stock form | A03 participant responsibility; INV_T1; Task_F2 | F2_Load → F2_RejectContext → producer rejection end | Store.find_product; contextAvailable/contextError; restricted rejection payload | product_not_found-engine.json; owner_mismatch-engine.json |
| R8/R9: zero stock and seasonal boundaries | D04/D09; INV_G/INV_Q1; Task_F2/Task_Visibility | F2_Assess → available/unavailable → F2_Save → F2_Sync | Existing sale_available and inventory business rules; SQLite version/projection updates | boundaries-engine.json |
| Invalid quantity/date input | R7/R10; INV_T1; Task_F2 | F2_Producer → F2_RejectInput | Shared inventory validation retained | invalid-input-engine.json |
| Duplicate order / conflicting version | A01; INV_Q1/INV_Q2; Task_F2 | F2_Order / F2_Save → applicable/confirmed decision | Existing change-ID and optimistic-version checks reused | boundaries-engine.json |
| Committed update survives a worker process exit | A01 accuracy / prompt-completion tension | F2_Save job expires before completion, new worker completes the same job | Store.once operation journal reused by S3 Worker | worker-recovery-engine.json |
| Ambiguous message delivery is visible | A03 participant exchanges; D01/D02/D03/D04 | S3 send-task jobs and requestId correlation | Worker.dispatch; durable message_outbox; explicit operator reconciliation | test_sprint3_runtime.py; not claimed as a complete real-engine network-failure campaign |

Evidence filenames above are under `docs/sprint-3/evidence/`. Tests are under `tests/`. All engine evidence is generated against the current Sprint 3 deployment; historical Sprint 2 records are not relabelled as new runs.

The context rejection and recovery mechanisms are implementation decisions. They are not additional requirements attributed to the case study. Producer registration remains a precondition; the prototype does not implement production identity or payment verification.
