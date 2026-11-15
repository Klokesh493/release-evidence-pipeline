# Skills and verification

## What this repository demonstrates

Candidate-bound report verification, SHA-256 artifact checks, and a fail-closed release decision.

## Reproduce the result

Run `make verify verify-integration` with the sibling repositories cloned beside this one. Healthy approves and incident holds.

Run `make verify` locally. Ruff and Bandit medium/high checks passed for the checked Python code.

## Scope

The pipeline runs locally. The workflow YAML is a template and its manifest assumes a trusted source.

[demo.py](../demo.py) · [gate.py](../gate.py) · [integration.py](../integration.py) · [Architecture](../docs/ARCHITECTURE.md) · [Case study](../docs/CASE_STUDY.md) · [Runbook](../docs/RUNBOOK.md) · [CI template](../docs/github-actions/ci.yml)
