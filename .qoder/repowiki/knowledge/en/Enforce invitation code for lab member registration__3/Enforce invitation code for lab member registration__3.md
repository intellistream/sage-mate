---
kind: design
name: Enforce invitation code for lab member registration
source: session
category: adr
---

# Enforce invitation code for lab member registration

_Source: coding plans from commit period 8dd53dd → 2dd47cf — records intent at planning time; the implementation may lag or differ._

**Status:** accepted

## Context
The onboarding knowledge base entries contain internal lab procedures and research directions that should not be publicly accessible. The existing auth system distinguishes between 'lab_member' and 'general_visitor' profiles, but the registration flow lacked a mechanism to verify that a user claiming to be a lab member is actually authorized.

## Decision drivers
- data confidentiality for internal lab materials
- controlled access to sensitive onboarding content
- simplicity of shared-secret verification

## Considered options
- **Invitation code validation** — pros: Simple to implement and manage; no external identity provider required; effective for small, closed groups like a research lab.; cons: Code can be leaked; requires manual rotation if compromised; less secure than individual admin approval.
- **Admin-approved registration** _(rejected)_ — pros: Highest security; each account is individually vetted.; cons: High operational overhead for the PI/admin; slows down onboarding for new students.
- **Public access with redacted content** _(rejected)_ — pros: Zero friction for users.; cons: Risk of accidental exposure of internal schedules, meeting notes, and research strategies.

## Decision
Require an invitation code during registration for users selecting the 'lab_member' profile. The code is validated server-side in `user_store.py` against a config value (`lab_member_invitation_code`). If the code is missing or incorrect, registration is rejected with HTTP 403. The frontend conditionally shows the input field only when 'lab_member' is selected.

## Consequences
Lab members must obtain the code from existing members or the PI to register. This prevents unauthorized public access to `audience: "lab_member"` documents. The code must be managed securely in environment variables and rotated if leaked.