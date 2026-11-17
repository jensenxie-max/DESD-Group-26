"""Launch the local F1/F2 walkthrough and wait for actual Tasklist input."""
import argparse
from datetime import datetime, timedelta, timezone
import json
import logging
import msvcrt
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.error
import uuid
import webbrowser

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT / "src"))
from sprint2_runtime.api import CamundaClient
from sprint2_runtime.demo import EngineDemo
from sprint2_runtime.samples import listing_details
from sprint2_runtime.store import Store

WORK = ROOT / "work"
STATE = WORK / "manual-demo-latest.json"
TASKLIST = "http://localhost:8080/tasklist"


def record(state, **changes):
    state.update(changes)
    state["updatedAt"] = datetime.now(timezone.utc).isoformat()
    temp = STATE.with_suffix(".tmp")
    temp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(STATE)


def ensure_engine(client):
    try:
        client.request("GET", "/topology")
        return
    except (urllib.error.URLError, ConnectionError, TimeoutError):
        pass
    runtime = Path(os.environ.get("CAMUNDA_RUN_DIR", str(Path.home() / "Downloads" /
                   "camunda8-run-8.10-windows-x86_64" / "c8run-8.10.9")))
    executable = runtime / "c8run.exe"
    if not executable.is_file():
        raise RuntimeError("Cannot find c8run.exe. Set CAMUNDA_RUN_DIR to the extracted Windows package.")
    env = os.environ.copy()
    env.update(SERVER_ADDRESS="127.0.0.1", MANAGEMENT_SERVER_ADDRESS="127.0.0.1",
               CAMUNDA_API_GRPC_ADDRESS="127.0.0.1",
               C8RUN_SECRETS_DIR=str(WORK / "c8run-secrets"),
               C8RUN_TENANTS_FILE=str(WORK / "c8run-tenants.json"))
    print("Starting Camunda. First startup can take about a minute.", flush=True)
    with (WORK / "manual-engine-start.log").open("ab") as log:
        startup = subprocess.Popen([str(executable), "start", "--detached", "--no-browser",
                                    "--disable-connectors"], cwd=runtime, env=env,
                                   stdout=log, stderr=log, creationflags=subprocess.CREATE_NO_WINDOW)
    deadline = time.monotonic() + 150
    while time.monotonic() < deadline:
        try:
            client.request("GET", "/topology")
            return
        except (urllib.error.URLError, ConnectionError, TimeoutError):
            if startup.poll() not in (None, 0):
                raise RuntimeError("Camunda startup failed; see work/manual-engine-start.log")
            time.sleep(1)
    raise RuntimeError("Camunda did not become ready; see work/manual-engine-start.log")


def run(no_browser=False):
    WORK.mkdir(exist_ok=True)
    with (WORK / "manual-demo.lock").open("a+b") as lock:
        lock.seek(0, os.SEEK_END)
        if lock.tell() == 0:
            lock.write(b"0")
            lock.flush()
        lock.seek(0)
        try:
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            print("A manual walkthrough is already running. Continue its Tasklist forms.")
            if not no_browser:
                webbrowser.open(TASKLIST)
            return
        state = {"status": "starting", "runId": str(uuid.uuid4()),
                 "formInteraction": "Tasklist UI; this launcher never completes user tasks"}
        record(state)
        store = None
        try:
            client = CamundaClient("http://127.0.0.1:8080/v2")
            ensure_engine(client)
            manifest_path = ROOT / "models/operational/execution-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
            resources = [manifest_path.parent / model["resource"] for model in manifest["models"].values()]
            resources += [manifest_path.parent / form for form in manifest["forms"]]
            deployment = client.deploy(resources)
            store = Store(WORK / "sprint2-runtime.sqlite3")
            demo = EngineDemo(client, store, timeout=3600, manifest_path=manifest_path)
            business_date = datetime.now(timezone(timedelta(hours=8))).date().isoformat()
            product_id = "manual-" + state["runId"]
            base = {"productId": product_id, "producerId": "demo-producer", "businessDate": business_date}
            f1_request = "f1-" + state["runId"]
            f1 = client.start("F1_ProducerProcess", base | {"requestId": f1_request,
                              "details": listing_details(business_date)})
            task = demo.user_task(f1["processInstanceKey"], "F1_Submit")
            record(state, status="waiting_f1", productId=product_id, businessDate=business_date,
                   deploymentKey=deployment["deploymentKey"], f1InstanceKey=f1["processInstanceKey"],
                   f1TaskKey=task["userTaskKey"])
            print("\nSTEP 1: Open " + TASKLIST + " (login: demo / demo).", flush=True)
            print("Open Submit product details. Assign to me, then Complete task.", flush=True)
            print("Keep this window open. F2 appears after F1 is published.", flush=True)
            if not no_browser:
                webbrowser.open(TASKLIST)
            f1_completed = demo.completed(f1["processInstanceKey"])
            try:
                before = store.get_product(product_id)
            except ValueError:
                record(state, status="f1_not_published", f1Completed=f1_completed)
                print("F1 ended without publication. Inspect its outcome in Operate; F2 was not started.")
                return
            f2_request = "f2-" + state["runId"]
            f2 = client.start("F2_ProducerProcess", base | {"requestId": f2_request,
                              "update": {"source": "producer", "producerId": "demo-producer"}})
            task = demo.user_task(f2["processInstanceKey"], "F2_EnterStockChange")
            record(state, status="waiting_f2", f1Completed=f1_completed, beforeStockUpdate=before,
                   f2InstanceKey=f2["processInstanceKey"], f2TaskKey=task["userTaskKey"])
            print("\nSTEP 2: Open the new F2 task in Tasklist. Refresh if it is not listed.", flush=True)
            print(f"Assign to me; change New quantity (whole units) from {before['quantity']} to 6; keep the dates; Complete Task.", flush=True)
            f2_completed = demo.completed(f2["processInstanceKey"])
            requests = {f1_request, f2_request}
            events = [event for event in demo.worker.events if event.get("requestId") in requests]
            producer_keys = {str(f1["processInstanceKey"]), str(f2["processInstanceKey"])}
            platform_keys = {event["processInstanceKey"] for event in events} - producer_keys
            platforms = [demo.completed(key) for key in sorted(platform_keys)]
            after = store.get_product(product_id)
            projection = next((row for row in store.snapshot()["customerAvailability"]
                               if row["product_id"] == product_id), None)
            record(state, status="completed", f2Completed=f2_completed, platformInstances=platforms,
                   product=after, customerAvailability=projection, completedJobs=events, engineExecuted=True)
            print(f"\nFinished. Stock: {before['quantity']} -> {after['quantity']}; available: {after['available']}")
            print("View completed instances: http://localhost:8080/operate/processes?completed=true")
            print("Result: work/manual-demo-latest.json")
        except BaseException as exc:
            record(state, status="stopped" if isinstance(exc, KeyboardInterrupt) else "failed", error=str(exc))
            raise
        finally:
            if store:
                store.close()
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.WARNING)
    try:
        run(args.no_browser)
    except KeyboardInterrupt:
        print("Walkthrough stopped. Existing tasks remain in Camunda.")
    except Exception as exc:
        print("ERROR:", exc)
        sys.exit(1)
