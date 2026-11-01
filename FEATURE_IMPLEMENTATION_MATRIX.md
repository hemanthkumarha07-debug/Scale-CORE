# SCALE.Core — Feature Implementation Matrix
**Product:** Supply Chain Analytics & Logistics Engine (SCALE.Core)  
**Project Owner:** Hemanth Kumar H A  
**Document Status:** Live Implementation Tracker  
**Last Updated:** Phase 0 Baseline  

---

## 1. Overview & Verification Standard

In strict compliance with **Part 3.4 and Part 30 (Rule 21)** of the Master Specification, no feature shall be marked as **Completed** or **Verified** merely because an interface, stub, or mockup exists.

### Status Definitions:
- **PLANNED:** Fully specified in architecture, schema ready, awaiting phase execution.
- **IN_PROGRESS:** Active engineering in the current development cycle.
- **TESTED:** Implemented, covered by automated unit/integration tests, verified in database.
- **VERIFIED:** End-to-end validated with UI, API, database constraints, and audit logging.

---

## 2. Master Feature Matrix

| ID | Module / Capability | Spec Part | Target Phase | Category | Core Service / Handler | API / View Route | Security Policy | Status |
|---|---|---|---|---|---|---|---|---|
| **F001** | Codebase Inspection & Baseline | Part 3 | Phase 0 | A | Architecture Audit Engine | N/A (CLI / Docs) | System Administrator | **VERIFIED** |
| **F002** | Git VCS Checkpoint & .gitignore | Part 3 | Phase 0 | A | Git Version Control | N/A | System Administrator | **VERIFIED** |
| **F003** | Architectural Documentation Suite | Part 3.4 | Phase 0 | A | Documentation System | Root Markdown Docs | Public / Developer | **IN_PROGRESS** |
| **F004** | Python 3.11 + Django 5 + TF Bridge | Part 4 | Phase 0 | A | Runtime Environment | `manage.py check` | System Administrator | **VERIFIED** |
| **F005** | Custom User (`SCALEUser`) & Roles | Part 6 | Phase 1 | C | `accounts.services.AuthService` | `/accounts/login/`, `/api/auth/` | Session + Strict RBAC | **PLANNED** |
| **F006** | Session Security & Brute-Force Shield | Part 6.3 | Phase 1 | A | `accounts.middleware.SecurityMiddleware` | Global Middleware | Auto-throttle IP | **PLANNED** |
| **F007** | Enterprise Hybrid Shell & Design Tokens | Part 17 | Phase 2 | N/A | `core.context_processors.theme` | Global Templates | Authenticated | **PLANNED** |
| **F008** | Global Sidebar & Responsive Header | Part 17.4 | Phase 2 | N/A | `templates/components/shell.html` | All Authenticated Views | Role-adaptive UI | **PLANNED** |
| **F009** | Product Master & Warehouse Inventory | Part 8.1 | Phase 3 | A | `inventory.services.StockService` | `/inventory/products/`, `/api/inventory/` | Manager Full, Emp Read | **PLANNED** |
| **F010** | Stock Movement Ledger & Availability | Part 8.2 | Phase 3 | A | `inventory.services.MovementService` | `/inventory/movements/` | Manager Full, Emp Create | **PLANNED** |
| **F011** | ABC/XYZ Demand Variability Analysis | Part 8.4 | Phase 3 | A | `inventory.services.ClassificationService`| `/inventory/classification/`| Manager Only | **PLANNED** |
| **F012** | Physical Count Reconciliation Workflow| Part 8.5 | Phase 3 | C | `inventory.services.ReconciliationService`| `/inventory/reconcile/`| Emp Submit, Mgr Approve | **PLANNED** |
| **F013** | Time-Series Sales ETL & Censoring Fix | Part 9.1 | Phase 4 | A | `forecasting.services.DataPipeline` | Celery Background Job | System Only | **PLANNED** |
| **F014** | Multi-step LSTM Forecaster (30-day) | Part 9.3 | Phase 4 | A | `forecasting.services.LSTMForecaster` | `/forecasting/models/` | Manager View/Trigger | **PLANNED** |
| **F015** | Benchmark Models (MA, ExpSmooth, XGB) | Part 9.5 | Phase 4 | A | `forecasting.services.BenchmarkService` | `/forecasting/benchmark/` | Manager View | **PLANNED** |
| **F016** | Rolling-Origin Cross-Validation Engine| Part 9.5 | Phase 4 | A | `forecasting.services.Evaluator` | `/forecasting/accuracy/` | Manager View | **PLANNED** |
| **F017** | Dynamic ROP & Safety Stock Formula | Part 10.1 | Phase 4 | A | `procurement.services.ROPService` | `/procurement/rop-engine/` | Manager View/Edit | **PLANNED** |
| **F018** | Stockout Risk & Urgency Scoring | Part 10.4 | Phase 4 | A | `procurement.services.RiskService` | `/procurement/risks/` | Manager Dashboard | **PLANNED** |
| **F019** | Supplier Directory & Contract Terms | Part 13 | Phase 5 | B | `suppliers.services.SupplierService` | `/suppliers/` | Manager Full, Emp Read | **PLANNED** |
| **F020** | Multi-Factor Supplier Performance Score| Part 12.2 | Phase 5 | A | `suppliers.services.ScoringService` | `/suppliers/scores/` | Manager View | **PLANNED** |
| **F021** | 15-Stage Procurement Lifecycle Engine | Part 12.1 | Phase 5 | B/C | `procurement.services.POService` | `/procurement/orders/` | Manager Full | **PLANNED** |
| **F022** | Automated PO Dispatch Policy Gate | Part 12.3 | Phase 5 | B | `procurement.services.DispatchGate` | Automated Workflow | System / Manager Policy | **PLANNED** |
| **F023** | Manager Approval Queue & Drawer | Part 12.3 | Phase 5 | C | `procurement.views.ApprovalView` | `/procurement/approvals/` | Manager Only | **PLANNED** |
| **F024** | Shipment Lifecycle & Discrepancy Alert | Part 14 | Phase 6 | A/B | `logistics.services.ShipmentService` | `/logistics/shipments/` | Manager Full, Emp Update| **PLANNED** |
| **F025** | Goods Receipt Verification Workflow | Part 14.2 | Phase 6 | B | `logistics.services.ReceiptService` | `/logistics/receipts/` | Emp Verify, Mgr Final | **PLANNED** |
| **F026** | Inventory Valuation & Holding Cost | Part 15.1 | Phase 7 | A | `finance.services.ValuationService` | `/finance/valuation/` | Manager Only (Restricted) | **PLANNED** |
| **F027** | Excess Inventory & Capital at Risk | Part 15.2 | Phase 7 | A | `finance.services.CapitalRiskService` | `/finance/capital-at-risk/`| Manager Only (Restricted) | **PLANNED** |
| **F028** | Local Ollama + Llama 3.2 Connector | Part 11.1 | Phase 8 | A | `intelligence.services.OllamaClient` | `http://127.0.0.1:11434` | System Internal | **PLANNED** |
| **F029** | Deterministic AI Justification Drafter | Part 11.5 | Phase 8 | B | `intelligence.services.CopilotService` | `/intelligence/copilot/` | Manager Only | **PLANNED** |
| **F030** | Context-Aware Operational Query Engine | Part 18 | Phase 8 | A | `intelligence.services.QueryEngine` | `/intelligence/ask/` | Manager Only | **PLANNED** |
| **F031** | Autonomous Workflow Orchestrator | Part 5 | Phase 9 | A | `automation.services.Orchestrator` | `/automation/workflows/` | Manager Control | **PLANNED** |
| **F032** | Human Intervention Rate (HIR) Telemetry| Part 16.3 | Phase 9 | A | `automation.services.MetricsService` | `/automation/control-center/` | Manager Dashboard | **PLANNED** |
| **F033** | Scheduled 02:00 AM Autonomous Pipeline | Part 22 | Phase 9 | A | `automation.tasks.NightlyPipeline` | Celery Beat Daily Job | System Engine | **PLANNED** |
| **F034** | Append-Only Cryptographic Audit Ledger | Part 7 | Phase 10 | A | `audit.services.AuditService` | `/audit/ledger/` | Manager Only (Immutable) | **PLANNED** |
| **F035** | Audit Hash-Chain Tamper Detection | Part 7.3 | Phase 10 | A | `audit.services.TamperDetector` | `/audit/verify-integrity/` | Manager Only | **PLANNED** |
| **F036** | Centralized Notification & Deduplication| Part 19 | Phase 10 | A | `notifications.services.AlertService` | `/notifications/hub/` | Authenticated | **PLANNED** |
| **F037** | System Health Probes (DB, Celery, AI) | Part 21 | Phase 10 | A | `system_health.services.ProbeService` | `/system-health/` | Manager Only | **PLANNED** |
| **F038** | Automated PDF / CSV / XLSX Reporting | Part 20 | Phase 10 | A | `reporting.services.ReportService` | `/reporting/export/` | Manager Only | **PLANNED** |
| **F039** | End-to-End Operational Lifecycle Tests | Part 26.6 | Phase 11 | N/A | `tests.e2e.test_lifecycle` | Pytest / Django Test | Developer / CI | **PLANNED** |
| **F040** | Linux Systemd Services & Deployment | Part 24 | Phase 11 | N/A | Systemd Units + Nginx Conf | Linux Host System | DevOps / Operator | **PLANNED** |

