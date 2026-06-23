---
kind: design
name: Enforce invitation code for lab member registration
source: session
category: adr
---

# Enforce invitation code for lab member registration

_Source: coding plans from commit period 3eb7563 → c6c2ee0 — records intent at planning time; the implementation may lag or differ._

**Status:** accepted

## Context
The application needed to restrict access to internal onboarding knowledge base entries (previously public) to verified lab members only, preventing unauthorized access to sensitive research protocols and advisor meeting standards.

## Decision drivers
- Access control for sensitive internal documentation
- Simple verification mechanism without complex identity providers
- Differentiation between public visitors and internal lab members

## Considered options
- **Invitation code validation during registration** — pros: Low implementation complexity; no external dependencies; allows immediate self-service registration for those with the code; keeps the existing auth system intact.; cons: Code sharing is possible (not cryptographically secure); requires manual distribution of the code by admins.
- **Admin-only account creation** _(rejected)_ — pros: Maximum control over who gets an account; no risk of code leakage.; cons: High operational overhead for admins; creates friction for new legitimate members; requires building an admin interface for user management.
- **Keep onboarding docs public** _(rejected)_ — pros: Zero changes to auth/registration flow.; cons: Internal research philosophy and advisor meeting standards remain visible to the general public, violating privacy/security expectations.

## Decision
Implement a static invitation code (`lab_member_invitation_code`) configured in backend settings. The registration endpoint (`user_store.register_user`) validates this code when the `visitor_profile` is 'lab_member'. Frontend forms conditionally show the input field for this profile. Onboarding KB entries are reclassified from 'public' to 'lab_member' audience.

## Consequences
Lab members must possess the shared secret code to register. If the code is compromised, it must be rotated in config/.env. Public users can still use 'Guest Mode' but lose chat history persistence and cannot access internal KB documents. The identity selection modal is now mandatory on boot, removing the previous localStorage bypass.