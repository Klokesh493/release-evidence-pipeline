# Case study

## Problem

A passing build alone cannot tell you whether a service is already burning its error budget or a model artifact differs from the one evaluated. Release decisions need evidence tied to the candidate.

## Implementation

The gate expects healthy SRE, ready AWS recovery, ready model quality and observe from on-call, plus a SHA-256 match for every report and the model artifact. Missing, mismatched, or adverse evidence returns hold with a nonzero exit status. The integration runner produces the actual reports from all four projects in the same checkout group.

## Validation

Six unit tests passed. The cross-repository demo approved a healthy release and held the incident because SRE paged and on-call escalated. Tests also held altered report bytes, altered model bytes, and a wrong candidate SHA.

## Limits

SHA-256 checks detect changes relative to a trusted manifest. The manifest is unsigned and provides no proof of origin by itself. The demo uses a synthetic commit by default and performs no deployment. The workflow is a template.
