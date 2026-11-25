# Sprint 3 week-one process models

| Resource | Purpose |
|---|---|
| `F1-Sprint3.bpmn` / `F1-Sprint3.svg` | Product validation, correction, publication and verification follow-up |
| `F2-Sprint3.bpmn` / `F2-Sprint3.svg` | Stock/date entry, confirmed-order changes, seasonal checks and rejected context requests |
| `forms/` | The three existing input forms plus the verification follow-up form |
| `execution-manifest.json` | Deployable resources, process IDs, isolated job types and message payload contracts |

The BPMN files are editable in Camunda. The SVG files are reading views generated from the same diagram coordinates. Producer activities are in the upper participant; Marketplace activities are in the lower participant. F1 keeps information correction and verification follow-up below the normal validation/publication row. F2 separates producer input, order processing and seasonal checks before the shared availability/commit path. All connections use orthogonal routes and avoid crossing unrelated flow nodes.

F1 now keeps an unavailable verification request at `F1_ReviewPending`. Catalogue support chooses **Retry verification** or **Close without publication**. Retry always returns through `F1_Verify`; the review task cannot publish a listing itself. The provider result on this form is an explicit simulated response. Closing the request passes through `F1_ClosePending` before the producer receives its closed outcome.

F2 now replies to a rejected context request rather than leaving the producer waiting for its stock form. `F2_ContextAvailable` directs expected rejection outcomes to `F2_RejectContext`; `F2_ProducerContextAvailable` prevents the rejected request from opening the input form. A rejection clears product/version context. Technical contract or infrastructure failures can still produce incidents and need operational recovery.

Sprint 3 process IDs end in `_S3`, job types are `desd.s3.business` and `desd.s3.message`, and message names begin with `S3 `. These separate the revision from deployed Sprint 2 instances. Deploy both BPMN files and every form listed in the manifest together. Form bindings select the form in the same deployment.

Rebuild with `python tools/build_sprint3_models.py`; validate without writing with `python tools/build_sprint3_models.py --check`. The command reads the retained Sprint 2 resources in `models/operational/`; it does not rewrite those baselines. A successful static check does not prove a deployed or completed process instance. Use the Sprint 3 runtime validation records for actual execution results.
