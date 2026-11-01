# SCALE.Core — Security Architecture & Threat Assessment
**Product:** Supply Chain Analytics & Logistics Engine (SCALE.Core)  
**Security Standard:** OWASP Top 10 + Supply Chain Autonomous Threat Model  
**Lead Cybersecurity Architect:** Hemanth Kumar H A  
**Document Status:** Enterprise Security Policy  

---

## 1. Security Philosophy & Threat Model

SCALE.Core operates on a **zero-trust, local-first, air-gapped ready** security architecture. As an enterprise supply chain system with autonomous execution capabilities, security cannot be treated as an afterthought or confined to simple password hashing.

### Primary Threat Vectors:
1. **Privilege Escalation:** An operational employee attempting to access financial margins, procurement budgets, or execute unauthorized purchase orders.
2. **Autonomous Policy Tampering:** Unauthorized modification of auto-dispatch thresholds or supplier pricing rules.
3. **LLM Hallucination / Injection Attack:** Manipulation of generative AI prompts to alter order quantities, prices, or approval states.
4. **Audit Record Repudiation:** Altering or deleting historical logs to conceal inventory shrinkage or unauthorized procurement.
5. **Data Exfiltration:** Transmission of proprietary supply chain data to public clouds.

---

## 2. STRIDE Threat Assessment & Mitigation Matrix

| Threat (STRIDE) | Attack Scenario in Supply Chain | Technical Mitigation in SCALE.Core | Defense Layer |
|---|---|---|---|
| **Spoofing** | Attacker impersonates Manager to dispatch unauthorized orders | Argon2/PBKDF2 password hashing, secure session invalidation, IP tracking, mandatory re-authentication on policy updates | Auth & Middleware |
| **Tampering** | Employee alters physical count records or audit logs | Append-only SHA-256 hash-chained `AuditLog`, PostgreSQL level triggers blocking UPDATE/DELETE, strict state diffing | Database & Audit |
| **Repudiation** | Operator denies placing or approving a purchase order | Every action logs immutable UUID, actor ID, IP address, timestamp, and previous hash; non-repudiable ledger | Audit Engine |
| **Information Disclosure** | Employee views supplier profit margins or company financial risk | Field-level and queryset-level RBAC; Employee serializer explicitly excludes cost and financial metrics | API / Serializers |
| **Denial of Service** | Flooding login endpoint or triggering massive LSTM inferences | Rate-limiting middleware (IP-based throttling), asynchronous background execution for all ML workloads | Celery / Middleware |
| **Elevation of Privilege** | Employee modifies HTML form to toggle `is_superuser` or approval | Explicit Django permission policies; backend model-level validation; server-side role verification | Application Core |

---

## 3. Defense-in-Depth Implementation

### 3.1 Role-Based Access Control (RBAC) Architecture
```
+------------------------------------------------------------------------+
|                            SCALEUser                                   |
+-----------------------------------+------------------------------------+
                                    │
          ┌─────────────────────────┴─────────────────────────┐
          ▼                                                   ▼
+───────────────────────────+               +───────────────────────────+
|     ROLE: MANAGER         |               |     ROLE: EMPLOYEE        |
| - Full Financial Vision   |               | - Operational Tasks Only  |
| - AI Copilot & Query      |               | - Stock Receipt Input     |
| - Strategic Policies      |               | - Physical Count Input    |
| - PO Approvals (Cat C)    |               | - View Assigned WH Stock  |
| - Audit Ledger Inspector  |               | - Zero Financial Access   |
| - System Health & Metrics |               | - Zero AI Policy Control  |
+---------------------------+               +---------------------------+
```

### 3.2 Generative AI Guardrails & Hallucination Containment
In strict adherence to **Part 11.3 and Part 30 (Rule 9)**:
- **No Direct Database Writes:** The Ollama / Llama 3.2 model has zero direct write access to database models, raw SQL execution, or ORM interfaces.
- **Deterministic Boundary:** All order quantities, reorder points, costs, and discounts are computed strictly by deterministic Python algorithms (`ROP = D_avg * L + SS`).
- **Structured Schema Validation:** Any AI-suggested recommendation must pass strict Pydantic JSON schema validation. If the LLM generates an invalid SKU, negative quantity, or unsupported price, the recommendation is rejected automatically and flagged for review.

### 3.3 Cryptographic Audit Ledger (Tamper Resistance)
The `AuditLog` table implements a cryptographic blockchain-like mechanism:
$$\text{Current Hash} = \text{SHA256}(\text{Previous Hash} \parallel \text{Actor} \parallel \text{Event} \parallel \text{Timestamp} \parallel \text{State After})$$

- If an attacker with direct database access alters any past row, the entire hash chain downstream becomes mathematically invalid.
- An automated verification task periodically calculates and validates the chain head against signed checkpoints.

### 3.4 Local-First Sovereignty (Air-Gap Readiness)
- All inference runs locally at `http://127.0.0.1:11434` via Ollama.
- No third-party cloud analytics, telemetry transmitters, or tracking pixels are embedded.
- Static assets (Tailwind, Chart.js, Inter font) are bundled locally within `static/`, enabling full offline execution without public internet access.
