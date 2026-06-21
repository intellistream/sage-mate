# Integrated Account Management View

<cite>
**Referenced Files in This Document**
- [auth.py](file://src/sage_faculty_twin/auth.py)
- [api.py](file://src/sage_faculty_twin/api.py)
- [service.py](file://src/sage_faculty_twin/service.py)
- [user_store.py](file://src/sage_faculty_twin/user_store.py)
- [app.js](file://src/sage_faculty_twin/web/app.js)
- [index.html](file://src/sage_faculty_twin/web/index.html)
- [models.py](file://src/sage_faculty_twin/models.py)
</cite>

## Update Summary
**Changes Made**
- Added documentation for new user account provisioning as part of testing infrastructure
- Enhanced visitor profile documentation to include lab member accounts
- Updated user account storage and authentication flow documentation
- Added information about invitation code system for lab member access

## Table of Contents
1. [Introduction](#introduction)
2. [System Architecture](#system-architecture)
3. [Core Components](#core-components)
4. [Account Management Implementation](#account-management-implementation)
5. [Session Management](#session-management)
6. [User Authentication Flow](#user-authentication-flow)
7. [Frontend Integration](#frontend-integration)
8. [Security Considerations](#security-considerations)
9. [Data Storage](#data-storage)
10. [Testing Infrastructure](#testing-infrastructure)
11. [Troubleshooting Guide](#troubleshooting-guide)
12. [Conclusion](#conclusion)

## Introduction

The Integrated Account Management View is a comprehensive user authentication and session management system built into the SAGE Faculty Twin platform. This system provides seamless user registration, login, and session persistence capabilities while maintaining robust security standards and user experience.

The system integrates tightly with the frontend application through a modern JavaScript interface that supports tabbed account management views, real-time session updates, and responsive design patterns. It leverages a layered architecture with clear separation of concerns between authentication logic, session management, and user data storage.

**Updated** The system now includes enhanced support for lab member accounts as part of the testing infrastructure, with dedicated visitor profiles and invitation code validation for controlled access.

## System Architecture

The Integrated Account Management View follows a multi-layered architecture that ensures scalability, security, and maintainability:

```mermaid
graph TB
subgraph "Frontend Layer"
A[Web Interface]
B[Account Management View]
C[Session Management]
D[Visitor Profile Selection]
end
subgraph "API Layer"
E[FastAPI Endpoints]
F[Authentication Routes]
G[Session Handlers]
H[Visitor Profile Validation]
end
subgraph "Service Layer"
I[DigitalTwinService]
J[User Authentication Service]
K[Session Validation]
L[Invitation Code Verification]
end
subgraph "Data Layer"
M[User Store]
N[Session Storage]
O[Configuration Management]
P[Visitor Profile Registry]
end
A --> E
B --> E
C --> E
D --> E
E --> I
F --> J
G --> K
H --> L
I --> M
J --> M
K --> N
L --> O
M --> P
```

**Diagram sources**
- [api.py:499-529](file://src/sage_faculty_twin/api.py#L499-L529)
- [service.py:2915-2946](file://src/sage_faculty_twin/service.py#L2915-L2946)
- [auth.py:16-86](file://src/sage_faculty_twin/auth.py#L16-L86)

## Core Components

### Authentication Module

The authentication module provides the foundation for secure user management through cookie-based session tokens:

```mermaid
classDiagram
class AuthModule {
+ADMIN_COOKIE_NAME : string
+USER_COOKIE_NAME : string
+build_admin_session_token() string
+build_user_session_token() string
+set_admin_session_cookie() void
+set_user_session_cookie() void
+decode_admin_session_token() dict
+decode_user_session_token() dict
+validate_admin_credentials() tuple
}
class SessionToken {
+sub : string
+email : string
+iat : int
+exp : int
+nonce : string
+role : string
}
class CookieHandler {
+set_cookie() void
+delete_cookie() void
+validate_signature() bool
+check_expiration() bool
}
AuthModule --> SessionToken : creates
AuthModule --> CookieHandler : uses
```

**Diagram sources**
- [auth.py:16-86](file://src/sage_faculty_twin/auth.py#L16-L86)

**Section sources**
- [auth.py:16-86](file://src/sage_faculty_twin/auth.py#L16-L86)

### User Store Management

The user store manages persistent user data with secure password hashing and validation:

```mermaid
classDiagram
class UserAccountStore {
-_settings : AppSettings
-_path : Path
-_records_by_id : dict
-_records_by_email : dict
+register_user() UserAccountResponse
+authenticate_user() UserAccountResponse
+get_user_by_id() UserAccountResponse
+count_users() int
+_persist_record() void
+_load_from_disk() void
+_hash_password() string
+_normalize_email() string
}
class UserAccountRecord {
+user_id : string
+name : string
+email : string
+visitor_profile : string
+password_salt : string
+password_hash : string
+created_at : datetime
+updated_at : datetime
+to_dict() dict
+from_dict() UserAccountRecord
+to_response() UserAccountResponse
}
UserAccountStore --> UserAccountRecord : manages
```

**Diagram sources**
- [user_store.py:62-200](file://src/sage_faculty_twin/user_store.py#L62-L200)

**Section sources**
- [user_store.py:62-200](file://src/sage_faculty_twin/user_store.py#L62-L200)

## Account Management Implementation

### Frontend Account View

The frontend implements a sophisticated account management interface with tabbed navigation and modal integration:

```mermaid
sequenceDiagram
participant User as User
participant Sidebar as Sidebar
participant AccountView as AccountView
participant Modal as Modal
participant API as API Layer
User->>Sidebar : Click Account Icon
Sidebar->>AccountView : openAccountView()
AccountView->>Modal : Initialize Register/Login Forms
Modal->>AccountView : Load Form Content
AccountView->>AccountView : switchAccountTab(register)
User->>AccountView : Fill Registration Form
AccountView->>API : POST /auth/user/register
API->>API : Validate Input & Hash Password
API->>User : Set User Session Cookie
API-->>AccountView : UserSessionResponse
AccountView->>AccountView : Close Account View
AccountView->>User : Show User Dashboard
```

**Diagram sources**
- [app.js:8021-8051](file://src/sage_faculty_twin/web/app.js#L8021-L8051)
- [api.py:512-516](file://src/sage_faculty_twin/api.py#L512-L516)

The account management view consists of two primary tabs:

1. **Registration Tab**: Allows new users to create accounts with validation
2. **Login Tab**: Provides authentication for existing users

**Section sources**
- [app.js:8021-8051](file://src/sage_faculty_twin/web/app.js#L8021-L8051)
- [index.html:185-200](file://src/sage_faculty_twin/web/index.html#L185-L200)

### Backend API Endpoints

The backend exposes comprehensive authentication endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/user/register` | POST | Creates new user accounts |
| `/auth/user/login` | POST | Authenticates existing users |
| `/auth/user/logout` | POST | Terminates user sessions |
| `/auth/user/session` | GET | Retrieves current user session |

**Section sources**
- [api.py:512-529](file://src/sage_faculty_twin/api.py#L512-L529)

## Session Management

### Cookie-Based Authentication

The system implements secure cookie-based session management with configurable expiration:

```mermaid
flowchart TD
Start([User Authentication]) --> ValidateInput["Validate Credentials"]
ValidateInput --> InputValid{"Credentials Valid?"}
InputValid --> |No| ReturnError["Return 401 Unauthorized"]
InputValid --> |Yes| CreateToken["Create Session Token"]
CreateToken --> SetCookie["Set Secure Cookie"]
SetCookie --> UpdateStore["Update Session Store"]
UpdateStore --> ReturnSuccess["Return UserSessionResponse"]
ReturnError --> End([End])
ReturnSuccess --> End
```

**Diagram sources**
- [auth.py:57-86](file://src/sage_faculty_twin/auth.py#L57-L86)
- [service.py:2931-2943](file://src/sage_faculty_twin/service.py#L2931-L2943)

### Session Validation

Session validation occurs on each request through middleware that checks cookie authenticity and expiration:

**Section sources**
- [auth.py:193-214](file://src/sage_faculty_twin/auth.py#L193-L214)
- [api.py:474-476](file://src/sage_faculty_twin/api.py#L474-L476)

## User Authentication Flow

### Registration Process

The registration process follows a secure multi-step validation and storage workflow:

```mermaid
sequenceDiagram
participant Client as Client Application
participant API as Authentication API
participant Store as User Store
participant Auth as Auth Module
participant Cookie as Cookie Handler
Client->>API : POST /auth/user/register
API->>API : Validate Registration Data
API->>Store : register_user()
Store->>Store : Normalize Email & Validate
Store->>Store : Generate Salt & Hash Password
Store->>Store : Persist User Record
Store-->>API : UserAccountResponse
API->>Auth : build_user_session_token()
Auth->>Cookie : set_user_session_cookie()
Cookie-->>API : Cookie Set Successfully
API-->>Client : UserSessionResponse with Session Token
```

**Diagram sources**
- [user_store.py:71-121](file://src/sage_faculty_twin/user_store.py#L71-L121)
- [service.py:2915-2929](file://src/sage_faculty_twin/service.py#L2915-L2929)

### Login Process

The login process validates credentials and establishes authenticated sessions:

**Section sources**
- [user_store.py:123-161](file://src/sage_faculty_twin/user_store.py#L123-L161)
- [service.py:2931-2943](file://src/sage_faculty_twin/service.py#L2931-L2943)

## Frontend Integration

### Responsive Design Implementation

The account management view integrates seamlessly with the responsive frontend architecture:

```mermaid
graph LR
subgraph "Desktop Layout"
A[Main Chat Interface]
B[Account View Panel]
C[Settings Drawer]
D[Status Panel]
end
subgraph "Mobile Layout"
E[Bottom Sheet View]
F[Modal Forms]
G[Responsive Navigation]
end
B --> |Tabs| H[Register/Login Forms]
H --> I[Form Validation]
I --> J[API Communication]
J --> K[Session Updates]
```

**Diagram sources**
- [app.js:8021-8051](file://src/sage_faculty_twin/web/app.js#L8021-L8051)
- [index.html:185-200](file://src/sage_faculty_twin/web/index.html#L185-L200)

### Real-time Session Updates

The frontend maintains real-time synchronization of user session states:

**Section sources**
- [app.js:8181-8189](file://src/sage_faculty_twin/web/app.js#L8181-L8189)
- [api.py:474-476](file://src/sage_faculty_twin/api.py#L474-L476)

## Security Considerations

### Password Security

The system implements industry-standard password hashing using scrypt with configurable cost parameters:

- **Algorithm**: scrypt with N=2^14, r=8, p=1
- **Salt Generation**: Cryptographically secure random 16-byte salt
- **Storage**: Separate salt and hash fields for each user
- **Validation**: Constant-time comparison to prevent timing attacks

### Session Security

Cookie-based sessions provide secure, stateless authentication:

- **HttpOnly Cookies**: Prevents XSS attacks
- **SameSite Protection**: CSRF mitigation
- **Secure Transport**: Configurable secure flag
- **Expiration Handling**: Automatic session cleanup
- **Nonce Support**: Additional entropy for token validation

### Input Validation

Comprehensive input validation prevents injection attacks and data corruption:

- **Email Validation**: RFC-compliant email format checking
- **Password Strength**: Minimum length and complexity requirements
- **Visitor Profile Validation**: Whitelisted profile values only
- **Rate Limiting**: Built-in protection against brute force attacks

**Section sources**
- [user_store.py:188-196](file://src/sage_faculty_twin/user_store.py#L188-L196)
- [auth.py:182-214](file://src/sage_faculty_twin/auth.py#L182-L214)

## Data Storage

### Persistent Storage Architecture

User data is stored in JSON format with automatic indexing and retrieval:

```mermaid
erDiagram
USER_ACCOUNT {
string user_id PK
string name
string email UK
string visitor_profile
string password_salt
string password_hash
datetime created_at
datetime updated_at
}
SESSION_TOKEN {
string session_id PK
string user_id FK
string token_data
datetime created_at
datetime expires_at
}
CONFIGURATION {
string setting_name PK
string setting_value
datetime updated_at
}
USER_ACCOUNT ||--o{ SESSION_TOKEN : has
```

**Diagram sources**
- [user_store.py:16-60](file://src/sage_faculty_twin/user_store.py#L16-L60)

### Data Integrity

The storage system ensures data integrity through:

- **Atomic Operations**: Complete transaction support
- **Consistency Checks**: Email uniqueness enforcement
- **Backup Support**: Automatic file-based persistence
- **Migration Support**: Schema evolution capabilities

**Section sources**
- [user_store.py:170-176](file://src/sage_faculty_twin/user_store.py#L170-L176)
- [user_store.py:178-183](file://src/sage_faculty_twin/user_store.py#L178-L183)

## Testing Infrastructure

### Lab Member Account Provisioning

The system includes dedicated support for lab member accounts as part of the testing infrastructure:

**Updated** The testing infrastructure now includes provisioned lab member accounts with controlled access through invitation codes.

#### Visitor Profile System

The system supports four distinct visitor profiles with different access levels:

| Profile Type | Access Level | Description | Invitation Code Required |
|--------------|--------------|-------------|-------------------------|
| `general_visitor` | Basic | Public access for general visitors | No |
| `hust_undergraduate` | Course Access | Access to undergraduate course materials | No |
| `paper_writing_student` | Writing Access | Access to thesis writing resources | No |
| `lab_member` | Full Access | Complete research system access | Yes |

#### Invitation Code Validation

Lab member accounts require invitation code validation during registration and login:

```mermaid
flowchart TD
Start([Lab Member Registration]) --> CheckCode["Check Invitation Code Enabled"]
CheckCode --> |Enabled| ValidateCode["Validate Invitation Code"]
CheckCode --> |Disabled| CreateAccount["Create Account"]
ValidateCode --> CodeValid{"Code Valid?"}
CodeValid --> |Yes| CreateAccount
CodeValid --> |No| ReturnError["Return 403 Forbidden"]
CreateAccount --> End([Account Created])
ReturnError --> End
```

**Diagram sources**
- [user_store.py:92-104](file://src/sage_faculty_twin/user_store.py#L92-L104)

#### Test Account Examples

The testing infrastructure includes pre-provisioned lab member accounts:

- **Test Account 1**: `8e5a47f9-49e8-4132-b983-dff1314a6d05` - Lab User
- **Test Account 2**: `01215b72-6871-483f-8799-d8f0a6d909df` - Lab User  
- Additional lab member accounts for comprehensive testing

**Section sources**
- [user_store.py:92-104](file://src/sage_faculty_twin/user_store.py#L92-L104)
- [data/user_accounts/8e5a47f9-49e8-4132-b983-dff1314a6d05.json:1-11](file://data/user_accounts/8e5a47f9-49e8-4132-b983-dff1314a6d05.json#L1-L11)

## Troubleshooting Guide

### Common Authentication Issues

**Issue**: Users cannot log in despite correct credentials
- **Cause**: Password hash mismatch or expired session
- **Solution**: Verify password hashing algorithm and session expiration
- **Debug Steps**: Check user record password hash, validate session cookie

**Issue**: Registration fails with validation errors
- **Cause**: Invalid email format or duplicate email address
- **Solution**: Validate input format and check existing user records
- **Debug Steps**: Test email regex pattern, query user store for duplicates

**Issue**: Session cookies not persisting
- **Cause**: Browser privacy settings or cookie restrictions
- **Solution**: Check SameSite and Secure cookie attributes
- **Debug Steps**: Verify browser cookie settings, test cross-origin requests

**Issue**: Lab member registration blocked by invitation code
- **Cause**: Invitation code validation failure
- **Solution**: Verify invitation code configuration and enablement
- **Debug Steps**: Check `lab_member_invitation_code_enabled` setting, validate code format

### Performance Optimization

**Recommendations**:
- Enable HTTP caching for static assets
- Implement connection pooling for database operations
- Optimize password hashing parameters for deployment environment
- Monitor session storage growth and implement cleanup policies

**Section sources**
- [user_store.py:78-90](file://src/sage_faculty_twin/user_store.py#L78-L90)
- [auth.py:169-172](file://src/sage_faculty_twin/auth.py#L169-L172)

## Conclusion

The Integrated Account Management View represents a comprehensive solution for user authentication and session management in the SAGE Faculty Twin platform. The system successfully balances security, usability, and performance through its layered architecture and robust implementation patterns.

Key strengths include:
- **Security**: Industry-standard password hashing and cookie-based authentication
- **Scalability**: Modular design supporting future expansion
- **Usability**: Intuitive frontend interface with responsive design
- **Maintainability**: Clear separation of concerns and comprehensive error handling
- **Testing Infrastructure**: Dedicated support for lab member accounts and invitation code validation

The system provides a solid foundation for user management while maintaining flexibility for future enhancements and integration with additional authentication providers or advanced security features.

**Updated** The addition of dedicated testing infrastructure with lab member accounts enhances the system's capability to support controlled access scenarios and comprehensive testing of authentication flows across different user profiles.