# Authentication System

<cite>
**Referenced Files in This Document**
- [auth.py](file://src/sage_faculty_twin/auth.py)
- [user_store.py](file://src/sage_faculty_twin/user_store.py)
- [models.py](file://src/sage_faculty_twin/models.py)
- [api.py](file://src/sage_faculty_twin/api.py)
- [config.py](file://src/sage_faculty_twin/config.py)
- [service.py](file://src/sage_faculty_twin/service.py)
- [history_auth.py](file://src/sage_faculty_twin/history_auth.py)
- [app.js](file://src/sage_faculty_twin/web/app.js)
- [index.html](file://src/sage_faculty_twin/web/index.html)
- [test_admin_auth.py](file://tests/test_admin_auth.py)
- [test_history_auth.py](file://tests/test_history_auth.py)
</cite>

## Update Summary
**Changes Made**
- Updated frontend authentication integration to reflect unified account view system
- Modified user-facing authentication flow documentation to account for integrated modal system
- Updated frontend architecture diagrams to show account-view tabbed interface
- Revised user experience documentation to reflect seamless authentication through unified view

## Table of Contents
1. [Introduction](#introduction)
2. [Project Structure](#project-structure)
3. [Core Components](#core-components)
4. [Architecture Overview](#architecture-overview)
5. [Detailed Component Analysis](#detailed-component-analysis)
6. [Dependency Analysis](#dependency-analysis)
7. [Performance Considerations](#performance-considerations)
8. [Troubleshooting Guide](#troubleshooting-guide)
9. [Conclusion](#conclusion)

## Introduction
This document provides comprehensive documentation for the authentication and authorization system. It explains session token generation and validation for both users and administrators, the authentication middleware, token encoding/decoding processes, and session management lifecycle. It also covers user registration and login workflows, credential validation, role-based access control, implementation examples for authentication decorators, session handling, security best practices, token expiration and refresh mechanisms, audit logging for authentication events, and integration with user stores and session persistence.

**Updated** Enhanced with unified account view system that integrates authentication modals into a single tabbed interface for improved user experience.

## Project Structure
The authentication system spans several modules with integrated frontend components:
- Token encoding/decoding and session cookie management
- User account storage and password hashing with invitation code validation
- API endpoints for authentication and protected routes
- Configuration for session secrets, TTLs, and invitation code policies
- Service layer orchestrating authentication workflows with invitation code processing
- Authorization helpers for resource access control
- Unified account view system with integrated authentication modals

```mermaid
graph TB
subgraph "API Layer"
API["FastAPI Endpoints<br/>auth.py, api.py"]
FRONT["Unified Account View<br/>app.js, index.html"]
end
subgraph "Auth Core"
AUTH["Session Tokens<br/>auth.py"]
CFG["Settings & Secrets<br/>config.py"]
INV["Invitation Code Policy<br/>config.py"]
end
subgraph "Storage"
USTORE["User Accounts<br/>user_store.py"]
MODELS["Pydantic Models<br/>models.py"]
end
subgraph "Service Layer"
SVC["Authentication Workflows<br/>service.py"]
HIST["History Access Control<br/>history_auth.py"]
end
FRONT --> API
API --> AUTH
API --> SVC
AUTH --> CFG
SVC --> USTORE
SVC --> AUTH
SVC --> MODELS
SVC --> INV
API --> HIST
```

**Diagram sources**
- [auth.py:1-214](file://src/sage_faculty_twin/auth.py#L1-L214)
- [user_store.py:1-208](file://src/sage_faculty_twin/user_store.py#L1-L208)
- [models.py:741-755](file://src/sage_faculty_twin/models.py#L741-L755)
- [api.py:510-521](file://src/sage_faculty_twin/api.py#L510-L521)
- [config.py:140-148](file://src/sage_faculty_twin/config.py#L140-L148)
- [service.py:2914-2942](file://src/sage_faculty_twin/service.py#L2914-L2942)
- [history_auth.py:6-27](file://src/sage_faculty_twin/history_auth.py#L6-L27)
- [app.js:8021-8051](file://src/sage_faculty_twin/web/app.js#L8021-L8051)
- [index.html:184-202](file://src/sage_faculty_twin/web/index.html#L184-L202)

**Section sources**
- [auth.py:1-214](file://src/sage_faculty_twin/auth.py#L1-L214)
- [user_store.py:1-208](file://src/sage_faculty_twin/user_store.py#L1-L208)
- [models.py:741-755](file://src/sage_faculty_twin/models.py#L741-L755)
- [api.py:510-521](file://src/sage_faculty_twin/api.py#L510-L521)
- [config.py:140-148](file://src/sage_faculty_twin/config.py#L140-L148)
- [service.py:2914-2942](file://src/sage_faculty_twin/service.py#L2914-L2942)
- [history_auth.py:6-27](file://src/sage_faculty_twin/history_auth.py#L6-L27)
- [app.js:8021-8051](file://src/sage_faculty_twin/web/app.js#L8021-L8051)
- [index.html:184-202](file://src/sage_faculty_twin/web/index.html#L184-L202)

## Core Components
- Session token encoding/decoding for administrators and users
- Cookie-based session management with HttpOnly and SameSite policies
- User registration with secure password hashing, email normalization, and invitation code validation
- Login validation with timing-safe comparisons and optional invitation code-based profile upgrades
- Role-based access control for administrative endpoints
- Protected resource access control for user history
- Invitation code enforcement for lab member registration and profile upgrades
- Configuration-driven session secrets, TTLs, and invitation code policies
- Unified account view system with integrated authentication modals

**Updated** Added unified account view system that consolidates authentication interfaces into a single tabbed interface.

**Section sources**
- [auth.py:16-214](file://src/sage_faculty_twin/auth.py#L16-L214)
- [user_store.py:71-161](file://src/sage_faculty_twin/user_store.py#L71-L161)
- [models.py:741-755](file://src/sage_faculty_twin/models.py#L741-L755)
- [api.py:510-521](file://src/sage_faculty_twin/api.py#L510-L521)
- [config.py:140-148](file://src/sage_faculty_twin/config.py#L140-L148)
- [service.py:2914-2942](file://src/sage_faculty_twin/service.py#L2914-L2942)
- [history_auth.py:6-27](file://src/sage_faculty_twin/history_auth.py#L6-L27)
- [app.js:8021-8051](file://src/sage_faculty_twin/web/app.js#L8021-L8051)

## Architecture Overview
The authentication system follows a layered architecture with enhanced invitation code functionality and unified frontend integration:
- API layer exposes endpoints for login/logout and protected resources with invitation code support
- Service layer validates credentials, processes invitation codes, builds sessions, and enforces RBAC
- Auth module handles token encoding/decoding and cookie management
- Storage layer persists user accounts, manages password hashes, and validates invitation codes
- Configuration module defines secrets, session lifetimes, and invitation code policies
- Unified account view system provides integrated authentication experience through tabbed interface
- Frontend captures invitation codes seamlessly through unified interface

```mermaid
sequenceDiagram
participant Client as "Client"
participant API as "FastAPI API<br/>api.py"
participant Service as "Service Layer<br/>service.py"
participant Auth as "Auth Module<br/>auth.py"
participant Store as "User Store<br/>user_store.py"
participant Config as "Settings<br/>config.py"
Client->>API : POST /auth/user/register (with invitation_code)
API->>Service : register_user(payload)
Service->>Store : register_user(name, email, visitor_profile, password, invitation_code)
Store->>Config : check lab_member_invitation_code_enabled
Store->>Store : validate invitation_code for lab_member
Store-->>Service : UserAccountResponse
Service->>Auth : build_user_session_token(user_id, email, settings)
Auth->>Config : read user_session_secret, ttl
Auth-->>Service : session_token
Service-->>API : UserAuthWorkflowResult
API->>Client : Set HttpOnly cookie (session_token)
```

**Diagram sources**
- [api.py:510-514](file://src/sage_faculty_twin/api.py#L510-L514)
- [service.py:2914-2928](file://src/sage_faculty_twin/service.py#L2914-L2928)
- [auth.py:45-54](file://src/sage_faculty_twin/auth.py#L45-L54)
- [user_store.py:71-121](file://src/sage_faculty_twin/user_store.py#L71-L121)
- [config.py:140-148](file://src/sage_faculty_twin/config.py#L140-L148)

## Detailed Component Analysis

### Unified Account View System
The authentication system now features a unified account view that integrates previously separate modals into a cohesive tabbed interface:
- Single account-view container with register and login tabs
- Dynamic content migration from legacy modals to tab panels
- Seamless tab switching between registration and login forms
- Maintained backward compatibility with hidden legacy modal elements

```mermaid
flowchart TD
LegacyModals["Legacy Modals<br/>user-register-modal<br/>user-login-modal"] --> UnifiedView["Unified Account View<br/>account-view"]
UnifiedView --> TabSystem["Tab System<br/>account-tab-register<br/>account-tab-login"]
TabSystem --> RegisterTab["Register Tab<br/>account-tab-register"]
TabSystem --> LoginTab["Login Tab<br/>account-tab-login"]
RegisterTab --> MigrateContent["Migrate Modal Content<br/>first-time load only"]
LoginTab --> MigrateContent
MigrateContent --> ActiveForms["Active Form Elements<br/>user-register-form<br/>user-login-form"]
```

**Diagram sources**
- [app.js:8021-8051](file://src/sage_faculty_twin/web/app.js#L8021-L8051)
- [index.html:184-202](file://src/sage_faculty_twin/web/index.html#L184-L202)

**Section sources**
- [app.js:8021-8051](file://src/sage_faculty_twin/web/app.js#L8021-L8051)
- [index.html:184-202](file://src/sage_faculty_twin/web/index.html#L184-L202)

### Session Token Generation and Validation
- Administrator and user sessions use distinct cookies and secrets
- Tokens are JSON payloads encoded with URL-safe base64 and signed with HMAC-SHA256
- Expiration is enforced by comparing exp against current Unix time
- Nonces are included to mitigate replay risks

```mermaid
flowchart TD
Start(["Token Decode"]) --> Split["Split token into payload_b64 and signature"]
Split --> VerifySig{"Signature valid?"}
VerifySig --> |No| ReturnNone["Return None"]
VerifySig --> |Yes| Decode["Base64 decode payload_b64"]
Decode --> Parse["Parse JSON payload"]
Parse --> ExpCheck{"exp > now?"}
ExpCheck --> |No| ReturnNone
ExpCheck --> |Yes| ReturnPayload["Return payload"]
```

**Diagram sources**
- [auth.py:193-214](file://src/sage_faculty_twin/auth.py#L193-L214)

**Section sources**
- [auth.py:182-214](file://src/sage_faculty_twin/auth.py#L182-L214)

### Authentication Middleware and Decorators
- API endpoints use dependency injection to enforce admin sessions
- The require_admin_session dependency decodes and normalizes admin payloads
- Protected routes depend on require_admin_session to gate access

```mermaid
sequenceDiagram
participant Client as "Client"
participant API as "FastAPI Endpoint<br/>api.py"
participant Dep as "Depends(require_admin_session)"
participant Service as "Service Layer<br/>service.py"
participant Auth as "Auth Module<br/>auth.py"
Client->>API : GET /admin/services
API->>Dep : Resolve require_admin_session
Dep->>Service : require_admin_session(cookie)
Service->>Auth : normalize_admin_session_payload(decode_admin_session_token)
Auth-->>Service : normalized payload or None
Service-->>Dep : dict or raises 403
Dep-->>API : dict
API-->>Client : 200 OK
```

**Diagram sources**
- [api.py:497-507](file://src/sage_faculty_twin/api.py#L497-L507)
- [api.py:490-492](file://src/sage_faculty_twin/api.py#L490-L492)
- [service.py:5600-5609](file://src/sage_faculty_twin/service.py#L5600-L5609)
- [auth.py:119-129](file://src/sage_faculty_twin/auth.py#L119-L129)

**Section sources**
- [api.py:490-492](file://src/sage_faculty_twin/api.py#L490-L492)
- [api.py:497-507](file://src/sage_faculty_twin/api.py#L497-L507)
- [service.py:5600-5609](file://src/sage_faculty_twin/service.py#L5600-L5609)
- [auth.py:119-129](file://src/sage_faculty_twin/auth.py#L119-L129)

### Token Encoding/Decoding Processes
- Payload construction includes subject, email/role, issued-at, expiration, and nonce
- Secret is per-role (admin vs user) and configurable
- Signature uses HMAC-SHA256 over base64-encoded payload
- Decoding validates signature and checks expiration

```mermaid
classDiagram
class TokenCodec {
+encode_session_cookie(payload, secret) str
+decode_session_cookie(token, secret) dict|None
}
class AdminAuth {
+build_admin_session_token(settings, username, role) str
+decode_admin_session_token(token, settings) dict|None
+normalize_admin_session_payload(payload, settings) dict|None
+require_admin(request, settings) dict
}
class UserAuth {
+build_user_session_token(user_id, email, settings) str
+decode_user_session_token(token, settings) dict|None
+set_user_session_cookie(response, token, settings) void
+clear_user_session_cookie(response) void
}
AdminAuth --> TokenCodec : "uses"
UserAuth --> TokenCodec : "uses"
```

**Diagram sources**
- [auth.py:24-86](file://src/sage_faculty_twin/auth.py#L24-L86)
- [auth.py:182-214](file://src/sage_faculty_twin/auth.py#L182-L214)

**Section sources**
- [auth.py:24-86](file://src/sage_faculty_twin/auth.py#L24-L86)
- [auth.py:182-214](file://src/sage_faculty_twin/auth.py#L182-L214)

### Session Management Lifecycle
- User registration creates a new account with hashed password, normalized email, and optional invitation code validation
- Login authenticates credentials and optionally upgrades profile based on invitation code
- Session cookie is validated on subsequent requests
- Logout clears the session cookie and returns anonymous state

```mermaid
sequenceDiagram
participant Client as "Client"
participant API as "FastAPI API<br/>api.py"
participant Service as "Service Layer<br/>service.py"
participant Auth as "Auth Module<br/>auth.py"
participant Store as "User Store<br/>user_store.py"
participant Config as "Settings<br/>config.py"
Client->>API : POST /auth/user/register (invitation_code optional)
API->>Service : register_user(payload)
Service->>Store : register_user(name, email, visitor_profile, password, invitation_code)
Store->>Config : check lab_member_invitation_code_enabled
Store->>Store : validate invitation_code for lab_member
Store-->>Service : UserAccountResponse
Service->>Auth : build_user_session_token(user_id, email, settings)
Auth->>Config : read user_session_secret, ttl
Auth-->>Service : session_token
Service-->>API : UserAuthWorkflowResult
API-->>Client : Set HttpOnly cookie
Client->>API : POST /auth/user/login (invitation_code optional)
API->>Service : login_user(payload)
Service->>Store : authenticate_user(email, password, invitation_code)
Store->>Config : check lab_member_invitation_code_enabled
Store->>Store : upgrade profile if invitation_code valid
Store-->>Service : UserAccountResponse
Service-->>API : UserAuthWorkflowResult
API-->>Client : Set HttpOnly cookie
Client->>API : GET /auth/user/session
API->>Service : get_user_session(cookie)
Service->>Auth : decode_user_session_token(cookie, settings)
Auth-->>Service : payload or None
Service-->>API : UserSessionResponse
API-->>Client : UserSessionResponse
Client->>API : POST /auth/user/logout
API->>Service : logout_user()
Service-->>API : UserSessionResponse
API-->>Client : Clear cookie
```

**Diagram sources**
- [api.py:510-521](file://src/sage_faculty_twin/api.py#L510-L521)
- [service.py:2914-2942](file://src/sage_faculty_twin/service.py#L2914-L2942)
- [auth.py:45-86](file://src/sage_faculty_twin/auth.py#L45-L86)
- [user_store.py:71-161](file://src/sage_faculty_twin/user_store.py#L71-L161)
- [config.py:140-148](file://src/sage_faculty_twin/config.py#L140-L148)

**Section sources**
- [api.py:510-521](file://src/sage_faculty_twin/api.py#L510-L521)
- [service.py:2914-2942](file://src/sage_faculty_twin/service.py#L2914-L2942)
- [auth.py:45-86](file://src/sage_faculty_twin/auth.py#L45-L86)
- [user_store.py:71-161](file://src/sage_faculty_twin/user_store.py#L71-L161)
- [config.py:140-148](file://src/sage_faculty_twin/config.py#L140-L148)

### Enhanced User Registration and Login Workflows
- Registration validates inputs, normalizes email, checks uniqueness, validates invitation code for lab members, and stores hashed credentials
- Login validates credentials using timing-safe comparison and optionally upgrades profile based on invitation code
- Both workflows issue session cookies and return session responses
- Invitation code validation is configurable and can be enabled/disabled

```mermaid
flowchart TD
RegStart["Registration Start"] --> Validate["Validate name/email/profile/password"]
Validate --> Unique{"Email unique?"}
Unique --> |No| Conflict["HTTP 409 Conflict"]
Unique --> |Yes| ProfileCheck{"Visitor profile == lab_member?"}
ProfileCheck --> |No| Hash["Hash password with scrypt"]
ProfileCheck --> |Yes| InvEnabled{"Invitation code enabled?"}
InvEnabled --> |No| Hash
InvEnabled --> |Yes| InvValid{"Invitation code valid?"}
InvValid --> |No| Forbidden["HTTP 403 Forbidden"]
InvValid --> |Yes| Hash
Hash --> Persist["Persist account record"]
Persist --> DoneReg["Return UserSessionResponse"]
LoginStart["Login Start"] --> Find["Lookup user by normalized email"]
Find --> Found{"User found?"}
Found --> |No| Unauthorized["HTTP 401 Unauthorized"]
Found --> |Yes| Compare["Compare digests (timing-safe)"]
Compare --> Match{"Match?"}
Match --> |No| Unauthorized
Match --> |Yes| UpgradeCheck{"Profile upgrade needed?"}
UpgradeCheck --> |No| DoneLogin["Return UserSessionResponse"]
UpgradeCheck --> |Yes| InvCheck{"Invitation code provided and valid?"}
InvCheck --> |No| DoneLogin
InvCheck --> |Yes| Upgrade["Upgrade profile to lab_member"]
Upgrade --> PersistUpgrade["Persist upgraded record"]
PersistUpgrade --> DoneLogin
```

**Diagram sources**
- [user_store.py:71-161](file://src/sage_faculty_twin/user_store.py#L71-L161)
- [auth.py:158-173](file://src/sage_faculty_twin/auth.py#L158-L173)

**Section sources**
- [user_store.py:71-161](file://src/sage_faculty_twin/user_store.py#L71-L161)
- [auth.py:158-173](file://src/sage_faculty_twin/auth.py#L158-L173)

### Invitation Code Functionality
- Invitation code validation occurs during user registration for lab member profiles
- Invitation code validation can trigger profile upgrades during login for non-lab members
- Configuration controls whether invitation code enforcement is enabled and what the expected code is
- Frontend automatically sets visitor profile to lab_member when invitation code is provided

```mermaid
flowchart TD
Start["Invitation Code Processing"] --> RegFlow["Registration Flow"]
Start --> LoginFlow["Login Flow"]
RegFlow --> CheckProfile{"Visitor profile == lab_member?"}
CheckProfile --> |No| SkipReg["Skip invitation code validation"]
CheckProfile --> |Yes| CheckEnabled{"lab_member_invitation_code_enabled?"}
CheckEnabled --> |No| SkipReg
CheckEnabled --> |Yes| ValidateReg["Validate invitation code"]
ValidateReg --> ValidReg{"Valid?"}
ValidReg --> |No| ErrorReg["HTTP 403 Forbidden"]
ValidReg --> |Yes| ContinueReg["Continue registration"]
LoginFlow --> CheckUpgrade{"Profile upgrade needed?"}
CheckUpgrade --> |No| SkipLogin["Skip upgrade"]
CheckUpgrade --> |Yes| CheckInv{"Invitation code provided?"}
CheckInv --> |No| SkipLogin
CheckInv --> |Yes| ValidateLogin["Validate invitation code"]
ValidateLogin --> ValidLogin{"Valid?"}
ValidLogin --> |No| SkipLogin
ValidLogin --> |Yes| UpgradeProfile["Upgrade to lab_member"]
UpgradeProfile --> PersistUpgrade["Persist upgraded record"]
```

**Diagram sources**
- [user_store.py:92-161](file://src/sage_faculty_twin/user_store.py#L92-L161)
- [config.py:140-148](file://src/sage_faculty_twin/config.py#L140-L148)
- [app.js:807-808](file://src/sage_faculty_twin/web/app.js#L807-L808)

**Section sources**
- [user_store.py:92-161](file://src/sage_faculty_twin/user_store.py#L92-L161)
- [config.py:140-148](file://src/sage_faculty_twin/config.py#L140-L148)
- [app.js:807-808](file://src/sage_faculty_twin/web/app.js#L807-L808)

### Credential Validation and Security Best Practices
- Timing-safe digest comparison prevents timing attacks
- Password hashing uses scrypt with configurable cost parameters
- Email normalization ensures case-insensitive uniqueness
- Session cookies use HttpOnly and SameSite lax; secure flag is disabled by default
- Secrets and TTLs are configurable via environment-backed settings
- Invitation code validation uses constant-time comparison to prevent timing attacks

```mermaid
classDiagram
class CredentialValidation {
+validate_admin_credentials(username, password, settings) (str,str)
+authenticate_user(email, password, invitation_code) UserAccountResponse
}
class Security {
+timing_safe_compare(a, b) bool
+hash_password(password, salt) str
+normalize_email(email) str
}
class InvitationCodeSecurity {
+validate_invitation_code(provided, expected) bool
+check_invitation_code_enabled() bool
}
CredentialValidation --> Security : "uses"
CredentialValidation --> InvitationCodeSecurity : "uses"
```

**Diagram sources**
- [auth.py:158-173](file://src/sage_faculty_twin/auth.py#L158-L173)
- [user_store.py:123-161](file://src/sage_faculty_twin/user_store.py#L123-L161)
- [user_store.py:140-161](file://src/sage_faculty_twin/user_store.py#L140-L161)

**Section sources**
- [auth.py:158-173](file://src/sage_faculty_twin/auth.py#L158-L173)
- [user_store.py:123-161](file://src/sage_faculty_twin/user_store.py#L123-L161)
- [user_store.py:140-161](file://src/sage_faculty_twin/user_store.py#L140-L161)

### Role-Based Access Control (RBAC)
- Admin roles: super_admin and manager
- Manager privileges are elevated for specific endpoints
- Identity resolution maps usernames to roles with fallback logic
- Normalized payloads expose consistent role claims

```mermaid
flowchart TD
Start(["Admin Identity Resolution"]) --> Extract["Extract sub and role from payload"]
Extract --> Normalize["Normalize username and role"]
Normalize --> Check{"Role in {super_admin, manager}?"}
Check --> |Yes| ReturnRoles["Return username, role"]
Check --> |No| ManagerCheck{"Username equals manager?"}
ManagerCheck --> |Yes| SetManager["Set role = manager"]
ManagerCheck --> |No| SetSuper["Set role = super_admin"]
SetManager --> ReturnRoles
SetSuper --> ReturnRoles
```

**Diagram sources**
- [auth.py:132-155](file://src/sage_faculty_twin/auth.py#L132-L155)

**Section sources**
- [auth.py:132-155](file://src/sage_faculty_twin/auth.py#L132-L155)

### Session Handling and Cookies
- Separate cookies for admin and user sessions
- Cookies set with HttpOnly, SameSite lax, and configurable TTL
- Logout endpoints clear cookies and reset session state

```mermaid
sequenceDiagram
participant API as "API<br/>api.py"
participant Auth as "Auth<br/>auth.py"
participant Resp as "Response"
API->>Auth : set_admin_session_cookie(response, token, settings)
Auth->>Resp : set_cookie(admin cookie)
API-->>Resp : 200 OK
API->>Auth : clear_admin_session_cookie(response)
Auth->>Resp : delete_cookie(admin cookie)
API-->>Resp : 200 OK
```

**Diagram sources**
- [api.py:497-507](file://src/sage_faculty_twin/api.py#L497-L507)
- [auth.py:57-86](file://src/sage_faculty_twin/auth.py#L57-L86)

**Section sources**
- [api.py:497-507](file://src/sage_faculty_twin/api.py#L497-L507)
- [auth.py:57-86](file://src/sage_faculty_twin/auth.py#L57-L86)

### Token Expiration and Refresh Mechanisms
- Tokens carry exp timestamps and are validated at decode time
- Current implementation does not include automatic token refresh
- TTLs are configured per role via settings

**Section sources**
- [auth.py:20-54](file://src/sage_faculty_twin/auth.py#L20-L54)
- [config.py:136-139](file://src/sage_faculty_twin/config.py#L136-L139)

### Audit Logging for Authentication Events
- Authentication endpoints return session state responses
- Tests demonstrate successful login/logout flows and session state transitions
- No dedicated audit log file is implemented in the referenced code

**Section sources**
- [test_admin_auth.py:254-280](file://tests/test_admin_auth.py#L254-L280)
- [test_admin_auth.py:563-621](file://tests/test_admin_auth.py#L563-L621)

### Integration with User Stores and Session Persistence
- User accounts stored as JSON files keyed by UUID
- Records indexed by ID and normalized email for fast lookup
- Session persistence relies on cookies; no server-side session store
- Invitation code validation occurs during registration and login workflows

**Section sources**
- [user_store.py:62-208](file://src/sage_faculty_twin/user_store.py#L62-L208)
- [auth.py:57-86](file://src/sage_faculty_twin/auth.py#L57-L86)

### Unified Frontend Authentication Experience
The unified account view system provides a seamless authentication experience:
- Single entry point for both registration and login
- Tabbed interface eliminates modal switching complexity
- Dynamic content migration preserves event handlers and form state
- Backward compatibility maintained through hidden legacy modal elements
- Enhanced user experience with integrated invitation code handling

```mermaid
sequenceDiagram
participant User as "User"
participant UnifiedView as "Unified Account View<br/>openAccountView()"
participant TabSystem as "Tab System<br/>switchAccountTab()"
participant LegacyModals as "Legacy Modals<br/>user-register-modal<br/>user-login-modal"
participant API as "Backend API<br/>api.py"
User->>UnifiedView : Click account button
UnifiedView->>LegacyModals : Migrate content (first open)
UnifiedView->>TabSystem : switchAccountTab(register|login)
TabSystem->>UnifiedView : Show selected tab
UnifiedView->>API : Submit form data
API-->>UnifiedView : Authentication response
UnifiedView->>User : Display success/error message
```

**Diagram sources**
- [app.js:8021-8051](file://src/sage_faculty_twin/web/app.js#L8021-L8051)
- [index.html:184-202](file://src/sage_faculty_twin/web/index.html#L184-L202)

**Section sources**
- [app.js:8021-8051](file://src/sage_faculty_twin/web/app.js#L8021-L8051)
- [index.html:184-202](file://src/sage_faculty_twin/web/index.html#L184-L202)

## Dependency Analysis
The authentication system exhibits clear separation of concerns with enhanced invitation code functionality and unified frontend integration:
- API depends on Service for orchestration
- Service depends on Auth for token handling, User Store for credentials, and Config for policies
- Auth depends on Config for secrets and TTLs
- Models define request/response contracts used across layers
- Unified account view system integrates frontend components with backend authentication
- Legacy modal elements maintained for backward compatibility

```mermaid
graph LR
API["api.py"] --> SVC["service.py"]
SVC --> AUTH["auth.py"]
SVC --> USTORE["user_store.py"]
SVC --> MODELS["models.py"]
SVC --> CFG["config.py"]
AUTH --> CFG
USTORE --> CFG
FRONT["app.js<br/>index.html"] --> API
UNIFIEDVIEW["Unified Account View"] --> FRONT
LEGACYMODALS["Legacy Modals"] --> UNIFIEDVIEW
```

**Diagram sources**
- [api.py:22-76](file://src/sage_faculty_twin/api.py#L22-L76)
- [service.py:29-131](file://src/sage_faculty_twin/service.py#L29-L131)
- [auth.py:13-15](file://src/sage_faculty_twin/auth.py#L13-L15)
- [config.py:9-15](file://src/sage_faculty_twin/config.py#L9-L15)
- [models.py:741-755](file://src/sage_faculty_twin/models.py#L741-L755)
- [app.js:8021-8051](file://src/sage_faculty_twin/web/app.js#L8021-L8051)
- [index.html:184-202](file://src/sage_faculty_twin/web/index.html#L184-L202)

**Section sources**
- [api.py:22-76](file://src/sage_faculty_twin/api.py#L22-L76)
- [service.py:29-131](file://src/sage_faculty_twin/service.py#L29-L131)
- [auth.py:13-15](file://src/sage_faculty_twin/auth.py#L13-L15)
- [config.py:9-15](file://src/sage_faculty_twin/config.py#L9-L15)
- [models.py:741-755](file://src/sage_faculty_twin/models.py#L741-L755)
- [app.js:8021-8051](file://src/sage_faculty_twin/web/app.js#L8021-L8051)
- [index.html:184-202](file://src/sage_faculty_twin/web/index.html#L184-L202)

## Performance Considerations
- Token signing and verification are lightweight; negligible overhead
- Password hashing uses scrypt with tunable cost parameters
- Cookie-based sessions eliminate server-side state, improving scalability
- Invitation code validation adds minimal overhead with constant-time comparison
- Unified account view reduces DOM manipulation overhead through content migration
- Consider adding refresh tokens and sliding expiration for long-lived sessions

## Troubleshooting Guide
Common issues and resolutions:
- 401 Unauthorized on login: incorrect email/password
- 403 Forbidden on admin endpoints: missing or invalid admin session cookie
- 409 Conflict on registration: duplicate email address
- 403 Forbidden accessing user history: must be logged in with matching email
- 403 Forbidden on lab member registration: incorrect or missing invitation code
- 400 Bad Request on registration: invalid visitor profile for invitation code flow
- Unified view tab switching issues: ensure proper tab element IDs are present
- Legacy modal compatibility: verify hidden modal elements remain accessible for migration

**Updated** Added troubleshooting for unified account view system and legacy modal compatibility.

**Section sources**
- [user_store.py:87-161](file://src/sage_faculty_twin/user_store.py#L87-L161)
- [auth.py:119-129](file://src/sage_faculty_twin/auth.py#L119-L129)
- [user_store.py:86-89](file://src/sage_faculty_twin/user_store.py#L86-L89)
- [history_auth.py:15-26](file://src/sage_faculty_twin/history_auth.py#L15-L26)
- [app.js:8021-8051](file://src/sage_faculty_twin/web/app.js#L8021-L8051)

## Conclusion
The authentication system provides robust session-based authentication for both users and administrators with enhanced invitation code functionality for controlled lab member registration and profile upgrades. The system now features a unified account view that integrates authentication modals into a cohesive tabbed interface, improving user experience while maintaining backward compatibility. It leverages secure token encoding, timing-safe credential validation, and role-based access control. The invitation code system allows for gated access to lab member profiles while maintaining security through constant-time validation. The unified frontend architecture streamlines the authentication process through dynamic content migration and seamless tab switching. While the current implementation focuses on cookie-based sessions without server-side persistence, it offers a solid foundation for extending with refresh tokens, audit logging, and enhanced invitation code management as needed.