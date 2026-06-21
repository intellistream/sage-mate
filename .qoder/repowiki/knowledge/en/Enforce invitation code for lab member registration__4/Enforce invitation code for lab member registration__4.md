---
kind: design
name: Enforce invitation code for lab member registration
source: session
category: adr
---

# Enforce invitation code for lab member registration

_Source: coding plans from commit period b109c0f → 67e3d05 — records intent at planning time; the implementation may lag or differ._

**Status:** accepted

## Context
The application needed to restrict access to sensitive onboarding knowledge base entries (previously public) to verified lab members only, while maintaining a guest mode for public users. The existing auth system lacked a mechanism to vet new 'lab_member' accounts during sign-up.

## Decision drivers
- Access control for internal research materials
- Prevention of unauthorized account creation
- Simplicity of shared-secret verification

## Considered options
- **Invitation code validation** — pros: Simple to implement; no external identity provider required; effective barrier against random sign-ups.; cons: Code leakage allows unauthorized access; requires manual distribution of the code.
- **Open registration for lab members** _(rejected)_ — pros: Frictionless onboarding.; cons: Anyone could claim 'lab_member' status and access restricted 'audience: lab_member' documents.
- **Admin-approved registration** _(rejected)_ — pros: Highest security; explicit control over each user.; cons: High operational overhead; requires admin UI and notification workflows not currently present.

## Decision
Implement a configurable invitation code (`lab_member_invitation_code`) in `config.py` that must be provided during registration when selecting the 'lab_member' profile. The backend (`user_store.py`) validates this code against the settings, rejecting invalid attempts with HTTP 403. The frontend (`index.html`, `app.js`) conditionally displays the input field and enforces an initial identity selection modal.

## Consequences
Lab member onboarding now requires a shared secret, preventing arbitrary access to restricted KB entries. The system relies on the secrecy of the code rather than individual approvals. Guest users retain access but without persistent history, and the 'identity-modal' ensures users consciously choose their access level on every session start if not already authenticated.