"""Repeat local checks and validate saved real-engine Sprint 2 evidence."""

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/sprint-2/evidence"
RUNTIME = ROOT / "review-evidence/runtime-2026-11-18"
SCENARIOS = ("happy", "correction", "organic", "pending", "invalid-certificate",
             "invalid-input", "boundaries")


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def engine_results():
    cases = []
    for scenario in SCENARIOS:
        path = RUNTIME / f"{scenario}-engine.json"
        result = load(path)
        assertions = result.get("assertions", [])
        instances = [i for field in ("producerInstances", "platformInstances", "boundaryInstances")
                     for i in result.get(field, [])]
        if (result.get("scenario") != scenario or result.get("engineExecuted") is not True
                or result.get("allAssertionsPassed") is not True or not assertions or not instances
                or any(a.get("passed") is not True for a in assertions)
                or any(i.get("state") != "COMPLETED" or i.get("hasIncident") is not False for i in instances)):
            raise ValueError(f"Incomplete or failed actual-engine evidence: {path}")
        if not result.get("stateSnapshots") or not result.get("businessResults"):
            raise ValueError(f"Missing state/business-result evidence: {path}")
        if not (RUNTIME / f"{scenario}-worker.log").is_file():
            raise FileNotFoundError(f"Missing worker log for {scenario}")
        cases.append({"scenario": scenario, "path": path.relative_to(ROOT).as_posix(),
                      "runId": result["runId"], "assertionsPassed": len(assertions),
                      "completedInstances": len(instances), "hasIncident": False,
                      "formInteraction": result["formInteraction"], "passed": True})
    return cases


def manual_result():
    path = RUNTIME / "tasklist-user-run.json"
    result = load(path)
    instances = [result["f1Completed"], result["f2Completed"], *result["platformInstances"]]
    before, after = result["beforeStockUpdate"], result["product"]
    if (result.get("status") != "completed" or result.get("engineExecuted") is not True
            or len(instances) != 4 or any(i["state"] != "COMPLETED" or i["hasIncident"] for i in instances)
            or before["quantity"] != 10 or after["quantity"] != 6
            or before["version"] != 0 or after["version"] != 1 or not after["published"]
            or result["customerAvailability"]["version"] != after["version"]):
        raise ValueError("Manual Tasklist evidence does not match the completed stock-change walkthrough")
    return {"path": path.relative_to(ROOT).as_posix(), "runId": result["runId"],
            "completedInstances": len(instances), "stockBefore": 10, "stockAfter": 6,
            "formInteraction": result["formInteraction"], "passed": True}


def main():
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    commands = (
        ["tools/build_sprint2_executable.py", "--check"],
        ["models/istar/validate_models.py"],
        ["tools/review_sprint2_models.py"],
        ["-m", "unittest", "discover", "-s", "tests", "-v"],
    )
    checks, logs, test_count = [], [], None
    for command in commands:
        completed = subprocess.run([sys.executable, *command], cwd=ROOT, env=env,
                                   capture_output=True, text=True, encoding="utf-8", errors="replace")
        log = completed.stdout + completed.stderr
        label = "python " + " ".join(command)
        logs.append(f"$ {label}\n{log}\nExit code: {completed.returncode}\n")
        checks.append({"command": label, "exitCode": completed.returncode, "passed": completed.returncode == 0})
        match = re.search(r"Ran (\d+) tests?", log)
        if match:
            test_count = int(match.group(1))
        if completed.returncode:
            (EVIDENCE / "implementation-tests-2026-11-18.txt").write_text("\n".join(logs), encoding="utf-8")
            raise RuntimeError(f"Required check failed: {label}")
    cases = engine_results()
    manual = manual_result()
    topology = load(RUNTIME / "topology.json")
    hashes = {}
    paths = {ROOT / "Run-Sprint2.cmd"}
    for directory in ("src", "tests", "tools", "models/istar", "models/operational"):
        paths.update(p for p in (ROOT / directory).rglob("*")
                     if p.is_file() and "__pycache__" not in p.parts and p.suffix not in {".pyc", ".pyo"})
    for path in sorted(paths):
        hashes[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    report = {
        "checkedAt": datetime.now(timezone.utc).isoformat(), "pythonVersion": sys.version.split()[0],
        "checks": checks, "allLocalChecksPassed": all(c["passed"] for c in checks),
        "pythonTestsPassed": test_count, "engineExecuted": True, "engineVersion": topology["gatewayVersion"],
        "cloudExecutableUpdated": False,
        "scope": "This command reruns local checks and verifies previously captured real-engine JSON/log evidence; it does not rerun engine scenarios.",
        "runtimeCases": cases, "runtimeAssertionsPassed": sum(c["assertionsPassed"] for c in cases),
        "scenarioCompletedInstances": sum(c["completedInstances"] for c in cases),
        "manualTasklist": manual,
        "limits": ["Certification uses local demo fixtures", "Identity and confirmed orders are trusted demo inputs",
                   "Seasonal changes are invoked explicitly", "No video recording, remote upload, personal review or tutor approval asserted"],
        "sourceHashes": hashes,
    }
    (EVIDENCE / "implementation-tests-2026-11-18.txt").write_text("\n".join(logs), encoding="utf-8")
    (EVIDENCE / "implementation-check-2026-11-18.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"localChecksPassed": True, "pythonTestsPassed": test_count,
                      "engineAssertionsPassed": report["runtimeAssertionsPassed"],
                      "scenarioInstancesCompleted": report["scenarioCompletedInstances"],
                      "manualTasklistPassed": manual["passed"]}))


if __name__ == "__main__":
    main()
