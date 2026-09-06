# Retrieval engineering limitation

## Status
Retrieval optimization is intentionally frozen.

## Decision
The targeted reranking experiment was invalid because its baseline reconstruction failed. The benchmark did not reproduce the known-good production retrieval baseline, so no further retrieval experimentation is allowed in this phase.

## Explicit constraints
- Do not modify `backend/app/services/evidence_retrieval.py`.
- Do not modify embedding providers or embedding logic.
- Do not modify similarity thresholds.
- Do not modify chunk content, query wording, or evidence preparation.
- Do not modify production ranking logic.
- Do not continue offline retrieval or reranking experiments at this stage.

## Why this is the correct stop condition
The project requirement is to preserve the current production retrieval path unchanged while the evaluation method is invalid. Since the baseline could not be reproduced, the correct engineering response is to freeze the work and move to the next FinSecAI capability in the upgrade sequence rather than iterate on retrieval behavior.

## Next capability
The next capability in the upgrade sequence is the background worker and report pipeline hardening work: move PDF/report generation and batch scoring into asynchronous background execution without touching the retrieval layer.
