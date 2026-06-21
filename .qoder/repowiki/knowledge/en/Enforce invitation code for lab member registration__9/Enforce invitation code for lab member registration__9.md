---
kind: design
name: Enforce invitation code for lab member registration
source: session
category: adr
---

# Enforce invitation code for lab member registration

_Source: coding plans from commit period f38f0eb → 3eb7563 — records intent at planning time; the implementation may lag or differ._

**Status:** accepted

## Context
The application needed to restrict access to internal onboarding knowledge base entries (previously public) to verified lab members only. The existing auth system supported profiles but lacked a mechanism to prevent unauthorized users from self-registering as 'lab_member'.

## Decision drivers
- Data confidentiality for internal research materials
- Controlled user onboarding without manual admin approval
- Simplicity of implementation over complex identity providers

## Considered options
- **Shared invitation code validation** — pros: Simple to implement and distribute; no external dependencies; immediate enforcement at registration time.; cons: Code leakage allows unauthorized access; requires manual rotation if compromised; single point of failure for the secret.
- **Admin-approved registration queue** _(rejected)_ — pros: Highest security; explicit control over every account.; cons: High operational overhead for the admin; delays user onboarding; requires building a new admin workflow.
- **Keep onboarding content public** _(rejected)_ — pros: Zero friction for new users; no code changes needed.; cons: Exposes internal research philosophy and standards to the general public; violates data segregation requirements.

## Decision
Implement a shared invitation code (`lab_member_invitation_code`) configured in backend settings. The `user_store.register_user()` method now validates this code when the `visitor_profile` is 'lab_member', rejecting requests with HTTP 403 if the code is missing or incorrect. The frontend registration modal conditionally displays an input field for this code based on the selected profile.

## Consequences
Lab members can self-register if they possess the code, reducing admin workload. Internal KB entries are effectively hidden from general visitors by changing their audience metadata to 'lab_member'. If the code is leaked, it must be rotated in config/.env to restore security.