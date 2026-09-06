# FinSecAI Project Timeline

## Executive summary
This document consolidates the project’s implementation history, milestones, and current status into a single production-facing timeline.

## Timeline

### Phase 1 — Foundation and architecture (early project work)
- Established the fraud and incident-response domain model.
- Defined a multi-component architecture spanning backend services, database access, and analytics.
- Created initial API and dashboard prototypes.

### Phase 2 — Streamlit prototype era
- Built multiple Streamlit-based dashboards for incident monitoring, deep-dive analysis, and metrics.
- Introduced early evaluation and governance concepts.
- Used these prototypes to validate the analyst workflow and demonstrate core fraud signals.

### Phase 3 — API and backend consolidation
- Reworked the project around a FastAPI backend for incidents, analytics, auth, reports, and copilot flows.
- Added a structured database layer with incident, report, and auth-related entities.
- Introduced environment-driven configuration and container-based deployment.

### Phase 4 — Frontend and productization
- Added a Next.js frontend to provide a more polished operational experience.
- Unified the product experience around a single app instead of competing prototypes.
- Added dashboard views for incidents, analytics, and copilot interaction.

### Phase 5 — Demo and handoff readiness
- Added deterministic analytics helpers for reproducible metrics.
- Introduced regression tests for the dashboard analytics layer.
- Prepared the project for local development and Docker-based deployment.

## Current production status
- Backend: FastAPI-based service layer with incident and analytics routes.
- Frontend: Next.js application for the analyst experience.
- Data layer: PostgreSQL + pgvector-ready structure with Redis support for background jobs.
- Testing: Core regression tests are present and maintained under the consolidated tests folder.
- Notes: Some parts remain demo-quality and are documented as such for future production hardening.

## Engineering limitation — retrieval experimentation is frozen
- Retrieval optimization work is explicitly suspended. The targeted reranking diagnostics failed to reconstruct a valid production baseline, so the benchmark was deemed invalid and no further retrieval experimentation is permitted at this stage.
- The production retrieval path remains unchanged: no edits to `evidence_retrieval.py`, embeddings, thresholds, chunk content, queries, or production ranking logic.
- This is treated as an engineering limitation, not a tuning issue. The current system is not allowed to proceed with additional evidence-ranking or reranking experiments until a valid, reproducible baseline exists and a controlled evaluation plan is approved.
- Current effect: all retrieval and evidence-ranking optimization work is parked, and the team is moving to the next capability in the upgrade sequence rather than continuing to iterate on retrieval behavior.

## Recommended next milestones
1. Replace placeholder RAG behavior with real embeddings and pgvector retrieval once a valid evaluation baseline is established.
2. Move PDF/report generation and batch scoring to background workers.
3. Add stronger end-to-end tests around auth, incidents, and analytics routes.
4. Harden deployment configuration for production environments.

## Active next capability
- The current workstream advances to the background worker and report pipeline capability: moving PDF/report generation and batch scoring out of synchronous execution and into Redis-backed background processing, while leaving retrieval untouched.
