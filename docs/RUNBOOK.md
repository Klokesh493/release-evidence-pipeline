# Operator runbook

## Reproduce

```sh
make verify
make verify-integration  # with the four sibling repos cloned beside this one
```

## Triage and recovery

For a digest or candidate mismatch, regenerate the bundle in the trusted job using the same commit. For an SRE page or on-call escalation, assign the incident and rerun evidence after recovery. Preserve the failed report for the release reviewer.

## Evidence boundaries

SHA-256 checks detect changes relative to a trusted manifest. The manifest is unsigned and provides no proof of origin by itself. The demo uses a synthetic commit by default and performs no deployment. The workflow is a template.
