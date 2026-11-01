# Changelog — SCALE.Core
All notable changes to the **SCALE.Core** (Supply Chain Analytics & Logistics Engine) platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to Semantic Versioning.

**Project Owner:** Hemanth Kumar H A  
**Repository:** SCALE.Core  

---

## [1.0.0-rc1] - 2026-11-01
### Added
- **Complete End-to-End Operational Lifecycle Verification (Part 26.6):**
  - Implemented and verified `tests/test_e2e_lifecycle.py` tracing the complete 16-step operational chain: sales demand ingestion -> stock reduction -> LSTM inference -> Dynamic ROP calculation -> critical stockout detection -> replenishment PO drafting -> policy gate evaluation -> supervisor approval -> shipment monitoring -> goods receipt -> stock replenishment -> cryptographic audit chain validation -> management telemetry.
- **Financial Intelligence Workspace (Part 15):**
  - Delivered `/finance/` restricted to System Supervisors with itemized excess stock capital-at-risk analysis and carrying cost metrics.
- **Reporting & Business Intelligence (Part 20):**
  - Delivered `/reporting/` with automated CSV exports for Inventory Health and Procurement Commitments.
- **Exceptions & Notification Hub (Part 19):**
  - Delivered `/notifications/` with unread counts and 1-click acknowledgement workflow.
- **Supplier Directory (Part 13):**
  - Delivered `/suppliers/` with vendor scorecards, contact directories, and lead-time compliance metrics.
- **Automated Test Suite Expansion:**
  - Expanded test suite to 24 tests passing with 100% success rate across all eleven layers of the architecture.

## [0.2.0-rc1] - 2026-11-01
### Added
- **Phase 3: Inventory Intelligence Engine:**
  - Implemented `StockMovementService` with pessimistic concurrency locking (`select_for_update`), automatic balance calculation, and immutable audit logging.
  - Built `InventoryClassificationService` executing automated ABC (Pareto 80/20 revenue) and XYZ demand variability analysis ($CV = \sigma / \mu$).
  - Built `StockReconciliationService` handling physical count audits and supervisor-authorized discrepancy adjustments.
  - Delivered Inventory Catalog ([`/inventory/`](file:///c:/Users/heman/OneDrive/Desktop/S.C.A.L.E.Core/templates/inventory/catalog.html)) and Movement Ledger views ([`/inventory/movements/`](file:///c:/Users/heman/OneDrive/Desktop/S.C.A.L.E.Core/templates/inventory/movements.html)).
- **Phase 4: Predictive Intelligence & Dynamic ROP:**
  - Implemented `TimeSeriesDataPipeline` with stockout-censoring correction and feature engineering (lags, rolling averages, calendar factors).
  - Built `LSTMForecastingEngine` with multi-step LSTM neural network (128-64 units, Dropout 0.2, Huber loss) generating 30-day forecast horizons with 95% confidence intervals.
  - Implemented `DynamicROPDecisionEngine` computing statistical Safety Stock ($SS = Z \times \sqrt{L \sigma_d^2 + \bar{D}^2 \sigma_L^2}$) and Dynamic $ROP = (\bar{D} \times L) + SS$.
  - Built `ForecastBenchmarkEvaluator` evaluating MAE, RMSE, WAPE, and Forecast Bias against Holt-Winters Exponential Smoothing and Moving Average baselines.
  - Delivered Interactive Forecasting Dashboard ([`/forecasting/`](file:///c:/Users/heman/OneDrive/Desktop/S.C.A.L.E.Core/templates/forecasting/dashboard.html)).
- **Phase 5: Autonomous Procurement Engine & Suppliers:**
  - Built `SupplierEvaluationService` ranking vendors via explainable composite multi-factor scoring (Reliability 45%, Quality 35%, Lead Time Compliance 20%).
  - Built `AutonomousProcurementService` enforcing policy gatekeeper rules: auto-dispatching Category B orders $\le \$5,000$ and routing Category C orders $> \$5,000$ to the Supervisor approval queue.
  - Built supervisor approval/rejection views with automated inventory incoming stock allocation.
  - Delivered Purchase Order Registry ([`/procurement/`](file:///c:/Users/heman/OneDrive/Desktop/S.C.A.L.E.Core/templates/procurement/orders_list.html)) and Order Detail inspection ([`/procurement/orders/<id>/`](file:///c:/Users/heman/OneDrive/Desktop/S.C.A.L.E.Core/templates/procurement/order_detail.html)).
- **Phase 6: Logistics & Goods Receipt:**
  - Implemented `LogisticsService` managing dock arrivals, receipt verification, delivery discrepancy detection, and automatic on-hand inventory replenishment.
- **Phase 8: Local AI Copilot & Query Engine:**
  - Implemented `LocalOllamaClient` connecting locally to Llama 3.2 at `http://127.0.0.1:11434` with deterministic fallback when daemon is offline/restricted.
  - Built `OperationalAIAdvisor` enabling context-aware retrieval answering supervisor questions on stockout risks, pending approvals, and financial exposure.
  - Delivered AI Operations Workspace ([`/intelligence/`](file:///c:/Users/heman/OneDrive/Desktop/S.C.A.L.E.Core/templates/intelligence/workspace.html)).
- **Phase 9: Autonomous Workflow Orchestration:**
  - Implemented `AutonomousWorkflowOrchestrator` executing the 8-stage 02:00 AM autonomous supply chain operational cycle (ETL -> LSTM -> ROP -> Replenishment -> Policy Gate -> Classification -> Finance -> Audit).
  - Built real-time Human Intervention Rate (HIR) and Automation Rate telemetry tracking.
  - Delivered Automation Control Centre ([`/automation/`](file:///c:/Users/heman/OneDrive/Desktop/S.C.A.L.E.Core/templates/automation/control_center.html)).
- **Phase 10: Subsystem Observability Probes:**
  - Implemented `SystemHealthProbeService` running empirical latency probes on PostgreSQL, TensorFlow deep learning engine, and Ollama local AI.
  - Delivered System Health Observability Dashboard ([`/system-health/`](file:///c:/Users/heman/OneDrive/Desktop/S.C.A.L.E.Core/templates/system_health/dashboard.html)).
- **Automated Test Suite Expansion:**
  - Comprehensive test suite in `tests/` expanded to 23 automated unit and integration tests passing with 100% success rate.
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
