# SCALE.Core — REST API Documentation (v1)
**Product:** Supply Chain Analytics & Logistics Engine (SCALE.Core)  
**Standard:** OpenAPI 3.0 Compatible REST / JSON  
**Project Owner:** Hemanth Kumar H A  
**Document Status:** Production Reference Specification  

---

## 1. API Architecture & Standards

All SCALE.Core API endpoints conform to the following specifications:
- **Base URI:** `/api/v1/`
- **Content-Type:** `application/json; charset=utf-8`
- **Authentication:** Django Session Auth or `Authorization: Token <token>`
- **Security:** CSRF protection mandatory on mutating requests (`POST`, `PUT`, `PATCH`, `DELETE`).
- **Response Format:** Uniform JSON envelope.
- **Audit Logging:** Every mutating request creates an immutable `AuditLog` entry.

### Standard Response Envelope
```json
{
  "status": "success",
  "data": { ... },
  "metadata": {
    "timestamp": "2026-11-01T10:45:00Z",
    "request_id": "req-9a8b7c6d",
    "execution_time_ms": 14.2
  }
}
```

### Standard Error Envelope
```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "Field 'quantity' must be greater than zero.",
    "details": {
      "quantity": ["Ensure this value is greater than or equal to 1.00."]
    }
  },
  "metadata": {
    "timestamp": "2026-11-01T10:45:00Z",
    "request_id": "req-9a8b7c6d"
  }
}
```

---

## 2. Authentication & Authorization Endpoints (`/api/v1/auth/`)

### 2.1 User Login
- **Endpoint:** `POST /api/v1/auth/login/`
- **Access:** Public (Rate-limited: 5 attempts / min)
- **Request Body:**
  ```json
  {
    "username": "hemanth.supervisor",
    "password": "SecurePassword123!"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "status": "success",
    "data": {
      "user_id": "8b087095-fb07-4e3b-9a41-2b028df13b19",
      "username": "hemanth.supervisor",
      "role": "MANAGER",
      "department": "Operations",
      "token": "4a71c89f..."
    }
  }
  ```

### 2.2 Current User Profile
- **Endpoint:** `GET /api/v1/auth/me/`
- **Access:** Authenticated (Manager or Employee)

---

## 3. Inventory Intelligence Endpoints (`/api/v1/inventory/`)

### 3.1 List Products with Stock Telemetry
- **Endpoint:** `GET /api/v1/inventory/products/`
- **Access:** Manager (Full data) | Employee (Operational data, cost hidden)
- **Query Parameters:** `category`, `abc_class`, `xyz_class`, `status`, `search`, `page`, `page_size`
- **Response (200 OK):**
  ```json
  {
    "status": "success",
    "data": [
      {
        "id": "1d8f7a93-...",
        "sku": "SKU-ELEC-4091",
        "name": "Microcontroller Unit MCU-32",
        "category": "Electronics",
        "unit_of_measure": "UNIT",
        "unit_cost": "24.5000",
        "on_hand_stock": "450.00",
        "reserved_stock": "50.00",
        "available_stock": "400.00",
        "incoming_stock": "200.00",
        "reorder_point": "380.00",
        "safety_stock": "120.00",
        "abc_class": "A",
        "xyz_class": "X",
        "stockout_risk_days": 18.5
      }
    ]
  }
  ```

### 3.2 Record Stock Movement
- **Endpoint:** `POST /api/v1/inventory/movements/`
- **Access:** Authenticated (Manager or authorized Employee)
- **Request Body:**
  ```json
  {
    "product_id": "1d8f7a93-...",
    "warehouse_id": "3c9d2b11-...",
    "movement_type": "DAMAGE_WRITEOFF",
    "quantity": -5.00,
    "reference_doc_type": "DamageInspection",
    "reference_doc_id": "DMG-2026-0042",
    "notes": "Water leakage in sector 4B"
  }
  ```

### 3.3 Physical Count Reconciliation
- **Endpoint:** `POST /api/v1/inventory/reconcile/`
- **Access:** Employee (Submit count) | Manager (Approve adjustment)

---

## 4. Predictive Intelligence Endpoints (`/api/v1/forecasting/`)

