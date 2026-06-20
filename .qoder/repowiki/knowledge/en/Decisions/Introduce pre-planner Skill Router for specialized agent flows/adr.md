# Introduce pre-planner Skill Router for specialized agent flows

_Source: coding plans from commit period 3fe81af → ed17f66 — records intent at planning time; the implementation may lag or differ._

**Status:** accepted

## Context
The existing deterministic planner and plugin injection pipeline was insufficient for complex, multi-turn academic mentoring scenarios (e.g., research direction, paper digestion) that require dynamic tool usage and persistent context. A mechanism was needed to intercept specific user intents and delegate them to a specialized LLM agent loop before falling back to the standard flow.

## Decision drivers
- Support for multi-turn tool-calling agents
- Separation of specialized mentoring logic from general planning
- Reusability of existing service methods via a tool registry

## Considered options
- **Pre-planner Skill Router with dedicated Agent Loop** — pros: Allows full control over system prompts and tool sets for specific domains; isolates complex agent logic from the main planner; enables multi-turn reasoning via `chat_with_tools_sync`.; cons: Adds a new execution path and configuration layer (skill manifests); requires maintaining trigger patterns.
- **Extend existing deterministic planner with conditional plugin steps** _(rejected)_ — pros: No new architectural components; keeps all logic in one pipeline.; cons: The existing planner is deterministic and lacks native support for multi-turn LLM tool-calling loops; would require significant refactoring to support dynamic agent behavior.

## Decision
Implement a `SkillRouter` that matches user questions against `trigger_patterns` in skill manifests. If a match is found, a `SkillRunner` executes a multi-turn agent loop using `llm_client.chat_with_tools_sync` and a `SkillToolRegistry`. If no match is found, the request falls through to the existing deterministic planner.

## Consequences
Specialized queries (e.g., research mentoring) are handled by dedicated agents with custom tools and prompts, improving response quality for those domains. The system now supports two distinct execution paths: the new skill-based agent loop and the legacy deterministic planner. New skills can be added via JSON manifests without code changes to the core service.