# SCALE.Core — Official System Architecture Specification
**System Name:** Supply Chain Analytics & Logistics Engine (SCALE.Core)  
**Project Owner & Lead Architect:** Hemanth Kumar H A  
**Architecture Style:** Layered Modular Monolith, Local-First, Autonomous & Event-Driven  
**Design Standard:** Enterprise Hybrid Design System (V1.0)  
**Document Status:** Approved & Authoritative  

---

## 1. Architectural Philosophy & Vision

SCALE.Core is designed from first principles as an autonomous enterprise supply chain intelligence engine requiring **ONE human operator** to supervise operations.

Routine operational cycles (data ingestion, stock calculations, demand forecasting, stockout risk detection, supplier scoring, low-risk PO dispatch, tracking, and exception alerts) are executed independently by the platform. The human supervisor retains strategic control, policy authorization, and exception review.

> **Operational Directive:** "One human supervises. SCALE.Core operates."  
> **Engineering Creed:** Precision in information. Restraint in appearance. Intelligence in execution.

```
+-------------------------------------------------------------------------------+
|                             HUMAN SUPERVISOR                                  |
|         Strategic Policies | High-Risk Approvals | Exception Resolution       |
+-------------------------------------------------------------------------------+
                                      ▲
                                      │ REST / Enterprise Hybrid UI / Webhooks
                                      ▼
+-------------------------------------------------------------------------------+
|                           SCALE.Core APPLICATION                              |
|                                                                               |
|  +--------------------+  +---------------------+  +------------------------+  |
|  | Presentation Layer |  | Auth & Access (RBAC)|  | Application Services   |  |
|  +--------------------+  +---------------------+  +------------------------+  |
|                                                                               |
|  +--------------------+  +---------------------+  +------------------------+  |
|  | Decision Engine    |  | Predictive ML/LSTM  |  | Local AI (Ollama/Llama)|  |
|  +--------------------+  +---------------------+  +------------------------+  |
|                                                                               |
|  +-------------------------------------------------------------------------+  |
|  |              Autonomous Workflow Orchestrator (State Machine)           |  |
|  +-------------------------------------------------------------------------+  |
|                                                                               |
|  +--------------------+  +---------------------+  +------------------------+  |
|  | Data Access (ORM)  |  | Immutable Audit     |  | System Health & Metrics|  |
|  +--------------------+  +---------------------+  +------------------------+  |
+-------------------------------------------------------------------------------+
         ▲                                                ▲
         │                                                │
         ▼                                                ▼
+--------------------+                           +------------------------------+
|   PostgreSQL 16    |                           |      Celery Beat & Worker    |
| (Relational/Audit) |                           |       (Redis Message Bus)    |
+--------------------+                           +------------------------------+
```

---

## 2. Technology Stack & Component Specifications

### 2.1 Backend Core
- **Language:** Python 3.11.9
- **Web Framework:** Django 5.2.x (Modular Monolith)
- **API Framework:** Django REST Framework (DRF 3.15.x)
- **Database Engine:** PostgreSQL 16 (with SQLite 3.45 fallback for local verification)
- **Object-Relational Mapping:** Django ORM with strict indexing, constraints, and transactions.

### 2.2 Deep Learning & Machine Learning
- **Deep Learning Framework:** TensorFlow 2.21.0 / Keras 3.15.1
- **Forecasting Model:** Multi-layer LSTM (60-day sequence input -> 30-day forecast horizon)
- **Classical Benchmarks:** Scikit-learn 1.9.1, Exponential Smoothing, Moving Average, XGBoost
- **Data Preprocessing & Math:** Pandas 3.1.0, NumPy 2.4.6, Huber Loss, Rolling-origin validation.

### 2.3 Local Generative AI
- **LLM Engine:** Ollama (v0.6+) hosting Meta Llama 3.2 (3B / 8B quantized)
- **Endpoint:** `http://127.0.0.1:11434/api/generate` (strictly local loopback, zero external egress)
- **Role Boundary:** Narrative explanations, PO justification drafting, and anomaly analysis. Deterministic calculations (ROP, quantities, costs) are strictly computed by the Python Decision Engine.

### 2.4 Asynchronous Task & Event Processing
- **Task Worker:** Celery
- **Message Broker & Result Store:** Redis
- **Task Scheduler:** Celery Beat (02:00 AM autonomous scheduled pipeline + event-driven workers)
- **Resilience:** Idempotency keys, transactional outbox pattern, exponential backoff, dead-letter queues.

### 2.5 Frontend & Visualization
- **Markup & Layout:** HTML5 Semantic Structure, Tailwind CSS (Design Tokens V1.0)
- **Interactivity:** Vanilla ECMAScript (ES2022+), zero frontend framework bloat
- **Visual Analytics:** Chart.js (configured with enterprise colorway and muted styling).

---

## 3. Eleven-Layer Architectural Model

In compliance with Part 4.2 of the Master Specification, SCALE.Core implements eleven strictly separated layers:

