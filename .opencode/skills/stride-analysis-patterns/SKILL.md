---
name: stride-analysis-patterns
description: "Apply STRIDE methodology to systematically identify threats. Use when analyzing system security, conducting threat modeling sessions, or creating security documentation. Identifies threats against the six STRIDE categories: Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, and Elevation of Privilege. Cluster: Security (SPLIT)"
---

# STRIDE Threat Modeling Methodology

Systematically identifying potential security threats in a design or application using the Microsoft STRIDE framework.

## When to Use This Skill

- Conducting threat modeling sessions on new features or architecture
- Analyzing trust boundaries and data flows
- Reviewing requirements for security gaps
- Documenting identified security risks

## STRIDE Categories

STRIDE provides a structured way to categorize threats:

| Category | Description | Mitigation Focus |
|----------|-------------|------------------|
| **S**poofing | Pretending to be someone/something else | Authentication, Identity Verification |
| **T**ampering | Unauthorized modification of data | Integrity Checks, Input Validation |
| **R**epudiation | Denying an action was performed | Non-repudiation, Logging, Audit Trails |
| **I**nformation Disclosure | Exposing data to unauthorized parties | Confidentiality, Encryption, Access Control |
| **D**enial of Service (DoS) | Preventing legitimate users from accessing resources | Availability, Rate Limiting, Resource Management |
| **E**levation of Privilege | Gaining unauthorized access/permissions | Least Privilege, Authorization Checks |

## Threat Modeling Workflow

### Step 1: Define Scope
Identify system boundaries, assets, and trust levels.

### Step 2: Decompose Application
Diagram data flows, trust boundaries, and entry points (Use C4 Model or Excalidraw).

### Step 3: Threat Identification (Applying STRIDE)
For every data flow/entry point, brainstorm potential threats for each of the six STRIDE categories.

**Example for an API Endpoint:**
1.  **Spoofing:** Can an attacker impersonate another user? (Mitigation: Strong JWT validation).
2.  **Tampering:** Can an attacker change the request body mid-flight? (Mitigation: HTTPS/HMAC).
3.  **Information Disclosure:** Does the response leak PII? (Mitigation: Data masking).

### Step 4: Risk Analysis & Mitigation
Rank identified threats by severity (e.g., Likelihood $\times$ Impact). Map each high-risk threat to specific security controls (see `threat-mitigation-mapping` skill).

## STRIDE Element Mapping

-   **Data in Transit**: Tampering, Information Disclosure
-   **Data at Rest**: Tampering, Information Disclosure
-   **Authentication**: Spoofing, Repudiation
-   **Authorization**: Elevation of Privilege
-   **System Resources**: Denial of Service

## Best Practices

-   **STRIDE + DREAD/ASVS:** Combine STRIDE for *what* the threat is with DREAD (Damage, Reproducibility, Exploitability, Affected Users, Discoverability) for *risk score*.
-   **Iterate:** Threat modeling is not a one-time activity; re-run on significant architectural changes.

## References

-   [Microsoft STRIDE Threat Model Overview](references/microsoft-overview.html)
-   [OWASP Threat Modeling Cheat Sheet](references/owasp-cheatsheet.html)

---

**Remember:** STRIDE helps ensure you cover all major security categories during design review. (Cluster: Security)
