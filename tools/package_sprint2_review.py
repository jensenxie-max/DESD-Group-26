"""Build or verify four disjoint, source-checked Sprint 2 GitHub upload packs.

The dated November 17 preparation packs are historical and are never modified.
Run without arguments only after the current validation evidence is complete.
"""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DATE = "2026-11-18"
OUT = ROOT / f"outputs/sprint2-github-{DATE}"
MEMBERS = ("Jiaqi", "Yunze", "Jilong", "Haodong")
CHECK_PATH = f"docs/sprint-2/evidence/implementation-check-{DATE}.json"
RUNTIME = f"review-evidence/runtime-{DATE}"
GUIDE_PATH = f"docs/sprint-2/individual-files-{DATE}.txt"
EXCLUDED_PARTS = {".git", ".agents", ".codex", ".aws", "__pycache__", "work", "outputs", "node_modules"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".db", ".sqlite", ".sqlite3", ".zip", ".7z", ".tar", ".gz", ".pem", ".key"}
CURRENT_DOCUMENTS = {
    "README.md", "docs/sprint-2/README.md", "docs/sprint-2/camunda-review.md",
    "docs/sprint-2/i-star-review-checklist.md", "docs/sprint-2/contribution-record.md",
    "docs/sprint-2/traceability.md", "docs/sprint-2/traceability.json",
    "docs/sprint-2/f1-contract.json", "docs/sprint-2/f2-contract.json",
    "docs/sprint-2/review-requirements-2026-11-17.txt",
    "docs/sprint-2/submission-links.txt", "docs/sprint-2/review-walkthrough.txt",
    "docs/sprint-2/evidence/README.md", GUIDE_PATH, CHECK_PATH,
    f"docs/sprint-2/evidence/implementation-tests-{DATE}.txt",
    f"docs/sprint-2/evidence/model-review-{DATE}.json",
    f"docs/sprint-2/model-review-{DATE}.md",
    f"docs/sprint-2/runtime-validation-{DATE}.md",
}
# Baselines and reference files needed to rebuild/validate the current models.
BASELINES = {
    "docs/Use-Case-1-Requirements.xlsm", "docs/sprint-1/README.md",
    "docs/sprint-1/submission-checklist.md",
    "docs/sprint-1/submission-links.txt",
    "docs/sprint-1/Group-26-Sprint-1-Contribution-Matrix.docx",
    "review-evidence/responsibilities-2026-11-17/F1-saved.bpmn",
    "review-evidence/responsibilities-2026-11-17/F2-saved.bpmn",
    "review-evidence/layout-2026-11-11/Strategic-saved.bpmn",
    "review-evidence/forms-2026-11-11/F1-saved.bpmn",
    "review-evidence/forms-2026-11-11/F2-saved.bpmn",
    "review-evidence/forms-2026-11-11/proposed/F1-Product-Details.form",
    "review-evidence/forms-2026-11-11/proposed/F1-Correct-Product-Details.form",
    "review-evidence/forms-2026-11-11/proposed/F2-Stock-and-Sale-Dates.form",
}
TOOLS = {"Run-Sprint2.cmd", "tools/run_sprint2_manual.py",
         "tools/build_sprint2_executable.py", "tools/package_sprint2_review.py",
         "tools/verify_sprint2_delivery.py"}
REQUIRED_RUNTIME_CASES = {"happy", "correction", "organic", "pending", "boundaries",
                          "invalid-input", "invalid-certificate"}
F1_EVIDENCE_PREFIXES = ("correction-", "organic-", "pending-", "invalid-certificate-")
F2_EVIDENCE_PREFIXES = ("boundaries-", "invalid-input-", "f2-")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def safe_source(relative):
    path = PurePosixPath(relative)
    if path.is_absolute() or ".." in path.parts or any(p in EXCLUDED_PARTS for p in path.parts):
        raise ValueError(f"Excluded or invalid repository path: {relative}")
    if path.suffix.lower() in EXCLUDED_SUFFIXES or path.name.startswith(".env"):
        raise ValueError(f"Excluded source type: {relative}")
    source = (ROOT / relative).resolve()
    if not source.is_relative_to(ROOT.resolve()):
        raise ValueError(f"Source resolves outside repository: {relative}")
    return source


