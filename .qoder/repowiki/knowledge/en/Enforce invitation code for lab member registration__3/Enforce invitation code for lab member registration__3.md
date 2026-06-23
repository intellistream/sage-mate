---
kind: design
name: Enforce invitation code for lab member registration
source: session
category: adr
---

# Enforce invitation code for lab member registration

_Source: coding plans from commit period 67e3d05 → 3ffb35c — records intent at planning time; the implementation may lag or differ._

**Status:** accepted

## Context
The application needed to restrict access to sensitive onboarding knowledge base entries (previously public) to verified lab members only, while still allowing general visitors. The existing auth system supported profiles but lacked a mechanism to verify new lab member registrations.

## Decision drivers
- Access control for internal documentation
- Prevention of unauthorized lab member account creation
- Simplicity of shared-secret verification

## Considered options
- **Invitation code validation** — pros: Simple to implement; no external identity provider required; effective gate for small teams.; cons: Code can be shared inadvertently; requires manual rotation if leaked.
- **Open registration for lab members** _(rejected)_ — pros: Zero friction for new users.; cons: Anyone could claim 'lab_member' status and access restricted onboarding materials.
- **Admin-approved registration** _(rejected)_ — pros: Highest security; explicit vetting of each user.; cons: High operational overhead for the admin; delays onboarding.

## Decision
Implement a configurable invitation code (`lab_member_invitation_code`) in `config.py` that must be provided during registration when the `lab_member` profile is selected. The backend (`user_store.py`) validates this code against the configuration, rejecting invalid attempts with HTTP 403. The frontend (`index.html`, `app.js`) conditionally displays the input field and enforces a mandatory identity selection modal on boot.

## Consequences
Lab member accounts are now gated by a shared secret. Onboarding KB entries were reclassified from 'public' to 'lab_member' audience, making them inaccessible to guests. Guests retain access but lose persistent chat history. The identity modal is now mandatory, removing the previous localStorage bypass.