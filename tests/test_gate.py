import json
import tempfile
import unittest
from pathlib import Path

from gate import check, seal, sha256

COMMIT = "a" * 40


class GateTest(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.bundle = Path(directory.name)
        self.write("sre.json", {"decision": "healthy"})
        self.write("aws.json", {"decision": "ready"})
        (self.bundle / "model-artifact").mkdir()
        self.artifact = self.bundle / "model-artifact/model.json"
        self.artifact.write_text("{}")
        self.write("model.json", {"decision": "ready", "model_sha256": sha256(self.artifact.read_bytes())})
        self.write("oncall.json", {"decision": "observe", "missing_or_uncertain": [],
                                  "human_action_required": False})
        self.seal()

    def write(self, name, value):
        (self.bundle / name).write_text(json.dumps(value))

    def seal(self):
        self.write("manifest.json", seal(self.bundle, COMMIT))

    def test_valid_bundle_approves(self):
        result = check(self.bundle, COMMIT)
        self.assertEqual(result["decision"], "approve")
        self.assertEqual(len(result["verified"]), 4)

    def test_artifact_change_holds(self):
        self.write("aws.json", {"decision": "ready", "edited": True})
        self.assertEqual(check(self.bundle, COMMIT)["failures"], [{"check": "aws", "reason": "digest mismatch"}])

    def test_healthy_commit_mismatch_holds(self):
        self.assertEqual(check(self.bundle, "c" * 40)["decision"], "hold")

    def test_incident_holds_even_with_valid_hash(self):
        self.write("sre.json", {"decision": "page"})
        self.seal()
        self.assertEqual(check(self.bundle, COMMIT)["decision"], "hold")

    def test_missing_evidence_holds(self):
        (self.bundle / "oncall.json").unlink()
        self.assertEqual(check(self.bundle, COMMIT)["decision"], "hold")

    def test_model_binary_change_holds(self):
        self.artifact.write_text('{"different": true}')
        self.assertIn({"check": "model", "reason": "model artifact digest mismatch"},
                      check(self.bundle, COMMIT)["failures"])
