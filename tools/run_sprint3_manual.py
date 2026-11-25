"""Start the isolated S3 walkthrough and wait for real Tasklist interaction."""
import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.error
import uuid
import webbrowser

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from sprint2_runtime.api import CamundaClient
from sprint2_runtime.demo import EngineDemo
from sprint2_runtime.samples import listing_details
from sprint3_runtime.store import Store
from sprint3_runtime.worker import Worker
from sprint3_runtime.exercise import exclusive_exercise

MANIFEST = ROOT / "models/sprint3/execution-manifest.json"
STATE = ROOT / "work/sprint3-manual-latest.json"


def ensure_engine(client):
    try:
        client.request("GET", "/topology")
        return
    except (urllib.error.URLError, ConnectionError, TimeoutError):
        pass
    runtime = Path(os.environ.get("CAMUNDA_RUN_DIR", str(Path.home() / "Downloads/camunda8-run-8.10-windows-x86_64/c8run-8.10.9")))
    if not (runtime / "c8run.exe").is_file():
        raise RuntimeError("Set CAMUNDA_RUN_DIR to the installed official Camunda Run directory")
    env = os.environ.copy()
    env.update(SERVER_ADDRESS="127.0.0.1", MANAGEMENT_SERVER_ADDRESS="127.0.0.1",
               CAMUNDA_API_GRPC_ADDRESS="127.0.0.1", C8RUN_SECRETS_DIR=str(ROOT / "work/c8run-secrets"),
               C8RUN_TENANTS_FILE=str(ROOT / "work/c8run-tenants.json"))
    with (ROOT / "work/sprint3-engine-start.log").open("ab") as log:
        startup = subprocess.Popen([str(runtime / "c8run.exe"), "start", "--detached", "--no-browser", "--disable-connectors"],
            cwd=runtime, env=env, stdout=log, stderr=log, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    deadline = time.monotonic() + 150
    while time.monotonic() < deadline:
        try:
            client.request("GET", "/topology")
            return
        except (urllib.error.URLError, ConnectionError, TimeoutError):
            if startup.poll() not in (None, 0):
                raise RuntimeError("Camunda startup failed; see work/sprint3-engine-start.log")
            time.sleep(1)
    raise TimeoutError("Camunda did not become ready")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--pending", action="store_true", help="Include the real certification follow-up user task")
    args = parser.parse_args()
    (ROOT / "work").mkdir(exist_ok=True)
    client = CamundaClient.from_env(os.environ.get("CAMUNDA_REST_URL", "http://127.0.0.1:8080/v2"))
    ensure_engine(client)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    deployment = client.deploy([MANIFEST.parent / m["resource"] for m in manifest["models"].values()] +
                               [MANIFEST.parent / f for f in manifest["forms"]])
    run_id = str(uuid.uuid4())
    day = datetime.now(timezone(timedelta(hours=8))).date().isoformat()
    store = Store(ROOT / "work/sprint3-runtime.sqlite3")
    demo = EngineDemo(client, store, timeout=3600, manifest_path=MANIFEST)
    demo.worker = Worker(client, store, manifest_path=MANIFEST)
    state = {"runId": run_id, "deployment": deployment, "engineExecuted": True,
             "formInteraction": "Manual Tasklist; launcher never completes user tasks", "status": "starting"}
    def record(**changes):
        state.update(changes)
        STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    try:
        base = {"productId": "manual-s3-" + run_id, "producerId": "demo-producer", "businessDate": day}
        details = listing_details(day)
        if args.pending:
            details |= {"organicClaim": True, "certificationReference": "DEMO-UNAVAILABLE"}
        f1 = client.start("F1_ProducerProcess_S3", base | {"requestId": "f1-" + run_id, "details": details})
        task = demo.user_task(f1["processInstanceKey"], "F1_Submit")
        record(status="waiting_f1", productId=base["productId"], f1InstanceKey=f1["processInstanceKey"], f1TaskKey=task["userTaskKey"])
        print("Open http://localhost:8080/tasklist (demo / demo). Assign and complete the S3 product task.", flush=True)
        if args.pending:
            print("Then complete Review verification follow-up: retry with the controlled verified fixture, or cancel.", flush=True)
        if not args.no_browser:
            webbrowser.open("http://localhost:8080/tasklist")
        f1_done = demo.completed(f1["processInstanceKey"])
        try:
            before = store.get_product(base["productId"])
        except ValueError:
            record(status="ended_without_publication", f1Completed=f1_done, state=store.snapshot())
            print("The request ended without publication. Inspect its cancellation in Operate.")
            return
        f2 = client.start("F2_ProducerProcess_S3", base | {"requestId": "f2-" + run_id,
                          "update": {"source": "producer", "producerId": "demo-producer"}})
        task = demo.user_task(f2["processInstanceKey"], "F2_EnterStockChange")
        record(status="waiting_f2", f1Completed=f1_done, beforeStockUpdate=before,
               f2InstanceKey=f2["processInstanceKey"], f2TaskKey=task["userTaskKey"])
        print("Complete the new S3 stock task: set quantity to 6 and keep the sale dates.", flush=True)
        f2_done = demo.completed(f2["processInstanceKey"])
        producers = {str(f1["processInstanceKey"]), str(f2["processInstanceKey"])}
        platforms = [demo.completed(k) for k in sorted({e["processInstanceKey"] for e in demo.worker.events} - producers)]
        record(status="completed", f2Completed=f2_done, platformInstances=platforms,
               product=store.get_product(base["productId"]), state=store.snapshot())
        print("Completed. Result: work/sprint3-manual-latest.json", flush=True)
    except BaseException as exc:
        record(status="stopped" if isinstance(exc, KeyboardInterrupt) else "failed", error=str(exc))
        raise
    finally:
        store.close()


if __name__ == "__main__":
    with exclusive_exercise():
        main()
