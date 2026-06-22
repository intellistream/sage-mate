---
kind: design
name: Adopt LLM-first with static fallback for onboarding and seed content
source: session
category: adr
---

# Adopt LLM-first with static fallback for onboarding and seed content

_Source: coding plans from commit period 7489233 → 3a5b0b9 — records intent at planning time; the implementation may lag or differ._

**Status:** accepted

## Context
The onboarding random button and seed chips previously relied exclusively on static pools (`ONBOARDING_RESEARCH_EXAMPLES` and `SEED_CHIP_POOL`), limiting contextual relevance. The existing `/lucky-question` endpoint already demonstrated a viable LLM-generation pattern with fallback, creating an opportunity to unify and enhance these UI elements.

## Decision drivers
- Contextual relevance of generated questions
- Perceived performance (instant initial render)
- Resilience against LLM latency or failure

## Considered options
- **LLM-first with static fallback and progressive loading** — pros: Provides highly contextual questions via LLM while ensuring instant UI responsiveness through static anchors; gracefully degrades to static content if the API fails or times out.; cons: Increases frontend complexity by managing two rendering states (static vs. LLM-enhanced) and handling async replacement logic.
- **Pure static pools** _(rejected)_ — pros: Zero latency, no dependency on external services, simple implementation.; cons: Lacks contextual awareness (e.g., specific onboarding steps like '问题定义' or '重要性'), resulting in a generic user experience.
- **Blocking LLM-only generation** _(rejected)_ — pros: Maximum contextual relevance without static anchors.; cons: Introduces noticeable latency before any content is visible; risks empty states if the LLM service is slow or unavailable.

## Decision
Extend the `/lucky-question` API to accept an `onboarding_step` parameter for context-aware prompting. Wire the onboarding random button to use this endpoint with a static fallback. For seed chips, implement a progressive loading strategy: render static pools immediately, then asynchronously fetch and replace a subset of chips with LLM-generated alternatives, keeping at least one static anchor.

## Consequences
Users receive more relevant, step-specific questions during onboarding. Seed chips benefit from dynamic content without blocking the initial view. The system remains robust via static fallbacks, but the frontend must manage additional state for loading indicators and partial content updates.