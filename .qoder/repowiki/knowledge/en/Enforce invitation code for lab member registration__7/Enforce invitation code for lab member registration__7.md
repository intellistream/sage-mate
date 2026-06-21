---
kind: design
name: Enforce invitation code for lab member registration
source: session
category: adr
---

# Enforce invitation code for lab member registration

_Source: coding plans from commit period c6c2ee0 → c05d89b — records intent at planning time; the implementation may lag or differ._

**Status:** accepted

## Context
The application needed to restrict access to sensitive onboarding knowledge base entries (previously public) to verified lab members only, while maintaining a guest mode for public users. The existing auth system lacked a mechanism to verify affiliation during the sign-up process.

## Decision drivers
- Access control for internal research materials
- Prevention of unauthorized account creation as lab members
- Simplicity of shared-secret verification over complex identity providers

## Considered options
- **Invitation code validation** — pros: Simple to implement; no external dependencies; immediate enforcement at registration time; easy to rotate via config/env.; cons: Code can be shared among unauthorized users; requires manual distribution by admins.
- **Admin approval workflow** _(rejected)_ — pros: Higher security; explicit vetting of each user.; cons: Significantly higher implementation complexity; introduces latency in onboarding; requires admin UI and notification logic.
- **Keep onboarding docs public** _(rejected)_ — pros: Zero friction for new users; no code changes needed for access control.; cons: Exposes internal lab rhythms, standards, and directions to the general public.

## Decision
Implement a mandatory invitation code field for 'lab_member' profile registration. The backend validates this code against a configured secret (`lab_member_invitation_code`) before creating the account. Onboarding KB entries are reclassified from 'public' to 'lab_member' audience to enforce this restriction.

## Consequences
Lab members must possess a valid code to register, preventing casual sign-ups. Guest users retain access but lose persistent chat history. The system relies on the secrecy of the invitation code rather than individual user vetting.