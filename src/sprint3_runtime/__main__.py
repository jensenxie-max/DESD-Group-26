"""Commands for the isolated Sprint 3 models and their local SQLite state."""

import argparse
import json
import logging
import os
from pathlib import Path
import subprocess
import sys
import uuid

from sprint2_runtime.samples import listing_details, seed_product

from .api import CamundaClient
from .store import Store
from .worker import DEFAULT_MANIFEST, Worker


def output(value):
    print(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False))


def parser():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--url", help="Camunda REST base URL, default CAMUNDA_REST_URL or http://localhost:8080/v2")
    cli.add_argument("--db", default="work/sprint3-runtime.sqlite3")
    cli.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    commands = cli.add_subparsers(dest="command", required=True)
    for name in ("health", "deploy", "inspect", "outbox"):
        commands.add_parser(name)
    demo = commands.add_parser("demo", help="Run the real-engine validation suite in a fresh isolated database")
    demo.add_argument("--date", default="2026-11-26")
    worker = commands.add_parser("worker")
    worker.add_argument("--once", action="store_true")
    worker.add_argument("--cycles", type=int)
    worker.add_argument("--interval", type=float, default=0.5)
    for name in ("seed", "sample", "start-f1", "start-f2", "order", "season"):
        command = commands.add_parser(name)
        command.add_argument("--date", required=True, help="Explicit business date YYYY-MM-DD")
        command.add_argument("--product-id", default=None if name == "start-f1" else "demo-carrots")
        command.add_argument("--producer-id", default="demo-producer")
        command.add_argument("--request-id")
        if name == "start-f1":
            command.add_argument("--details", type=Path)
            command.add_argument("--verification-outcome", choices=("verified", "invalid", "unavailable"))
        if name == "order":
            command.add_argument("--deduction", required=True, type=int)
            command.add_argument("--change-id", required=True)
            command.add_argument("--expected-version", type=int)
        if name == "season":
            command.add_argument("--expected-version", type=int)
    tasks = commands.add_parser("tasks")
    tasks.add_argument("--instance-key", required=True)
    complete = commands.add_parser("complete-task")
    complete.add_argument("--task-key", required=True)
    complete.add_argument("--variables", required=True, type=Path)
    review = commands.add_parser("follow-up-complete", help="Complete the actual follow-up user task through REST")
    review.add_argument("--task-key", required=True)
    review.add_argument("--decision", required=True, choices=("retry", "cancel"))
    review.add_argument("--outcome", choices=("verified", "invalid", "unavailable"))
    review.add_argument("--notes", default="")
    reconcile = commands.add_parser("reconcile-message", help="Record a verified operator decision; resolve the engine incident separately")
    reconcile.add_argument("--operation-id", required=True)
    reconcile.add_argument("--resolution", required=True, choices=("accepted", "not_sent"))
    reconcile.add_argument("--evidence", required=True)
    return cli


def message_name(manifest_path, message_id):
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8-sig"))
    return manifest["messages"][message_id]["name"]


def main():
    args = parser().parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", stream=sys.stderr)
    if args.command == "demo":
        if Path(args.manifest).resolve() != DEFAULT_MANIFEST.resolve():
            raise ValueError("The validation suite uses the repository Sprint 3 manifest")
        env = os.environ.copy()
        if args.url:
            env["CAMUNDA_REST_URL"] = args.url
        root = Path(__file__).resolve().parents[2]
        result = subprocess.run([sys.executable, "-B", str(root / "tools/run_sprint3_validation.py"), "--date", args.date],
                                cwd=root, env=env)
        if result.returncode:
            raise SystemExit(result.returncode)
        return
    store = Store(args.db)
    try:
        if args.command == "inspect":
            output(store.snapshot())
            return
        if args.command == "outbox":
            output(store.snapshot()["messageOutbox"])
            return
        if args.command == "reconcile-message":
            output(store.reconcile_message(args.operation_id, args.resolution, args.evidence))
            return
        if args.command == "sample":
            output({"details": listing_details(args.date), "allergenEntries": []})
            return
        if args.command == "seed":
            product = seed_product(args.date, args.product_id, args.producer_id)
            result = store.once("seed:" + args.product_id, "seed",
                                lambda: (store.insert_product(product, "seed"), {"product": product})[1])
            output(result | {"scope": "Local SQLite fixture; no Camunda instance was executed"})
            return
        client = CamundaClient.from_env(args.url)
        if args.command == "health":
            output(client.request("GET", "/topology"))
        elif args.command == "deploy":
            path = Path(args.manifest)
            manifest = json.loads(path.read_text(encoding="utf-8-sig"))
            resources = [path.parent / model["resource"] for model in manifest["models"].values()]
            resources += [path.parent / form for form in manifest["forms"]]
            output(client.deploy(resources))
        elif args.command == "worker":
            worker = Worker(client, store, manifest_path=args.manifest)
            if args.once:
                output(worker.run_once())
            else:
                worker.run(interval=args.interval, max_cycles=args.cycles)
        elif args.command == "tasks":
            output(client.request("POST", "/user-tasks/search",
                                  {"filter": {"processInstanceKey": args.instance_key, "state": "CREATED"}}))
        elif args.command == "complete-task":
            variables = json.loads(args.variables.read_text(encoding="utf-8-sig"))
            if not isinstance(variables, dict):
                raise ValueError("Task variables file must contain a JSON object")
            output(client.complete_user_task(args.task_key, variables))
        elif args.command == "follow-up-complete":
            if args.decision == "retry" and args.outcome is None:
                raise ValueError("Retry requires --outcome naming the simulated provider response")
            variables = {"followUpDecision": args.decision, "followUpNotes": args.notes}
            if args.outcome:
                variables["verificationOutcome"] = args.outcome
            output(client.complete_user_task(args.task_key, variables))
        else:
            request_id = args.request_id or str(uuid.uuid4())
            product_id = args.product_id or "listing-" + request_id
            variables = {"requestId": request_id, "productId": product_id,
                         "producerId": args.producer_id, "businessDate": args.date}
            if args.command == "start-f1":
                variables["details"] = json.loads(args.details.read_text(encoding="utf-8-sig")) if args.details else listing_details(args.date)
                if args.verification_outcome:
                    variables["verificationOutcome"] = args.verification_outcome
                result = client.start("F1_ProducerProcess_S3", variables)
            elif args.command == "start-f2":
                # Expected missing/ownership errors are handled in the actual process.
                variables["update"] = {"source": "producer", "producerId": args.producer_id}
                result = client.start("F2_ProducerProcess_S3", variables)
            else:
                product = store.get_product(product_id)
                update = {"source": "order" if args.command == "order" else "season-check",
                          "expectedVersion": args.expected_version if args.expected_version is not None else product["version"]}
                if args.command == "order":
                    update |= {"confirmed": True, "changeId": args.change_id, "deduction": args.deduction}
                variables["update"] = update
                result = client.publish(message_name(args.manifest, "F2_Message_UpdateRequest"), request_id,
                                        variables, "request:" + request_id)
            output({"requestId": request_id, "productId": product_id, "engineResponse": result})
    finally:
        store.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
