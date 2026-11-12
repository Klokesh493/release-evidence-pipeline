"""Run the four sibling flagship projects and evaluate their release bundle."""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from gate import check, seal

DEMO_COMMIT = "0" * 39 + "1"


def collect(repo, *args):
    output = subprocess.check_output([sys.executable, "-B", *args], cwd=repo)
    return json.loads(output)


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def run(workspace, bundle, incident, commit):
    sre = collect(workspace / "sre-error-budget-control-plane", "budget.py",
                  "examples/incident.json" if incident else "examples/healthy.json")
    aws = collect(workspace / "aws-event-recovery-platform", "drill.py", "examples/mixed-batch.json")
    model = collect(workspace / "azure-ml-endpoint-release-lab", "release.py",
                    "--output", str(bundle / "model-artifact"))
    snapshot = {
        "service": "checkout", "now_minute": sre["as_of_minute"],
        "observations": [
            {"kind": kind, "id": reference, "status": status, "service": "checkout",
             "observed_minute": sre["as_of_minute"]}
            for kind, reference, status in (
                ("slo", "slo:replay", sre["decision"]),
                ("queue", "cloudwatch:synthetic", "alarm" if incident else "ok"),
                ("change", "deploy:synthetic", "recent" if incident else "stable"),
            )
        ],
    }
    write_json(bundle / "oncall-input.json", snapshot)
    oncall = collect(workspace / "cloud-oncall-evidence-agent", "agent.py", str(bundle / "oncall-input.json"))
    for name, report in (("sre", sre), ("aws", aws), ("model", model), ("oncall", oncall)):
        write_json(bundle / f"{name}.json", report)
    write_json(bundle / "manifest.json", seal(bundle, commit))
    result = check(bundle, commit)
    result["observed_decisions"] = {
        "sre": sre["decision"], "aws": aws["decision"],
        "model": model["decision"], "oncall": oncall["decision"],
    }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--scenario", choices=["healthy", "incident"], default="healthy")
    parser.add_argument("--commit", default=DEMO_COMMIT)
    parser.add_argument("--evidence-dir", type=Path, help="retain evidence in a new directory")
    args = parser.parse_args()
    workspace = args.workspace.resolve()
    incident = args.scenario == "incident"
    if args.evidence_dir:
        bundle = args.evidence_dir.resolve()
        bundle.mkdir(parents=True, exist_ok=False)
        result = run(workspace, bundle, incident, args.commit)
    else:
        with tempfile.TemporaryDirectory() as directory:
            result = run(workspace, Path(directory), incident, args.commit)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["decision"] == "approve" else 1)


if __name__ == "__main__":
    main()
