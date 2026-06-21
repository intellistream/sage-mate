---
kind: design
name: Mandate explicit identity selection on application boot
source: session
category: adr
---

# Mandate explicit identity selection on application boot

_Source: coding plans from commit period c6c2ee0 → c05d89b — records intent at planning time; the implementation may lag or differ._

**Status:** accepted

## Context
The frontend previously allowed users to bypass identity selection via local storage, leading to inconsistent state where guests might inadvertently access features intended for authenticated users or vice versa. The identity modal was referenced in JS but missing from HTML.

## Decision drivers
- Clear separation of guest vs. authenticated user capabilities
- Ensuring users acknowledge ephemeral nature of guest chats
- Fixing broken UI reference to identity-modal

## Considered options
- **Mandatory blocking modal on boot** — pros: Forces explicit choice every session if not authenticated; clearly communicates trade-offs (e.g., no history for guests); prevents accidental state leakage.; cons: Adds an extra click/step for returning guests; cannot be dismissed without choosing a path.
- **Optional identity prompt with localStorage persistence** _(rejected)_ — pros: Less intrusive for returning users.; cons: Users may forget their status; harder to enforce security boundaries for lab-member-only content if state is stale.

## Decision
Introduce a non-dismissible `identity-modal` that appears on every boot for unauthenticated users. It offers three paths: Lab Member Registration (with invite code), Existing User Login, or Guest Mode (with explicit notice about ephemeral history). LocalStorage bypasses are removed.

## Consequences
All users must consciously select their role upon entry. Guest users are explicitly informed that their chat history will not be saved, managing expectations. Authenticated flows are strictly separated from guest flows.