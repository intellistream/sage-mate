---
kind: design
name: Enforce invitation code for lab member registration
source: session
category: adr
---

# Enforce invitation code for lab member registration

_Source: coding plans from commit period 6c49c35 → 4c9a1f2 — records intent at planning time; the implementation may lag or differ._

**Status:** accepted

## Context
The application needed to restrict access to internal onboarding knowledge base entries (previously public) to verified lab members only. The existing auth system supported profiles but lacked a mechanism to verify new 'lab_member' registrations, and the frontend identity selection modal was missing.

## Decision drivers
- Access control for sensitive internal documentation
- Prevention of unauthorized lab member account creation
- Explicit user identity selection on every session start

## Considered options
- **Invitation code validation** — pros: Simple shared-secret verification; no external identity provider required; easy to rotate via config/env; cons: Code can be shared among unauthorized users; manual distribution required
- **Open registration for lab members** _(rejected)_ — pros: Zero friction for new users; cons: Anyone could claim 'lab_member' status and access restricted onboarding materials
- **Admin-approved registration** _(rejected)_ — pros: Highest security; explicit vetting of each user; cons: High operational overhead; requires admin UI and workflow not currently present

## Decision
Implement an invitation code gate for 'lab_member' registration. The backend validates the code against `settings.lab_member_invitation_code` during `register_user()`, rejecting invalid codes with HTTP 403. The frontend exposes the code input conditionally and forces an identity choice via a mandatory `identity-modal` on boot.

## Consequences
Lab members must possess a valid code to register, securing the `audience: 'lab_member'` knowledge base entries. Guests retain access but are explicitly warned that their chat history is ephemeral. The `identity-modal` removes the previous `localStorage` bypass, ensuring users consciously select their role (Member, Login, Guest) at the start of every unauthenticated session.