def files(folder):
    return {p.relative_to(ROOT).as_posix() for p in (ROOT / folder).rglob("*")
            if p.is_file() and not any(part in EXCLUDED_PARTS for part in p.relative_to(ROOT).parts)
            and p.suffix.lower() not in EXCLUDED_SUFFIXES and not p.name.startswith(".env")}


def assignments():
    assigned = {name: set() for name in MEMBERS}
    assigned["Jiaqi"] = (files("models/istar") | files("models/strategic") |
                         files("review-evidence/requirements-2026-11-18")) | {
        "README.md", "docs/Use-Case-1-Requirements.xlsm", "docs/sprint-1/README.md",
        "docs/sprint-1/submission-checklist.md",
        "docs/sprint-1/submission-links.txt",
        "docs/sprint-1/Group-26-Sprint-1-Contribution-Matrix.docx",
        "docs/sprint-2/traceability.md", "docs/sprint-2/traceability.json",
        "docs/sprint-2/f1-contract.json", "docs/sprint-2/i-star-review-checklist.md",
        "src/sprint2_demo/f1.py", "models/operational/F1-Operational.bpmn",
        "models/operational/F1-Operational.svg",
        "review-evidence/responsibilities-2026-11-17/F1-saved.bpmn",
        "review-evidence/forms-2026-11-11/F1-saved.bpmn",
        "review-evidence/layout-2026-11-11/Strategic-saved.bpmn",
        f"docs/sprint-2/evidence/model-review-{DATE}.json",
        f"docs/sprint-2/model-review-{DATE}.md",
    }
    assigned["Jilong"] = {
        "models/operational/forms/F1-Product-Details.form",
        "models/operational/forms/F1-Correct-Product-Details.form", "tests/test_f1.py",
        "review-evidence/forms-2026-11-11/proposed/F1-Product-Details.form",
        "review-evidence/forms-2026-11-11/proposed/F1-Correct-Product-Details.form",
    }
    assigned["Haodong"] = {
        "models/operational/forms/F2-Stock-and-Sale-Dates.form",
        "review-evidence/forms-2026-11-11/proposed/F2-Stock-and-Sale-Dates.form",
        "tests/test_f2.py", "tests/test_common.py", "tests/test_sprint2_runtime.py",
    }
    runtime_files = files(RUNTIME)
    for relative in runtime_files:
        name = PurePosixPath(relative).name
        if name.startswith(F1_EVIDENCE_PREFIXES):
            assigned["Jilong"].add(relative)
        elif name.startswith(F2_EVIDENCE_PREFIXES):
            assigned["Haodong"].add(relative)
    required = (files("src") | files("tests") | files("models/operational") |
                files("models/istar") | files("models/strategic") | runtime_files |
                CURRENT_DOCUMENTS | BASELINES | TOOLS)
    # A current model review may include its own reproducible review tool/source.
    required |= files("review-evidence/requirements-2026-11-18")
    for optional in ("tools/review_sprint2_models.py", "tools/validate_sprint2_models.py"):
        if (ROOT / optional).is_file():
            assigned["Jiaqi"].add(optional)
            required.add(optional)
    assigned["Yunze"] = required - set.union(*assigned.values())
    counts = Counter(p for paths in assigned.values() for p in paths)
    if any(value != 1 for value in counts.values()):
        raise ValueError("A repository path was assigned more than once")
    if set(counts) != required:
        raise ValueError("Current required files are missing from member assignments")
    for relative in counts:
        safe_source(relative)
    return assigned, required


