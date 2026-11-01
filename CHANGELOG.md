# Changelog — SCALE.Core
All notable changes to the **SCALE.Core** (Supply Chain Analytics & Logistics Engine) platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to Semantic Versioning.

**Project Owner:** Hemanth Kumar H A  
**Repository:** SCALE.Core  

---

## [0.1.0-alpha.1] - 2026-11-01
### Added
- **Phase 1: Foundation Architecture Delivery:**
  - Designed and deployed custom user model `SCALEUser` with two-tier role authorization (`MANAGER` vs `EMPLOYEE`).
  - Implemented session security middleware with IP tracking and brute-force defenses.
  - Implemented 15 modular Django applications covering the complete supply chain lifecycle.
  - Applied relational schemas across 10 core domains with check constraints, foreign key protections, and decimal precision.
  - Implemented append-only cryptographic Audit Ledger with SHA-256 hash chaining and tamper detection service.
  - Created deterministic foundation data seeding command (`seed_foundation`).
- **Phase 2: Enterprise Hybrid Design System (V1.0) Delivery:**
  - Implemented centralized design tokens in `static/css/enterprise.css` adhering strictly to official palette and Inter typography.
  - Developed unified application shell with responsive 248px sidebar, 60px header, and breadcrumb navigation.
  - Built flagship Operational Command Center dashboard (`templates/overview.html`) featuring KPI metrics, critical stockout risk analysis, Chart.js multi-step forecasting, and Category C human approval queue.
  - Automated test suite `tests/test_foundation.py` passing 5/5 tests covering RBAC, inventory calculations, audit immutability, hash chaining, and view rendering.

---

## [0.1.0-alpha.0] - 2026-11-01
### Added
- **Phase 0 Baseline Execution:**
  - Initialized official Git version control repository.
  - Implemented comprehensive `.gitignore` protecting binary model weights, environment secrets, and bytecode.
  - Completed environment and runtime audit verifying Python 3.11.9, Django 5.2.5, DRF 3.15.2, TensorFlow 2.21.0, Keras 3.15.1, Scikit-learn 1.9.1, Pandas 3.1.0, NumPy 2.4.6, and Ollama 0.6.1.
  - Built isolated virtual environment (`.\venv`) with system-wide deep learning framework bridging enabled (`include-system-site-packages = true`).
  - Authored official architectural and governance documentation suite:
    - `CODEBASE_AUDIT.md`: System baseline report and functionality audit.
    - `SYSTEM_ARCHITECTURE.md`: Official 11-layer architecture, modular monolith specification, and autonomous state machine.
    - `FEATURE_IMPLEMENTATION_MATRIX.md`: End-to-end 40-feature delivery tracking matrix with Category A/B/C breakdown.
    - `DATABASE_SCHEMA.md`: Third-normal-form relational schema specification for PostgreSQL 16 (and SQLite3 dev) across 10 core domains.
    - `API_DOCUMENTATION.md`: REST API contract specification with standard JSON envelopes and RBAC rules.
    - `SECURITY_ASSESSMENT.md`: STRIDE threat model, privilege escalation defense, and cryptographic audit specifications.
    - `DEPLOYMENT_GUIDE.md`: Linux on-premise systemd services, Nginx reverse proxy, and disaster recovery procedures.
    - `CHANGELOG.md`: Transparent lifecycle audit tracking.
