---
kind: design
name: Mandate identity selection on application boot
source: session
category: adr
---

# Mandate identity selection on application boot

_Source: coding plans from commit period c05d89b → 8894345 — records intent at planning time; the implementation may lag or differ._

**Status:** accepted

## Context
The frontend previously allowed users to bypass identity selection via local storage, leading to inconsistent state where guests might accidentally access features intended for authenticated users or vice versa. The identity modal was also missing from the HTML despite being referenced in JS.

## Decision drivers
- Explicit user intent for access level
- Consistent session initialization
- Clarification of guest mode limitations

## Considered options
- **Mandatory blocking modal on boot** — pros: Forces explicit choice between 'lab member', 'login', or 'guest'; ensures correct permissions are set before any interaction; clarifies that guest history is not saved.; cons: Adds friction for returning guests who must dismiss the modal every time.
- **Persist guest choice in localStorage** _(rejected)_ — pros: Better UX for frequent guests.; cons: Risk of stale state; users might forget they are in guest mode and expect history persistence.

## Decision
Introduce a non-dismissible `identity-modal` that appears on every boot if no valid session exists. It offers three paths: register as lab member (requiring invitation code), login with existing credentials, or continue as guest. The `localStorage` bypass key `VISITOR_IDENTITY_SELECTED_KEY` is removed to ensure this prompt always appears for unauthenticated users.

## Consequences
Users must actively choose their role on every visit if not logged in. Guest users are explicitly informed that their chat history will not be persisted, managing expectations regarding data retention.