---
kind: design
name: Enforce invitation code for lab member registration
source: session
category: adr
---

# Enforce invitation code for lab member registration

_Source: coding plans from commit period c05d89b → 8894345 — records intent at planning time; the implementation may lag or differ._

**Status:** accepted

## Context
The application needed to restrict access to sensitive onboarding knowledge base entries (previously public) to verified lab members only, while maintaining a guest mode for general visitors. The existing auth system lacked a mechanism to verify affiliation during the initial registration process.

## Decision drivers
- Access control for internal documentation
- Prevention of unauthorized lab member account creation
- Separation of guest and authenticated user experiences

## Considered options
- **Shared static invitation code** — pros: Simple to implement and distribute within the lab; low operational overhead; no need for an admin UI or database table for codes.; cons: Code leakage allows unauthorized access; difficult to revoke individual access without changing the global code.
- **Admin-approved registration queue** _(rejected)_ — pros: Granular control over each user; easy revocation.; cons: Requires building an admin interface and asynchronous approval workflow; higher complexity for a small team.
- **Keep onboarding docs public** _(rejected)_ — pros: No friction for new users.; cons: Exposes internal research philosophy and standards to the general public.

## Decision
Implement a static, configuration-driven invitation code (`lab_member_invitation_code`) that must be provided during registration when selecting the 'lab_member' profile. The backend validates this code against `settings.lab_member_invitation_code` before creating the account. Onboarding KB entries are switched to `audience: 'lab_member'` to enforce this restriction.

## Consequences
Lab members must obtain the code from staff to register. Guest users can still access the app but will not see internal documents and will have ephemeral chat history. The security model relies on the secrecy of the shared code rather than individual token management.