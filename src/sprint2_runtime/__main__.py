"""Command-line entry point. Run with PYTHONPATH=src and python -m sprint2_runtime.

Local preparation: seed, sample, inspect. Engine operations: deploy, worker,
start-f1, start-f2, order, season, tasks, complete-task. Credentials are read only
from CAMUNDA_TOKEN or CAMUNDA_USERNAME/CAMUNDA_PASSWORD; never command arguments.
"""

import argparse
import json
import logging
from pathlib import Path
import sys
import uuid

from .api import CamundaClient
from .demo import EngineDemo
from .samples import listing_details, seed_product
from .store import Store
from .worker import DEFAULT_MANIFEST, Worker


def output(value):
    print(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False))


def parser():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--url", help="Camunda REST base URL, default CAMUNDA_REST_URL or http://localhost:8080/v2")
    cli.add_argument("--db", default="work/sprint2-runtime.sqlite3", help="SQLite store used by worker and local inspection")
    cli.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    commands = cli.add_subparsers(dest="command", required=True)
    commands.add_parser("inspect", help="Read local SQLite products, projection and task-operation records")
    commands.add_parser("deploy", help="Deploy both BPMN models and all three forms in one request")
    health = commands.add_parser("health", help="Read actual Camunda topology")
    worker = commands.add_parser("worker", help="Activate, perform and complete/fail actual engine jobs")
    worker.add_argument("--once", action="store_true")
    worker.add_argument("--cycles", type=int)
    worker.add_argument("--interval", type=float, default=0.5)
    for name in ("seed", "sample", "start-f1", "start-f2", "order", "season"):
        command = commands.add_parser(name)
        command.add_argument("--date", required=True, help="Explicit business date YYYY-MM-DD")
        command.add_argument("--product-id", default="demo-carrots" if name != "start-f1" else None)
        command.add_argument("--producer-id", default="demo-producer")
        command.add_argument("--request-id")
        if name == "start-f1":
            command.add_argument("--details", type=Path, help="Optional JSON file to prefill the actual user form")
            command.add_argument("--verification-outcome", choices=("verified", "invalid", "unavailable"),
                                 help="Mock certification response for the demo only")
        if name == "order":
            command.add_argument("--deduction", required=True, type=int)
            command.add_argument("--change-id", required=True)
            command.add_argument("--expected-version", type=int)
        if name == "season":
            command.add_argument("--expected-version", type=int)
    tasks = commands.add_parser("tasks", help="Search actual open user tasks for one process instance")
    tasks.add_argument("--instance-key", required=True)
    complete = commands.add_parser("complete-task", help="Complete a real user task from an explicit JSON payload")
    complete.add_argument("--task-key", required=True)
    complete.add_argument("--variables", required=True, type=Path)
    demo = commands.add_parser("demo", help="Run a real engine exercise; requires prior deployment, no separate worker needed")
    demo.add_argument("--date", required=True)
    demo.add_argument("--scenario", choices=("happy", "correction", "organic", "pending", "boundaries", "invalid-input", "invalid-certificate"), default="happy")
    demo.add_argument("--timeout", type=int, default=90)
    return cli


def main():
    args = parser().parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", stream=sys.stderr)
    store = Store(args.db)
    try:
        if args.command == "inspect":
            output(store.snapshot())
            return
        if args.command == "sample":
            output({"details": listing_details(args.date), "allergenEntries": []})
            return
        if args.command == "seed":
            product = seed_product(args.date, args.product_id, args.producer_id)
            result = store.once("seed:" + args.product_id, "seed", lambda: (store.insert_product(product, "seed"), {"product": product})[1])
            output(result | {"note": "Local SQLite seed only; no Camunda process has run."})
            return
        client = CamundaClient.from_env(args.url)
        if args.command == "health":
            output(client.request("GET", "/topology"))
        elif args.command == "deploy":
            path = Path(args.manifest)
            manifest = json.loads(path.read_text(encoding="utf-8-sig"))
            resources = [path.parent / m["resource"] for m in manifest["models"].values()]
            resources += [path.parent / f for f in manifest["forms"]]
            output(client.deploy(resources))
        elif args.command == "worker":
            worker = Worker(client, store, manifest_path=args.manifest)
            if args.once:
                output(worker.run_once())
            else:
                worker.run(interval=args.interval, max_cycles=args.cycles)
        elif args.command == "tasks":
            output(client.request("POST", "/user-tasks/search", {"filter": {"processInstanceKey": args.instance_key, "state": "CREATED"}}))
        elif args.command == "complete-task":
            variables = json.loads(args.variables.read_text(encoding="utf-8-sig"))
            if not isinstance(variables, dict):
                raise ValueError("Task variables file must contain a JSON object")
            output(client.complete_user_task(args.task_key, variables))
        elif args.command == "demo":
            output(EngineDemo(client, store, timeout=args.timeout, manifest_path=args.manifest).run(args.date, args.scenario))
        else:
            request_id = args.request_id or str(uuid.uuid4())
            product_id = args.product_id or "listing-" + request_id
            variables = {"requestId": request_id, "productId": product_id, "producerId": args.producer_id, "businessDate": args.date}
            if args.command == "start-f1":
                variables["details"] = json.loads(args.details.read_text(encoding="utf-8-sig")) if args.details else listing_details(args.date)
                if args.verification_outcome:
                    variables["verificationOutcome"] = args.verification_outcome
                result = client.start("F1_ProducerProcess", variables)
            elif args.command == "start-f2":
                product = store.get_product(product_id)
                if product["producerId"] != args.producer_id:
                    raise ValueError("Cannot start F2: producer ID does not match the stored product owner")
                variables["update"] = {"source": "producer", "producerId": args.producer_id}
                result = client.start("F2_ProducerProcess", variables)
            else:
                product = store.get_product(product_id)
                update = {"source": "order" if args.command == "order" else "season-check",
                          "expectedVersion": args.expected_version if args.expected_version is not None else product["version"]}
                if args.command == "order":
                    update |= {"confirmed": True, "changeId": args.change_id, "deduction": args.deduction}
                variables["update"] = update
                result = client.publish("F2 update request", request_id, variables, "request:" + request_id)
            output({"requestId": request_id, "productId": product_id, "engineResponse": result})
    finally:
        store.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