### 4.1 Generate 30-Day Demand Forecast
- **Endpoint:** `POST /api/v1/forecasting/predict/`
- **Access:** Manager Only
- **Request Body:**
  ```json
  {
    "product_id": "1d8f7a93-...",
    "warehouse_id": "3c9d2b11-...",
    "model_type": "LSTM",
    "horizon_days": 30
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "status": "success",
    "data": {
      "sku": "SKU-ELEC-4091",
      "model": "LSTM-MultiStep-V1",
      "forecast_horizon": 30,
      "forecast": [
        {"day": 1, "date": "2026-11-02", "predicted_demand": 21.4, "lower": 18.2, "upper": 24.6},
        {"day": 2, "date": "2026-11-03", "predicted_demand": 22.8, "lower": 19.1, "upper": 26.5}
      ],
      "evaluation": {
        "historical_wape": 0.084,
        "historical_rmse": 3.12
      }
    }
  }
  ```

---

## 5. Autonomous Procurement Endpoints (`/api/v1/procurement/`)

### 5.1 List Purchase Orders
- **Endpoint:** `GET /api/v1/procurement/orders/`
- **Query Parameters:** `status`, `supplier_id`, `category` (B/C), `date_from`, `date_to`

### 5.2 Approve Purchase Order (Category C Human Gateway)
- **Endpoint:** `POST /api/v1/procurement/orders/{id}/approve/`
- **Access:** Manager Only
- **Request Body:**
  ```json
  {
    "decision": "APPROVED",
    "supervisor_notes": "Emergency stock authorized due to upcoming Q4 seasonal surge."
  }
  ```

### 5.3 Dispatch Purchase Order
- **Endpoint:** `POST /api/v1/procurement/orders/{id}/dispatch/`
- **Access:** Policy-Controlled Autonomous (Category B) or Manager (Category C)

---

## 6. Local AI Copilot Endpoints (`/api/v1/intelligence/`)

### 6.1 Context-Aware Operational Query
- **Endpoint:** `POST /api/v1/intelligence/query/`
- **Access:** Manager Only
- **Request Body:**
  ```json
  {
    "query": "Which products face stockout risk within the next 7 days?",
    "include_telemetry": true
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "status": "success",
    "data": {
      "answer": "Two products are currently at critical stockout risk within the next 7 days: SKU-ELEC-4091 (4.2 days remaining) and SKU-MECH-1022 (6.1 days remaining). Both have replenishment purchase orders drafted and pending approval.",
      "structured_data": [
        {"sku": "SKU-ELEC-4091", "days_remaining": 4.2, "recommended_order": 450, "po_id": "PO-2026-11-0012"},
        {"sku": "SKU-MECH-1022", "days_remaining": 6.1, "recommended_order": 200, "po_id": "PO-2026-11-0013"}
      ],
      "source": "Deterministic Inventory & ROP Service + Ollama Llama 3.2 Narrative"
    }
  }
  ```

---

## 7. Autonomous Workflow Control Center (`/api/v1/automation/`)

### 7.1 Workflow Control Center Telemetry
- **Endpoint:** `GET /api/v1/automation/control-center/`
- **Access:** Manager Only
- **Response (200 OK):**
  ```json
  {
    "status": "success",
    "data": {
      "active_workflows": 2,
      "completed_today": 48,
      "failed_today": 0,
      "awaiting_approval": 3,
      "human_intervention_rate_pct": 5.88,
      "automation_rate_pct": 94.12,
      "average_execution_time_seconds": 1.42
    }
  }
  ```

### 7.2 Retry Failed Workflow Task
- **Endpoint:** `POST /api/v1/automation/retry/{execution_id}/`
- **Access:** Manager Only

---

## 8. Cryptographic Audit & Governance (`/api/v1/audit/`)

### 8.1 Query Audit Ledger
- **Endpoint:** `GET /api/v1/audit/ledger/`
- **Access:** Manager Only (Restricted)
- **Query Parameters:** `event_type`, `entity_type`, `actor_username`, `date_from`, `date_to`

### 8.2 Verify Audit Ledger Cryptographic Integrity
- **Endpoint:** `POST /api/v1/audit/verify/`
- **Access:** Manager Only
- **Response (200 OK):**
  ```json
  {
    "status": "success",
    "data": {
      "verified_records_count": 1284,
      "chain_integrity": "VALID",
      "tampering_detected": false,
      "genesis_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "head_hash": "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"
    }
  }
  ```