def require_ready(assigned):
    missing = sorted(p for paths in assigned.values() for p in paths if not safe_source(p).is_file())
    if missing:
        raise FileNotFoundError("Current inputs are not ready:\n" + "\n".join(missing))
    verification = json.loads(safe_source(CHECK_PATH).read_text(encoding="utf-8"))
    if not verification.get("allLocalChecksPassed") or not verification.get("engineExecuted"):
        raise ValueError("Current verification must record successful local checks and real engine execution")
    for scenario in sorted(REQUIRED_RUNTIME_CASES):
        for suffix in ("engine.json", "worker.log"):
            relative = f"{RUNTIME}/{scenario}-{suffix}"
            if not safe_source(relative).is_file():
                raise FileNotFoundError(f"Current runtime scenario evidence missing: {relative}")
        outcome = json.loads(safe_source(f"{RUNTIME}/{scenario}-engine.json").read_text(encoding="utf-8"))
        assertions = outcome.get("assertions", [])
        instances = [item for key in ("producerInstances", "platformInstances", "boundaryInstances")
                     for item in outcome.get(key, [])]
        if (outcome.get("engineExecuted") is not True or outcome.get("allAssertionsPassed") is not True
                or not assertions or not all(item.get("passed") is True for item in assertions)
                or not instances or not all(item.get("state") == "COMPLETED" and
                                             not item.get("hasIncident") for item in instances)):
            raise ValueError(f"Runtime scenario did not pass: {scenario}")
    return verification


def member_guide(member, paths):
    return (f"{member} — 本次上传文件（18 November 2026）\n\n"
            "1. 解压 ZIP，打开 repo-root 文件夹。\n"
            "2. 用自己的 GitHub 账号打开 DESD-Group-26 仓库根目录。\n"
            "3. Add file → Upload files，拖入 repo-root 里面的全部文件和文件夹。\n"
            "4. 核对路径后 Commit changes；已有文件按原路径更新。\n\n"
            "不要上传 ZIP、repo-root 包装层、READ-FIRST.txt 或 manifest.json。\n"
            "根目录启动文件 Run-Sprint2.cmd 是有效项目文件；仅 Yunze 的包包含它。\n"
            "四个包的仓库路径互不重复，四人全部上传后才是完整项目。\n"
            "已验证真实引擎正常路径和本轮异常/边界场景；运行范围见 runtime-validation-2026-11-18.md。\n"
            "这些是文件上传安排；个人贡献请按实际复核、修改与运行记录说明。\n"
            "旧 sprint2-review-2026-11-17 是历史准备包，请使用本次新包。\n"
            "本包不含最终视频，也不是 Blackboard 最终提交 ZIP。\n\n"
            "本人的完整上传路径：\n" + "\n".join(sorted(paths)) + "\n")


def clear_member_folder(folder):
    # Never clear the output root or any historical pack. Verify the final path.
    if folder.resolve().parent != OUT.resolve() or folder.name not in {f"{m}-files" for m in MEMBERS}:
        raise ValueError(f"Unsafe member output path: {folder}")
    if folder.exists():
        shutil.rmtree(folder)