1. **Presentation Layer:** Django templates, component partials, Tailwind CSS tokens, Chart.js views.
2. **Authentication and Authorization Layer:** Custom `SCALEUser`, role-based permission policies (Manager vs Employee), session management, CSRF defense.
3. **Application Service Layer:** Orchestrates multi-domain operations, coordinates workflows, and separates business logic from views.
4. **Business Logic Layer:** Implements core supply chain calculations, reorder policies, stock adjustments, and goods receipt logic.
5. **Supply Chain Decision Engine:** Deterministic calculation of Safety Stock, Reorder Point (ROP), and Order-Up-To quantities with lead-time variability.
6. **Machine Learning Layer:** Feature engineering, historical demand ETL, LSTM model lifecycle, rolling-origin cross-validation, and metrics (MAE, RMSE, WAPE, Bias).
7. **Local AI Intelligence Layer:** Local Ollama interface, structured JSON validation, procurement justification generation, and natural-language queries.
8. **Workflow Orchestration Layer:** Autonomous state machine managing Category A, B, and C operations, retries, approval suspension, and execution logging.
9. **Data Access Layer:** Django ORM, query optimization (`select_related`, `prefetch_related`), database constraints, foreign keys, and indexes.
10. **Audit and Governance Layer:** Append-only cryptographic ledger (`AuditLog`), hash chaining (`SHA-256`), state before/after diffing, and tamper detection.
11. **Infrastructure and Monitoring Layer:** Real-time health probes for PostgreSQL, Redis, Celery, Ollama, TensorFlow, and application uptime.

---

## 4. Django Application Modular Organization

The project is structured into cohesive, decoupled Django applications:

```
SCALE.Core/
├── scale_core/                 # Project configuration root (settings, wsgi, asgi, urls, celery)
├── apps/
│   ├── core/                  # Base utilities, design system tokens, common view mixins
│   ├── accounts/              # Custom User (SCALEUser), roles, permissions, auth views
│   ├── inventory/             # Product master, warehouses, stock movements, ABC/XYZ classification
│   ├── sales/                 # Historical sales transactions (DailySalesLog), demand records
│   ├── forecasting/           # LSTM model, feature extraction, benchmarks, inference pipeline
│   ├── procurement/           # Reorder logic, PO lifecycle, dispatch policies, approval queue
│   ├── suppliers/             # Supplier directory, lead-time tracking, multi-factor scoring
│   ├── logistics/             # Shipment tracking, carrier performance, delivery discrepancies
│   ├── finance/               # Inventory valuation, excess inventory capital at risk, cost tracking
│   ├── intelligence/          # Local Ollama / Llama 3.2 integration, structured prompt engine
│   ├── automation/            # Autonomous Workflow Orchestrator, state machine, job queue
│   ├── audit/                 # Append-only cryptographic audit ledger, tamper verification
│   ├── notifications/         # Centralized alert hub, priority escalation, deduplication
│   ├── system_health/         # Subsystem monitoring, heartbeat probes, telemetry
│   └── reporting/             # Automated PDF/CSV/XLSX operational report generators
├── static/                    # CSS, JS, Chart.js bundles, brand assets
├── templates/                 # Global layout, navigation, modals, and module views
├── tests/                     # Unit, integration, security, and end-to-end test suites
└── scripts/                   # Database seeds, backup scripts, Linux systemd unit definitions
```

---

## 5. Autonomous Operations State Machine

Every autonomous operation runs under the Workflow Orchestrator with unambiguous state transitions:

```
  [EVENT / SCHEDULE]
          │
          ▼
      [QUEUED] ──────────────────────────┐
          │                              │
          ▼                              ▼
      [RUNNING] ─────────────────► [CANCELLED]
       │     │
       │     ├───────────────────────────┐
       │     ▼                           ▼
       │  [FAILED] ──► [RETRYING]   [AWAITING_APPROVAL] (Category C / Policy Block)
       │                  │              │
       │                  └───► [RUNNING]├──► [COMPLETED] (Approved)
       │                                 └──► [CANCELLED] (Rejected)
       ▼
  [COMPLETED] ──► (Trigger downstream workflow / Record Audit)
       │
       ▼
  [RECONCILIATION_REQUIRED] (Uncertain external outcome / goods discrepancy)
```

### Execution Categories:
- **Category A (Fully Autonomous):** DailySalesLog ETL, LSTM demand inference, ROP calculation, stockout risk scoring, supplier score recalculation, routine reporting.
- **Category B (Policy-Controlled Autonomous):** PO auto-dispatch when supplier is approved, unit price <= contract price, and total value <= $5,000 threshold.
- **Category C (Human Intervention Required):** POs exceeding financial threshold, supplier quote anomalies > 15% variance, stock count discrepancies > 5%, model accuracy degradation (WAPE > 30%).

---

## 6. Security & Data Governance Architecture
1. **Zero External Data Egress:** All AI models run on local silicon via Ollama. No telemetry is transmitted to third-party clouds.
2. **Deterministic Primacy:** Machine learning and generative AI provide advice and predictions; deterministic business logic validates all quantities, constraints, and financial actions.
3. **Cryptographic Audit Ledger:** Every state-modifying action records `actor`, `event_type`, `before_state`, `after_state`, and `hash_chain`.
4. **Role Isolation:** Strict separation between Manager (Supervisor) and Employee (Operator) at view, API, queryset, and UI levels.
