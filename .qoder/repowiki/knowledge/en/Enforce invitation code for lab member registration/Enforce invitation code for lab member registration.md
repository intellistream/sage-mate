---
kind: design
name: Enforce invitation code for lab member registration
source: session
category: adr
---

# Enforce invitation code for lab member registration

_Source: coding plans from commit period 2dd47cf → b109c0f — records intent at planning time; the implementation may lag or differ._

**Status:** accepted

## Context
The application needed to restrict access to sensitive onboarding knowledge base entries (previously public) to verified lab members only, while maintaining a guest mode for public users. The existing auth system lacked a mechanism to verify affiliation during sign-up.

## Decision drivers
- Access control for internal documentation
- Prevention of unauthorized lab member account creation
- Separation of guest and authenticated user experiences

## Considered options
- **Shared static invitation code** — pros: Simple to implement in backend config and frontend form; easy to distribute to known members; low operational overhead.; cons: Code can be shared externally; no individual tracking of who invited whom; requires manual rotation if leaked.
- **Admin-approved registration queue** _(rejected)_ — pros: Highest security; admin verifies each user manually.; cons: High friction for onboarding; requires admin intervention for every new user; complex state management for pending approvals.
- **Open registration with post-hoc verification** _(rejected)_ — pros: Zero friction for sign-up.; cons: Unverified users could access sensitive data before being flagged; requires complex retroactive permission revocation logic.

## Decision
Implement a static, configurable invitation code (`lab_member_invitation_code`) that must be provided during registration when selecting the 'lab_member' profile. The backend validates this code against settings before creating the account. Onboarding KB entries are switched from 'public' to 'lab_member' audience to enforce this gate.

## Consequences
Lab members can self-register if they possess the code, reducing admin workload compared to manual approval. However, the code acts as a shared secret that must be protected and rotated if compromised. Guest users retain access but lose chat history persistence, clearly distinguishing the two tiers.