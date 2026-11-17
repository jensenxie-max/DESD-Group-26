# Sprint 2 operational models

`F1-Operational.bpmn` and `F2-Operational.bpmn` add Camunda 8.10 execution configuration to the saved responsibility diagrams from 17 November. Each file contains the producer and marketplace processes. F1 also shows the certification provider as an external black-box participant.

The original node IDs, business branches, pools, lanes, layout and three user-task input/output mappings are preserved. Each user task uses its original Form ID with `bindingType="deployment"`; deploy both BPMN files and the three files in `forms/` in the same resource deployment.

## Execution contract

`execution-manifest.json` lists every task, message and allowed payload field. It is consumed by the accompanying worker rather than treating graphical message flows as automatic transport.

| Configuration | Meaning |
| --- | --- |
| `desd.business` + `action` header | Execute the business operation identified by the existing BPMN node ID. |
| `desd.message` + `action` / `messageName` headers | Publish the explicit message and complete the send task after publication succeeds. |
| `requestId` | Unique string per producer request; retained across both pools and the F1 correction loop. |
| Message TTL: 3,600,000 ms | Buffer replies that arrive before the receiving token opens its subscription. |
| Message ID: send-task job key | Reuse the ID on retries of the same send task. Each correction-loop iteration creates a new job. |
| Receive output mappings | Propagate only the fields in the message contract, keeping the participants' other variables separate. |

F1 starts at `F1_ProducerProcess`; the `Product details` message starts `F1_Process`. F2 starts at `F2_ProducerProcess` for a producer edit. Order and seasonal updates publish `F2 update request` directly with `update.source` set to `order` or `season-check`, bypassing the producer form.

Use a distinct `requestId` for every new request and pass the explicit `businessDate`, `productId` and producer identity required by the worker. These identifiers are demonstration inputs, not authentication. The certification worker uses a documented simulated provider outcome; the external pool does not imply connection to a real certification authority.

## Rebuild and static validation

From the repository root:

```powershell
python tools/build_sprint2_executable.py
python tools/build_sprint2_executable.py --check
```

The checks compare the generated files with the saved source graph and layout, verify all gateway conditions, job definitions, message subscriptions, allowed receive mappings and form bindings, and verify that the copied Forms are byte-for-byte unchanged. Unknown decision values produce an engine incident rather than an undocumented default route.

Passing these checks is not evidence of a deployed or completed engine instance. Deployment, human-task completion, cross-pool message delivery and the resulting database state must also be demonstrated with Camunda running.

## Known limitations for the Sprint 2 demonstration

- The two message flows between F1 and the black-box certification pool express the external interaction in the business design. At runtime, F1_Verify calls the local simulated adapter inside the business worker. No independent certification process is deployed and no real authority is contacted. The recorded verificationMode is "mock"; DEMO-VALID, DEMO-INVALID and DEMO-UNAVAILABLE are demonstration fixtures.
- F2's original graph has no error-response branch before stock context is delivered. The CLI checks that the product exists and its owner matches before starting a producer request. If data becomes unavailable after that check, or an invalid request bypasses the CLI, F2_Load fails with a visible incident and worker error. The producer remains waiting for context until the incident is corrected or the demo instances are cancelled; this is not an automatic rejection response.
- Missing or malformed integration variables and unsupported source/outcome values produce incidents. The worker never invents a default business decision. Seasonal checks require explicit invocation; there is no running seasonal scheduler.
- Producer identity and confirmed orders are supplied demonstration inputs. Authentication, payment verification, full food-information compliance and production retry/reminder policies remain outside this runtime.
- SQLite and the customer-availability projection support a local demonstration. They are not a deployed multi-user marketplace or an external customer application.

## Configuration references

- [Exclusive gateways](https://docs.camunda.io/docs/components/modeler/bpmn/exclusive-gateways/)
- [Message events and correlation](https://docs.camunda.io/docs/components/modeler/bpmn/message-events/)
- [Send-task workers](https://docs.camunda.io/docs/components/modeler/bpmn/send-tasks/)
- [User tasks, mappings and form deployment bindings](https://docs.camunda.io/docs/components/modeler/bpmn/user-tasks/)
READABLE DIAGRAMS
F1-Operational.svg and F2-Operational.svg are the native Camunda exports of
the 17 November responsibility revision. The executable copies preserve that
layout and visible business structure. The images do not prove deployment or
display all XML execution settings.

