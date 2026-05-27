# Roadmap

This document marks the first organized release baseline for `sage-faculty-twin` under the
IntelliStream organization plan.

For the parallel implementation order of the `v2` workstreams, see
[`docs/agent-rollout-plan.md`](docs/agent-rollout-plan.md).

## V1 Baseline

`v1.0.0` defines the first usable faculty twin baseline: a personal academic digital twin that can
answer common student questions, guide office-hour preparation, and route actionable requests
through explicit workflows instead of a single opaque chat completion.

### V1 Scope

- Student-facing Chinese-first chat interface with a simple ChatGPT-like workflow view.
- SAGE/FlowNet-based agentic orchestration for answering, booking, escalation, and follow-up.
- Retrieval-aware answers grounded in imported homepage content, curated notes, course pages, and
  PDFs.
- NeuroMem-backed short-term memory and long-term student profile memory.
- Booking workflow with weekly availability management, admin approval, rejection reasons, and
  email notifications.
- Admin capabilities for knowledge updates, booking review, escalation review, memory profile
  inspection, and question analytics.
- Offline homepage/course material ingestion and local deployment scripts for app, site, and
  tunnel-based access.

### What V1 Is Meant To Prove

- A faculty twin should behave like an academic office workflow, not just a Q&A bot.
- SAGE workflows can coordinate model calls, retrieval, approvals, and follow-up actions in a
  transparent way.
- Memory, knowledge, and booking state can be persisted locally and audited by the owner.
- The product can already support real student interactions while keeping sensitive approval steps
  with the human owner.

## V2 Plan

`v2` is planned as the operations and deployment expansion release. The main goal is to move from a
working faculty twin to a reusable, organization-owned service that is easier to operate, improve,
and extend.

### V2 Focus Areas

- Upgrade the current admin area into a true operations console covering question distribution,
  knowledge gaps, student segmentation, satisfaction trends, human handoff queues, and follow-up
  tasks.
- Add stronger operational data models so analytics, feedback, escalations, and follow-up actions
  form one closed loop.
- Integrate real calendar providers instead of repo-only availability for confirmed meetings.
- Add stronger identity and governance controls such as student verification, audit trails, and
  clearer human-takeover boundaries.
- Improve deployment ergonomics for IntelliStream-owned rollout, environment setup, and branded
  reuse.
- Strengthen evaluation and reliability with better latency/error observability and release-facing
  quality checks.

### Candidate V2 Extensions

- Multichannel entry points such as LMS embedding, homepage widgets, or messaging connectors.
- Voice interaction and richer avatar presentation once the operations baseline is stable.
- Better knowledge publishing workflows that connect updated source content to indexed retrieval
  with less manual intervention.
- Reusable persona and organization templates for deploying the same product shape to multiple
  faculty members.

## Release Note

`v1.0.0` should be treated as the first public repository baseline: stable enough to publish, demo,
and use as the starting point for parallel agent work, while still leaving the operations console
and organization-scale rollout to `v2`.