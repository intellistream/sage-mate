---
kind: design
name: Mandate explicit identity selection on application boot
source: session
category: adr
---

# Mandate explicit identity selection on application boot

_Source: coding plans from commit period f38f0eb → 3eb7563 — records intent at planning time; the implementation may lag or differ._

**Status:** accepted

## Context
The application previously allowed users to bypass identity selection via a `localStorage` flag (`VISITOR_IDENTITY_SELECTED_KEY`), leading to ambiguous session states. Additionally, the referenced `identity-modal` was missing from the HTML, preventing users from choosing between authenticated and guest modes.

## Decision drivers
- Clear separation of guest vs. authenticated user experiences
- Ensuring users acknowledge ephemeral nature of guest chats
- Fixing broken UI reference to enable intended workflow

## Considered options
- **Mandatory blocking identity modal** — pros: Forces explicit user intent; prevents accidental data loss confusion for guests; ensures correct profile loading.; cons: Adds an extra click step for returning users; interrupts immediate access to the chat interface.
- **Auto-resume previous session via localStorage** _(rejected)_ — pros: Fastest path to interaction for returning users.; cons: Users may forget they are in guest mode and expect history persistence; ambiguous state management.

## Decision
Introduce a mandatory `identity-modal` that appears on every boot if the user is not authenticated. This modal removes the close button and forces a choice between 'Lab Member' (register/login), 'Existing Account' (login), or 'Guest Mode'. The `localStorage` bypass key is removed to ensure this prompt always appears for unauthenticated sessions. Guest mode explicitly notifies users that chat history will not be saved.

## Consequences
Unauthenticated users can no longer silently enter the app; they must consciously choose guest mode or authenticate. This clarifies the expectation of ephemeral chats for guests and ensures lab members are directed to the correct authentication flow.