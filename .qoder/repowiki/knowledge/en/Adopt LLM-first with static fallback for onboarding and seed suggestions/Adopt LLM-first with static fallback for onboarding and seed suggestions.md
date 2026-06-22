---
kind: design
name: Adopt LLM-first with static fallback for onboarding and seed suggestions
source: session
category: adr
---

# Adopt LLM-first with static fallback for onboarding and seed suggestions

_Source: coding plans from commit period 7489233 → 4adea3c — records intent at planning time; the implementation may lag or differ._

**Status:** accepted

## Context
The onboarding random button and seed chips previously relied exclusively on static pools (`ONBOARDING_RESEARCH_EXAMPLES` and `SEED_CHIP_POOL`), limiting contextual relevance. The existing `/lucky-question` endpoint already demonstrated an LLM-powered approach with fallback, creating an inconsistency in user experience and suggestion quality across the application.

## Decision drivers
- Contextual relevance of generated questions
- Perceived performance (instant initial render)
- Resilience against LLM latency or failure

## Considered options
- **Pure static pools** _(rejected)_ — pros: Zero latency, no dependency on external services, simple implementation; cons: Generic content, lacks personalization to user profile or onboarding step, poor engagement potential
- **Pure LLM generation (blocking)** _(rejected)_ — pros: Maximum contextual relevance, dynamic content; cons: High latency blocks UI rendering, poor user experience if API fails or times out
- **LLM-first with progressive static fallback** — pros: Instant UI feedback via static content, enhanced relevance via async LLM updates, graceful degradation on failure; cons: Increased frontend complexity (state management for swapping chips), higher backend load

## Decision
Implement a hybrid 'LLM-first' strategy where static pools provide immediate initial rendering, followed by asynchronous LLM calls to enhance or replace suggestions. For the onboarding button, this means calling `/lucky-question` with an `onboarding_step` parameter and falling back to static examples on failure. For seed chips, static items render instantly, then 1-2 are replaced by LLM-generated alternatives if available within 3 seconds.

## Consequences
Users experience instant interface responsiveness while benefiting from personalized content when the LLM is available. The system requires maintaining both static pools and LLM prompt logic. Frontend code must handle async state transitions and partial updates to the UI (swapping chips). Backend must support context-aware prompting via the new `onboarding_step` parameter in `llm_client.py`.