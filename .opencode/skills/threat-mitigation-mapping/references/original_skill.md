---
name: threat-mitigation-mapping
description: "Map identified threats to appropriate security controls and mitigations. Use when prioritizing security investments, creating remediation plans, or validating control effectiveness. Focuses on STRIDE/DREAD threat outcomes. Cluster: Security (SPLIT)"
---

# Threat Mitigation Mapping

Systematically mapping identified threats (from modeling) to concrete, measurable security controls and mitigation strategies.

## When to Use This Skill

- Creating remediation roadmaps after threat modeling
- Prioritizing security efforts based on risk exposure
- Validating control effectiveness against specific threats
- Developing comprehensive security architectures
- Translating security requirements into implementation tasks

## Threat Modeling Foundation

This skill assumes you have already identified threats using a methodology like STRIDE (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege).

## Core Concepts: Mapping & Prioritization

### 1. Threat $\rightarrow$ Control Mapping
Every high-priority threat must be mapped to at least one control.

| Threat Category | Example Threat | Mitigation Strategy | Specific Control |
|-----------------|----------------|---------------------|------------------|
| Information Disclosure | Sensitive data logged in plaintext | Encryption in transit/at rest | TLS 1.3, AES-256 |
| Tampering          | In-transit data modification | Integrity checks | HMAC, Digital Signatures |
| DoS                | Resource exhaustion | Rate limiting, circuit breakers | Cloud WAF/Load Balancer Config |
| Spoofing           | Impersonation | Strong identity verification | MFA, JWT validation |

### 2. Control Implementation Levels
Controls should be mapped across the stack:

-   **Application Layer:** Code validation, secure library use.
-   **Infrastructure Layer:** Network segmentation, IAM policies.
-   **Process Layer:** Security training, incident response playbooks.

### 3. Risk Scoring
Mitigation effectiveness is assessed by how much it reduces **Residual Risk**.

$$\text{Residual Risk} = \text{Inherent Risk} \times (1 - \text{Control Effectiveness})$$

## Mitigation Strategy Templates

### Template 1: Data In-Transit Protection (Information Disclosure/Tampering)

-   **Threat:** Eavesdropping on API traffic.
-   **Control:** Enforce Transport Layer Security (TLS).
-   **Implementation:**
    1.  Mandate TLS 1.3 end-to-end.
    2.  Pin certificates (if applicable, e.g., for mobile clients).
    3.  Configure HTTP Strict Transport Security (HSTS) headers.

### Template 2: Input Validation for Injection Attacks (Tampering)

-   **Threat:** SQL Injection, Cross-Site Scripting (XSS).
-   **Control:** Strict input validation and parameterized queries.
-   **Implementation:**
    1.  Use parameterized queries/ORMs for all database interactions.
    2.  Sanitize and encode all user-generated content before rendering (HTML context, URL context).

## Best Practices

-   **Principle of Least Privilege:** Controls should enforce the minimum necessary access.
-   **Defense-in-Depth:** Implement overlapping controls (defense in depth).
-   **Auditability:** Ensure control implementation is auditable (logs, configuration verification).

## References

-   [NIST SP 800-53 Catalog](https://csrc.nist.gov/Projects/Risk-Management/framework-security-controls/csrc-catalog-search)
-   [MITRE ATT&CK Framework](https://attack.mitre.org/) (For understanding TTPs)
-   [OWASP ASVS](https://owasp.org/www-project-application-security-verification-standard/)

---

**Remember:** A mitigation is only as good as its implementation. Verify controls rigorously. (Cluster: Security)