---

## 3. Autonomous Execution Breakdown

### Category A: Fully Autonomous (Zero Human Overhead)
- Nightly historical sales extraction and missing data interpolation.
- Feature engineering (lagged variables, rolling standard deviations, day-of-week).
- LSTM demand inference for 30-day forecast horizon.
- Dynamic Reorder Point and Safety Stock calculation based on supplier lead-time variance.
- Stockout risk scoring and expected depletion horizon calculation.
- Automated supplier reliability and quality scoring.
- Inventory holding cost and excess valuation computation.
- Workflow health checks, idempotency verification, and scheduled report compiling.

### Category B: Policy-Controlled Autonomous (Authorized Workflows)
- Purchase order auto-generation when SKU projected inventory drops below ROP.
- Purchase order auto-dispatch when:
  1. Supplier is active and contract is valid.
  2. Total PO value <= $5,000 (configurable policy threshold).
  3. Quoted price <= approved contracted price.
  4. Available procurement budget is verified.
- Automated delivery status transition based on verified tracking events.
- Routine reconciliation when goods receipt variance == 0.

### Category C: Human Intervention Required (Supervisor Gateway)
- Purchase orders exceeding $5,000 threshold.
- Supplier quotations with > 15% unit price variance.
- Physical stock count discrepancies exceeding 5% or $1,000 value.
- Supplier disputes or late delivery exception handling.
- Machine learning model retraining trigger when rolling WAPE exceeds 30%.
- Policy modifications (service level Z-factor, budget ceilings, auto-dispatch limits).
