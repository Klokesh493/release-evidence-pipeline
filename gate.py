"""Verify a release evidence bundle and return a fail-closed decision."""
import argparse
import hashlib
import hmac
import json
import re
from pathlib import Path

FILES = {
    "sre": "sre.json",
    "aws": "aws.json",
    "model": "model.json",
    "oncall": "oncall.json",
}
POLICY = {"sre": "healthy", "aws": "ready", "model": "ready", "oncall": "observe"}
GIT_SHA = re.compile("[a-f0-9]{40}")
DIGEST = re.compile("[a-f0-9]{64}")
MAX_FILE_BYTES = 262_144


def read_file(path):
    with path.open("rb") as handle:
        data = handle.read(MAX_FILE_BYTES + 1)
    if len(data) > MAX_FILE_BYTES:
        raise ValueError("evidence file too large")
    return data


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def seal(bundle, commit):
    if not GIT_SHA.fullmatch(commit):
        raise ValueError("invalid commit SHA")
    files = {kind: sha256(read_file(bundle / filename)) for kind, filename in FILES.items()}
    return {"version": 1, "commit": commit, "reports": files}


def check(bundle, commit):
    failures = []
    verified = {}
    try:
        manifest = json.loads(read_file(bundle / "manifest.json"))
        if not GIT_SHA.fullmatch(commit) or type(manifest["version"]) is not int or manifest["version"] != 1:
            raise ValueError("unsupported manifest")
        if manifest["commit"] != commit:
            raise ValueError("manifest commit mismatch")
        if set(manifest["reports"]) != set(FILES):
            raise ValueError("manifest must contain all four evidence reports")
    except (OSError, ValueError, KeyError, TypeError) as error:
        return {"decision": "hold", "commit": commit, "verified": {},
                "failures": [{"check": "manifest", "reason": str(error)}]}

    for kind, filename in FILES.items():
        try:
            payload = read_file(bundle / filename)
            expected_digest = manifest["reports"][kind]
            if not DIGEST.fullmatch(expected_digest) or not hmac.compare_digest(sha256(payload), expected_digest):
                raise ValueError("digest mismatch")
            report = json.loads(payload)
            actual = report["decision"]
            if actual != POLICY[kind]:
                raise ValueError("report did not approve this check")
            if kind == "model":
                artifact_digest = sha256(read_file(bundle / "model-artifact" / "model.json"))
                if not DIGEST.fullmatch(report["model_sha256"]) or not hmac.compare_digest(
                    artifact_digest, report["model_sha256"]
                ):
                    raise ValueError("model artifact digest mismatch")
            if kind == "oncall" and (report["missing_or_uncertain"] != [] or
                                     report["human_action_required"] is not False):
                raise ValueError("on-call evidence requires review")
            verified[kind] = expected_digest
        except (OSError, ValueError, KeyError, TypeError) as error:
            failures.append({"check": kind, "reason": str(error)})
    return {"decision": "hold" if failures else "approve",
            "commit": commit, "verified": verified, "failures": failures}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--commit", required=True)
    args = parser.parse_args()
    result = check(args.bundle, args.commit)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["decision"] == "approve" else 1)


if __name__ == "__main__":
    main()
