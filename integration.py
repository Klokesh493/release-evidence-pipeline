"""Verify that sibling projects approve a healthy release and hold an incident."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def verify(workspace):
    with tempfile.TemporaryDirectory() as scratch:
        for scenario, expected_code, expected in (("healthy", 0, "approve"), ("incident", 1, "hold")):
            directory = Path(scratch, scenario)
            result = subprocess.run(
                [sys.executable, "-B", str(ROOT / "demo.py"), workspace, "--scenario", scenario,
                 "--evidence-dir", str(directory)],
                capture_output=True, text=True, check=False,
            )
            if result.returncode != expected_code:
                raise SystemExit(result.stderr or f"{scenario} returned {result.returncode}")
            evidence = json.loads(result.stdout)
            if evidence["decision"] != expected:
                raise SystemExit(f"{scenario} produced {evidence['decision']}, expected {expected}")
            if scenario == "incident" and {row["check"] for row in evidence["failures"]} != {"sre", "oncall"}:
                raise SystemExit("incident did not hold for the SRE and on-call checks")
            print(f"{scenario}: {evidence['decision']}")


if __name__ == "__main__":
    verify(sys.argv[1])
