---
name: security-requirement-extraction
description: "Derive security requirements from threat models and business context. Use when translating threats into actionable requirements, creating security user stories, or building security test cases. Focuses on translating STRIDE/DREAD/Attack Trees into verifiable requirements. Cluster: Security (SPLIT)"
---

# Deriving Security Requirements

Translating abstract security threats (from modeling) into concrete, verifiable, and actionable engineering requirements.

## When to Use This Skill

- Converting threat modeling output into actionable tasks
- Defining Acceptance Criteria for security features
- Creating security user stories for the backlog
- Establishing verifiable test cases for security controls
- Ensuring compliance mapping links directly to features

## Core Concepts: Requirement Types

Requirements must be **SMART** (Specific, Measurable, Achievable, Relevant, Time-bound) where possible.

| Source Artifact | Output Requirement Type | Focus |
|-----------------|-------------------------|-------|
| Threat Model (STRIDE) | Functional Security Requirement | What the system MUST DO (e.g., "The system shall encrypt all PII at rest") |
| Risk Score (DREAD) | Non-Functional Security Requirement (Quality Attribute) | How well it must do it (e.g., "Authentication latency must be < 500ms") |
| Compliance (PCI/GDPR) | Policy Requirement | Adherence to external standard (e.g., "Must use TLS 1.2+") |

## Key Patterns

### Pattern 1: Translating STRIDE to Requirement (Cluster: Security)

| STRIDE Threat | Threat Scenario Example | Derived Requirement | Verification Method |
|---------------|-------------------------|---------------------|---------------------|
| **Spoofing**  | Attacker impersonates admin via stolen credentials. | The system SHALL enforce Multi-Factor Authentication (MFA) for all administrative access points. | Security Audit / Manual Test |
| **Tampering** | User modifies order total in transit. | All API requests SHALL use HMAC signing validated server-side before processing. | Integration Test |
| **Info Disclosure**| Database error reveals stack trace with internal paths. | The API SHALL return only generic error codes (4xx/500) and sanitize all logs. | DAST/Pen Test |

### Pattern 2: Security User Story Format

Format security requirements as actionable user stories, often tied to a specific actor.

```
AS A [System Role/Actor],
I WANT [The Feature/Control],
SO THAT [The Security Benefit/Risk Reduction].
```

**Example:**
*AS an Admin User, I WANT to be forced to use MFA during login, SO THAT credential compromise does not lead to system-wide access.*

### Pattern 3: Linking Compliance to Code

Map external standards (e.g., PCI DSS) to specific technical requirements.

-   **PCI Requirement 3.4:** "Do not store sensitive authentication data after authorization is complete."
-   **Technical Requirement:** The `auth_service` SHALL purge session tokens and passwords from memory within 5 minutes of successful authentication.

## Best Practices

-   **Traceability:** Maintain a link between the threat, the requirement, and the test case.
-   **Verifiability:** Requirements must be testable (unit, integration, or audit).
-   **Security Tests:** Ensure every security requirement has a corresponding security test (unit or E2E).

## References

-   [OWASP ASVS](references/owasp-asvs.html) - For requirement definition.
-   [NIST SP 800-53 Catalog](references/nist-catalog.html) - For control mappings.
-   [Security Testing Guide](references/security-testing-guide.html)

---

**Remember:** If a requirement is not verifiable by a test or audit, it is not a requirement. (Cluster: Security)