def build(assigned, required, verification):
    if not OUT.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError("Output resolves outside the project workspace")
    OUT.mkdir(parents=True, exist_ok=True)
    report = {"date": DATE, "purpose": "Individual GitHub uploads; not a Blackboard submission",
              "runtimeExecuted": verification["engineExecuted"], "verification": CHECK_PATH,
              "historicalPack": "outputs/sprint2-review-2026-11-17 (unchanged)",
              "requiredFiles": sorted(required), "members": []}
    for member, paths in assigned.items():
        folder = OUT / f"{member}-files"
        clear_member_folder(folder)
        upload = folder / "repo-root"
        upload.mkdir(parents=True)
        entries = []
        for relative in sorted(paths):
            data = safe_source(relative).read_bytes()
            target = upload / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            entries.append({"path": relative, "sha256": sha256(data), "bytes": len(data)})
        (folder / "READ-FIRST.txt").write_text(member_guide(member, paths), encoding="utf-8-sig")
        (folder / "manifest.json").write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        archive = OUT / f"{member}-Sprint2-Files.zip"
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
            for path in (folder / "READ-FIRST.txt", folder / "manifest.json"):
                bundle.write(path, path.name)
            for relative in sorted(paths):
                bundle.write(upload / relative, "repo-root/" + relative)
        report["members"].append({"member": member, "files": len(paths), "archive": archive.name,
                                  "paths": sorted(paths), "archiveSha256": sha256(archive.read_bytes())})
    (OUT / "START-HERE.txt").write_text(
        "Sprint 2 — 四个人分别上传（18 November 2026）\n\n"
        "Jiaqi：SD/SR、战略参照、F1 图与规则、需求对应和模型复核。\n"
        "Yunze：F2 图、运行代码、启动文件、共用说明、正常运行与手动表单证据。\n"
        "Jilong：F1 两张表单、F1 测试、资料纠正及认证分支运行证据。\n"
        "Haodong：F2 表单、F2/公共/运行层测试、库存边界与无效输入运行证据。\n\n"
        "每人解压自己的 ZIP，按 READ-FIRST.txt 上传 repo-root 里面的内容。\n"
        "不要把 ZIP 或 repo-root 外层当作项目文件上传。四个包没有重复仓库路径。\n"
        "全部上传后，可从仓库根目录运行 Run-Sprint2.cmd。\n"
        "当前真实运行结果见 docs/sprint-2/runtime-validation-2026-11-18.md。\n"
        "11 月 17 日旧包保留为历史，请使用本目录的新包。\n"
        "本目录不含最终 MP4，也不是 Blackboard 最终提交 ZIP。\n", encoding="utf-8-sig")
    (OUT / "package-status.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def verify(assigned, required):
    report = json.loads((OUT / "package-status.json").read_text(encoding="utf-8"))
    if report.get("date") != DATE or report.get("runtimeExecuted") is not True or report.get("verification") != CHECK_PATH:
        raise ValueError("Package status does not identify the current verified delivery")
    if set(report["requiredFiles"]) != required:
        raise ValueError("Package required-file list is stale")
    combined = []
    for member, paths in assigned.items():
        folder = OUT / f"{member}-files"
        entries = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
        entry_paths = [entry["path"] for entry in entries]
        if set(entry_paths) != paths or len(entry_paths) != len(paths):
            raise ValueError(f"Stale or duplicate member manifest: {member}")
        copied_paths = {p.relative_to(folder / "repo-root").as_posix()
                        for p in (folder / "repo-root").rglob("*") if p.is_file()}
        if copied_paths != paths:
            raise ValueError(f"Unexpected or missing copied file: {member}")
        archive = OUT / f"{member}-Sprint2-Files.zip"
        member_report = next(x for x in report["members"] if x["member"] == member)
        if member_report["paths"] != sorted(paths) or member_report["files"] != len(paths):
            raise ValueError(f"Package status is stale: {member}")
        if member_report["archiveSha256"] != sha256(archive.read_bytes()):
            raise ValueError(f"Archive hash changed: {member}")
        with zipfile.ZipFile(archive) as bundle:
            expected = {"READ-FIRST.txt", "manifest.json"} | {"repo-root/" + p for p in paths}
            if set(bundle.namelist()) != expected or len(bundle.namelist()) != len(expected) or bundle.testzip():
                raise ValueError(f"Invalid archive file list: {member}")
            for entry in entries:
                relative = entry["path"]
                source = safe_source(relative).read_bytes()
                copy = (folder / "repo-root" / relative).read_bytes()
                zipped = bundle.read("repo-root/" + relative)
                if len(source) != entry["bytes"] or any(sha256(data) != entry["sha256"] for data in (source, copy, zipped)):
                    raise ValueError(f"Source/copy/archive hash mismatch: {relative}")
            for name in ("READ-FIRST.txt", "manifest.json"):
                if bundle.read(name) != (folder / name).read_bytes():
                    raise ValueError(f"Archive guide/manifest mismatch: {member}/{name}")
        combined.extend(entry_paths)
    if set(combined) != required or any(n != 1 for n in Counter(combined).values()):
        raise ValueError("Four-pack union is incomplete or overlapping")
    return {"output": str(OUT), "files": {m: len(p) for m, p in assigned.items()},
            "uniqueRepositoryPaths": len(required), "duplicatePaths": [],
            "requiredFilesIncluded": True, "sourceCopyZipHashesVerified": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--plan", action="store_true", help="Print assignments and missing inputs without writing packages")
    mode.add_argument("--check", action="store_true", help="Verify existing packages against current source files")
    args = parser.parse_args()
    assigned, required = assignments()
    if args.plan:
        print(json.dumps({"output": str(OUT), "members": {m: sorted(p) for m, p in assigned.items()},
                          "missing": sorted(p for p in required if not safe_source(p).is_file())},
                         ensure_ascii=False, indent=2))
        return
    verification = require_ready(assigned)
    if not args.check:
        build(assigned, required, verification)
    print(json.dumps(verify(assigned, required), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
