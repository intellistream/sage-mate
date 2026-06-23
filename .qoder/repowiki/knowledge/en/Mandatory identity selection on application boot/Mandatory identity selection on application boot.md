---
kind: design
name: Mandatory identity selection on application boot
source: session
category: adr
---

# Mandatory identity selection on application boot

_Source: coding plans from commit period 8dd53dd → 2dd47cf — records intent at planning time; the implementation may lag or differ._

**Status:** accepted

## Context
The application previously allowed users to bypass identity selection via a `localStorage` flag, leading to inconsistent access control states. With the introduction of sensitive lab-member-only content, it is critical that every session explicitly declares its access level (authenticated member vs. ephemeral guest) before interacting with the system.

## Decision drivers
- consistent enforcement of access control policies
- clear user expectation setting regarding data persistence
- prevention of accidental privilege escalation

## Considered options
- **Mandatory modal without close button** — pros: Forces an explicit choice every time; ensures the backend knows the user's intent; allows clear communication about guest limitations (no history).; cons: Slightly higher friction for returning guests who must click through again.
- **Optional identity prompt with localStorage remember-me** _(rejected)_ — pros: Better user experience for frequent guests.; cons: Users might get stuck in a 'guest' state unintentionally; harder to enforce strict audience filtering if the state is stale or bypassed.

## Decision
Implement a mandatory `identity-modal` that appears on boot if the user is not authenticated. It offers three paths: register as a lab member (with invitation code), login as an existing user, or continue as a guest. The modal has no close button, forcing a decision. The `localStorage` bypass key `VISITOR_IDENTITY_SELECTED_KEY` is removed to ensure this prompt always appears for unauthenticated users.

## Consequences
Unauthenticated users can no longer silently access the app without choosing a role. Guest users are explicitly informed that their chat history will not be saved. Authenticated lab members gain access to restricted knowledge base entries.