# SCALE.Core — Relational Database Schema Specification
**Target Database:** PostgreSQL 16 (Development Compatible: SQLite 3.45+)  
**Data Integrity Standard:** Third Normal Form (3NF), Cryptographic Audit Chaining, Decimal Precision for Financial & Quantity Fields  
**Project Owner:** Hemanth Kumar H A  
**Document Status:** Production-Oriented Schema Design  

---

## 1. Data Design Principles

In strict adherence to **Part 7, Part 23, and Part 28** of the Master Specification:
1. **Precision & Types:** All currency and quantity values use `DecimalField(max_digits=14, decimal_places=4)` or `(12, 2)`. No floating-point types (`float`, `double`) are permitted for financial balances, inventory counts, or prices.
2. **Referential Integrity:** All relationships use explicit foreign keys with `on_delete=models.PROTECT` on master records to prevent accidental cascading deletion of historical supply chain transactions.
3. **Database Constraints:** `CheckConstraint` enforces non-negative stock, non-negative prices, valid status transitions, and percentage ranges [0, 100].
4. **Indexing Strategy:** Composite indexes are placed on high-frequency query paths: `(sku, warehouse)`, `(order_id, status)`, `(created_at, event_type)`, and `(workflow_id, status)`.
5. **Cryptographic Chaining:** The `AuditLog` table contains immutable records with `previous_hash` and `current_hash` (SHA-256) ensuring verifiable tamper resistance.

---

## 2. Entity Relationship Diagram (Conceptual)

```
  +------------------+           +-------------------+
  |    SCALEUser     |◄──────────┤     AuditLog      |
  +--------┬---------+           +-------------------+
           │
           │ (created_by / approved_by)
           ▼
  +------------------+           +-------------------+           +-------------------+
  |     Supplier     |──────────►|   PurchaseOrder   |──────────►|     Shipment      |
  +--------┬---------+           +---------┬---------+           +---------┬---------+
           │                               │                               │
           ▼                               ▼                               ▼
  +------------------+           +-------------------+           +-------------------+
  | SupplierProduct  |           | PurchaseOrderItem |           |   GoodsReceipt    |
  +--------┬---------+           +---------┬---------+           +---------┬---------+
           │                               │                               │
           ▼                               ▼                               ▼
  +------------------+           +-------------------+                     │
  |     Product      |──────────►| InventoryMovement |◄────────────────────┘
  +--------┬---------+           +-------------------+
           │                               ▲
           ▼                               │
  +------------------+                     │
  | InventoryBalance |─────────────────────┘
  +--------┬---------+
           │
           ▼
  +------------------+           +-------------------+
  |  DemandForecast  |           | WorkflowExecution |
  +------------------+           +-------------------+
```

---

## 3. Comprehensive Schema Definition by Domain

### 3.1 Domain: Accounts & Authentication (`apps/accounts`)

#### Table: `accounts_scaleuser`
- `id` (UUID, Primary Key, default=uuid4)
- `username` (VARCHAR(150), Unique, Indexed)
- `email` (VARCHAR(254), Unique, Indexed)
- `password` (VARCHAR(128), PBKDF2/Argon2 encrypted)
- `role` (VARCHAR(20), Enum: `MANAGER`, `EMPLOYEE`, Default: `EMPLOYEE`, Indexed)
- `first_name` (VARCHAR(150))
- `last_name` (VARCHAR(150))
- `is_active` (BOOLEAN, Default=True)
- `is_staff` (BOOLEAN, Default=False)
- `is_superuser` (BOOLEAN, Default=False)
- `phone_number` (VARCHAR(30), Nullable)
- `department` (VARCHAR(100), Default='Operations')
- `failed_login_attempts` (INTEGER, Default=0)
- `last_login_ip` (GENERIC_IP_ADDRESS, Nullable)
- `created_at` (TIMESTAMPTZ, auto_now_add=True)
- `updated_at` (TIMESTAMPTZ, auto_now=True)

---

### 3.2 Domain: Inventory Intelligence (`apps/inventory`)

#### Table: `inventory_warehouse`
- `id` (UUID, Primary Key)
- `code` (VARCHAR(20), Unique, Indexed) — e.g., 'WH-CENTRAL-01'
- `name` (VARCHAR(100))
- `address` (TEXT)
- `city` (VARCHAR(100))
- `country` (VARCHAR(100), Default='India')
- `total_capacity_sqft` (DECIMAL(12, 2))
- `is_active` (BOOLEAN, Default=True)
- `created_at` (TIMESTAMPTZ)

#### Table: `inventory_productcategory`
- `id` (UUID, Primary Key)
- `code` (VARCHAR(30), Unique)
- `name` (VARCHAR(100))
- `description` (TEXT, Nullable)
- `holding_cost_rate_annual` (DECIMAL(5, 4), Default=0.2000) — e.g. 20% annual holding rate
- `created_at` (TIMESTAMPTZ)

#### Table: `inventory_product`
- `id` (UUID, Primary Key)
- `sku` (VARCHAR(50), Unique, Indexed) — e.g., 'SKU-ELEC-4091'
- `name` (VARCHAR(255), Indexed)
- `category_id` (FK -> `inventory_productcategory`, on_delete=PROTECT)
- `unit_of_measure` (VARCHAR(20), Default='UNIT') — e.g., 'UNIT', 'KG', 'LITER', 'BOX'
- `description` (TEXT, Blank=True)
- `unit_cost` (DECIMAL(14, 4), CheckConstraint > 0)
- `unit_price` (DECIMAL(14, 4), CheckConstraint > 0)
- `abc_class` (VARCHAR(1), Enum: `A`, `B`, `C`, Nullable, Indexed)
- `xyz_class` (VARCHAR(1), Enum: `X`, `Y`, `Z`, Nullable, Indexed)
- `reorder_point` (DECIMAL(12, 2), Default=0.00)
- `safety_stock` (DECIMAL(12, 2), Default=0.00)
- `minimum_order_qty` (DECIMAL(12, 2), Default=1.00)
- `order_multiple` (DECIMAL(12, 2), Default=1.00)
- `lead_time_days_avg` (DECIMAL(6, 2), Default=7.00)
- `lead_time_days_std` (DECIMAL(6, 2), Default=1.50)
- `service_level_target` (DECIMAL(4, 3), Default=0.950) — 95% service level
- `status` (VARCHAR(20), Enum: `ACTIVE`, `DISCONTINUED`, `UNDER_REVIEW`, Default='ACTIVE')
- `created_at` (TIMESTAMPTZ)
- `updated_at` (TIMESTAMPTZ)

#### Table: `inventory_inventorybalance`
- `id` (UUID, Primary Key)
- `product_id` (FK -> `inventory_product`, on_delete=PROTECT)
- `warehouse_id` (FK -> `inventory_warehouse`, on_delete=PROTECT)
- `on_hand_stock` (DECIMAL(12, 2), Default=0.00, CheckConstraint >= 0)
- `reserved_stock` (DECIMAL(12, 2), Default=0.00, CheckConstraint >= 0)
- `incoming_stock` (DECIMAL(12, 2), Default=0.00, CheckConstraint >= 0)
- `damaged_stock` (DECIMAL(12, 2), Default=0.00, CheckConstraint >= 0)
- `storage_bin` (VARCHAR(50), Blank=True)
- `last_recounted_at` (TIMESTAMPTZ, Nullable)
- `updated_at` (TIMESTAMPTZ)
- *Unique Constraint:* `(product_id, warehouse_id)`

#### Table: `inventory_inventorymovement`
- `id` (UUID, Primary Key)
- `transaction_number` (VARCHAR(50), Unique, Indexed)
- `product_id` (FK -> `inventory_product`, on_delete=PROTECT)
- `warehouse_id` (FK -> `inventory_warehouse`, on_delete=PROTECT)
- `movement_type` (VARCHAR(30), Enum: `GOODS_RECEIPT`, `SALES_DISPATCH`, `INTERNAL_TRANSFER`, `DAMAGE_WRITEOFF`, `COUNT_ADJUSTMENT`, `RETURN`)
- `quantity` (DECIMAL(12, 2), CheckConstraint != 0) — positive for inbound, negative for outbound
- `balance_before` (DECIMAL(12, 2))
- `balance_after` (DECIMAL(12, 2))
- `reference_doc_type` (VARCHAR(50)) — e.g. 'PurchaseOrder', 'SalesOrder', 'StockReconciliation'
- `reference_doc_id` (VARCHAR(100))
- `performed_by_id` (FK -> `accounts_scaleuser`, Nullable, on_delete=SET_NULL)
- `notes` (TEXT, Blank=True)
- `timestamp` (TIMESTAMPTZ, auto_now_add=True, Indexed)

#### Table: `inventory_stockreconciliation`
- `id` (UUID, Primary Key)
- `reconciliation_number` (VARCHAR(50), Unique)
- `warehouse_id` (FK -> `inventory_warehouse`, on_delete=PROTECT)
- `status` (VARCHAR(25), Enum: `DRAFT`, `SUBMITTED`, `UNDER_REVIEW`, `APPROVED`, `REJECTED`, Default='DRAFT')
- `assigned_to_id` (FK -> `accounts_scaleuser`, on_delete=PROTECT)
- `reviewed_by_id` (FK -> `accounts_scaleuser`, Nullable, on_delete=PROTECT)
- `total_discrepancy_value` (DECIMAL(14, 2), Default=0.00)
- `created_at` (TIMESTAMPTZ)
- `approved_at` (TIMESTAMPTZ, Nullable)

#### Table: `inventory_stockreconciliationitem`
- `id` (UUID, Primary Key)
- `reconciliation_id` (FK -> `inventory_stockreconciliation`, on_delete=CASCADE)
- `product_id` (FK -> `inventory_product`, on_delete=PROTECT)
- `system_quantity` (DECIMAL(12, 2))
- `physical_quantity` (DECIMAL(12, 2))
- `discrepancy_quantity` (DECIMAL(12, 2))
- `discrepancy_cost` (DECIMAL(14, 2))
- `notes` (TEXT, Blank=True)

---

### 3.3 Domain: Sales & Demand Records (`apps/sales`)

#### Table: `sales_dailysaleslog`
- `id` (UUID, Primary Key)
- `date` (DATE, Indexed)
- `product_id` (FK -> `inventory_product`, on_delete=PROTECT)
- `warehouse_id` (FK -> `inventory_warehouse`, on_delete=PROTECT)
- `units_sold` (DECIMAL(12, 2), Default=0.00, CheckConstraint >= 0)
- `sales_revenue` (DECIMAL(14, 2), Default=0.00)
- `was_stockout_day` (BOOLEAN, Default=False) — Critical for censoring correction
- `is_promotion_active` (BOOLEAN, Default=False)
- *Unique Constraint:* `(date, product_id, warehouse_id)`

---

### 3.4 Domain: Suppliers (`apps/suppliers`)

#### Table: `suppliers_supplier`
- `id` (UUID, Primary Key)
- `code` (VARCHAR(30), Unique, Indexed) — e.g. 'SUPP-IND-0104'
- `legal_name` (VARCHAR(255))
- `contact_person` (VARCHAR(150))
- `email` (VARCHAR(254), Indexed)
- `phone` (VARCHAR(30))
- `address` (TEXT)
- `payment_terms` (VARCHAR(50), Default='NET_30') — e.g. 'NET_30', 'NET_60', 'IMMEDIATE'
- `reliability_score` (DECIMAL(5, 2), Default=100.00) — [0, 100]
- `quality_score` (DECIMAL(5, 2), Default=100.00) — [0, 100]
- `lead_time_compliance_rate` (DECIMAL(5, 2), Default=100.00) — [0, 100]
- `status` (VARCHAR(20), Enum: `ACTIVE`, `PROBATION`, `SUSPENDED`, `INACTIVE`, Default='ACTIVE')
- `created_at` (TIMESTAMPTZ)
- `updated_at` (TIMESTAMPTZ)

#### Table: `suppliers_supplierproduct`
- `id` (UUID, Primary Key)
- `supplier_id` (FK -> `suppliers_supplier`, on_delete=PROTECT)
- `product_id` (FK -> `inventory_product`, on_delete=PROTECT)
- `supplier_sku` (VARCHAR(100), Blank=True)
- `contracted_unit_price` (DECIMAL(14, 4), CheckConstraint > 0)
- `lead_time_days` (INTEGER, Default=7)
- `minimum_order_quantity` (DECIMAL(12, 2), Default=1.00)
- `is_preferred` (BOOLEAN, Default=False)
- *Unique Constraint:* `(supplier_id, product_id)`

---

### 3.5 Domain: Autonomous Procurement (`apps/procurement`)

#### Table: `procurement_procurementpolicy`
- `id` (UUID, Primary Key)
- `policy_name` (VARCHAR(100))
- `auto_dispatch_max_value` (DECIMAL(14, 2), Default=5000.00) — Maximum auto-dispatch ceiling ($5,000)
- `require_approval_above_value` (DECIMAL(14, 2), Default=5000.00)
- `max_supplier_price_variance_pct` (DECIMAL(5, 2), Default=15.00) — Quote variance ceiling
- `min_supplier_reliability_score` (DECIMAL(5, 2), Default=80.00)
- `is_active` (BOOLEAN, Default=True)
- `created_at` (TIMESTAMPTZ)

#### Table: `procurement_purchaseorder`
- `id` (UUID, Primary Key)
- `po_number` (VARCHAR(50), Unique, Indexed) — e.g. 'PO-2026-11-0001'
- `supplier_id` (FK -> `suppliers_supplier`, on_delete=PROTECT)
- `warehouse_id` (FK -> `inventory_warehouse`, on_delete=PROTECT)
- `total_amount` (DECIMAL(14, 2), Default=0.00)
- `status` (VARCHAR(30), Enum: `DRAFT`, `AWAITING_APPROVAL`, `APPROVED`, `DISPATCHED`, `ACKNOWLEDGED`, `PARTIALLY_DELIVERED`, `COMPLETED`, `CANCELLED`, Default='DRAFT', Indexed)
- `category` (VARCHAR(2), Enum: `B`, `C`, Default='B') — Policy-controlled (B) vs Human-approved (C)
- `generated_by_system` (BOOLEAN, Default=True)
- `ai_justification` (TEXT, Blank=True)
- `approved_by_id` (FK -> `accounts_scaleuser`, Nullable, on_delete=PROTECT)
- `created_at` (TIMESTAMPTZ, auto_now_add=True)
- `dispatched_at` (TIMESTAMPTZ, Nullable)
- `expected_delivery_date` (DATE)

#### Table: `procurement_purchaseorderitem`
- `id` (UUID, Primary Key)
- `purchase_order_id` (FK -> `procurement_purchaseorder`, on_delete=CASCADE)
- `product_id` (FK -> `inventory_product`, on_delete=PROTECT)
- `quantity` (DECIMAL(12, 2), CheckConstraint > 0)
- `unit_price` (DECIMAL(14, 4), CheckConstraint > 0)
- `total_price` (DECIMAL(14, 2))
- `quantity_received` (DECIMAL(12, 2), Default=0.00)

---

### 3.6 Domain: Logistics & Shipments (`apps/logistics`)

#### Table: `logistics_shipment`
- `id` (UUID, Primary Key)
- `tracking_number` (VARCHAR(100), Unique, Indexed)
- `purchase_order_id` (FK -> `procurement_purchaseorder`, on_delete=PROTECT)
- `carrier_name` (VARCHAR(100))
- `dispatch_date` (DATE)
- `expected_delivery_date` (DATE)
- `actual_delivery_date` (DATE, Nullable)
- `freight_cost` (DECIMAL(12, 2), Default=0.00)
- `status` (VARCHAR(30), Enum: `CREATED`, `DISPATCHED`, `IN_TRANSIT`, `DELAYED`, `OUT_FOR_DELIVERY`, `DELIVERED`, `EXCEPTION`, `CANCELLED`, Default='CREATED')
- `is_delayed` (BOOLEAN, Default=False)

#### Table: `logistics_goodsreceipt`
- `id` (UUID, Primary Key)
- `receipt_number` (VARCHAR(50), Unique)
- `purchase_order_id` (FK -> `procurement_purchaseorder`, on_delete=PROTECT)
- `shipment_id` (FK -> `logistics_shipment`, Nullable, on_delete=PROTECT)
- `received_by_id` (FK -> `accounts_scaleuser`, on_delete=PROTECT)
- `received_at` (TIMESTAMPTZ, auto_now_add=True)
- `discrepancy_detected` (BOOLEAN, Default=False)
- `notes` (TEXT, Blank=True)

---

### 3.7 Domain: Predictive Intelligence & Deep Learning (`apps/forecasting`)

#### Table: `forecasting_forecastmodel`
- `id` (UUID, Primary Key)
- `model_name` (VARCHAR(100)) — e.g. 'LSTM-MultiStep-V1'
- `model_type` (VARCHAR(50), Enum: `LSTM`, `XGBOOST`, `EXPONENTIAL_SMOOTHING`, `MOVING_AVERAGE`)
- `version` (VARCHAR(30))
- `model_file_path` (VARCHAR(500), Blank=True)
- `scaler_file_path` (VARCHAR(500), Blank=True)
- `training_mae` (DECIMAL(8, 4), Nullable)
- `training_rmse` (DECIMAL(8, 4), Nullable)
- `training_wape` (DECIMAL(5, 4), Nullable)
- `is_active` (BOOLEAN, Default=False)
- `trained_at` (TIMESTAMPTZ)

#### Table: `forecasting_demandforecast`
- `id` (UUID, Primary Key)
- `product_id` (FK -> `inventory_product`, on_delete=PROTECT)
- `warehouse_id` (FK -> `inventory_warehouse`, on_delete=PROTECT)
- `forecast_date` (DATE, Indexed)
- `horizon_days` (INTEGER) — 1 to 30
- `predicted_demand` (DECIMAL(12, 2), CheckConstraint >= 0)
- `confidence_lower` (DECIMAL(12, 2), Nullable)
- `confidence_upper` (DECIMAL(12, 2), Nullable)
- `model_used_id` (FK -> `forecasting_forecastmodel`, on_delete=PROTECT)
- `generated_at` (TIMESTAMPTZ, auto_now_add=True)
- *Unique Constraint:* `(product_id, warehouse_id, forecast_date, horizon_days)`

---

### 3.8 Domain: Autonomous Workflow Orchestration (`apps/automation`)

#### Table: `automation_automationworkflow`
- `id` (UUID, Primary Key)
- `name` (VARCHAR(100), Unique)
- `workflow_type` (VARCHAR(50)) — e.g. 'NIGHTLY_PIPELINE', 'PO_DISPATCH', 'RECONCILIATION'
- `execution_category` (VARCHAR(2), Enum: `A`, `B`, `C`)
- `is_enabled` (BOOLEAN, Default=True)
- `max_retries` (INTEGER, Default=3)
- `timeout_seconds` (INTEGER, Default=300)

#### Table: `automation_workflowexecution`
- `id` (UUID, Primary Key)
- `workflow_id` (FK -> `automation_automationworkflow`, on_delete=PROTECT)
- `idempotency_key` (VARCHAR(128), Unique, Indexed)
- `status` (VARCHAR(30), Enum: `QUEUED`, `RUNNING`, `COMPLETED`, `FAILED`, `RETRYING`, `SUSPENDED`, `AWAITING_APPROVAL`, `CANCELLED`, `RECONCILIATION_REQUIRED`, Default='QUEUED', Indexed)
- `related_entity_type` (VARCHAR(100), Blank=True)
- `related_entity_id` (VARCHAR(100), Blank=True)
- `initiated_at` (TIMESTAMPTZ, auto_now_add=True)
- `completed_at` (TIMESTAMPTZ, Nullable)
- `retry_count` (INTEGER, Default=0)
- `error_message` (TEXT, Blank=True)
- `execution_context` (JSONB, Default=dict)

---

### 3.9 Domain: Cryptographic Audit Ledger (`apps/audit`)

#### Table: `audit_auditlog`
- `id` (UUID, Primary Key)
- `actor_id` (FK -> `accounts_scaleuser`, Nullable, on_delete=PROTECT)
- `actor_username` (VARCHAR(150)) — Preserved even if user record modified
- `actor_role` (VARCHAR(20))
- `event_type` (VARCHAR(100), Indexed) — e.g., 'INVENTORY_ADJUSTMENT', 'PO_APPROVED'
- `entity_type` (VARCHAR(100), Indexed)
- `entity_id` (VARCHAR(100), Indexed)
- `state_before` (JSONB, Default=dict)
- `state_after` (JSONB, Default=dict)
- `source_ip` (GENERIC_IP_ADDRESS, Nullable)
- `request_id` (VARCHAR(100), Blank=True)
- `timestamp` (TIMESTAMPTZ, auto_now_add=True, Indexed)
- `previous_hash` (VARCHAR(64), Indexed)
- `current_hash` (VARCHAR(64), Unique, Indexed) — SHA-256(previous_hash + actor + event_type + timestamp + state_after)

---

## 4. Database Views & Indexing Directives

### Composite Indexes:
- `CREATE INDEX idx_inv_prod_wh ON inventory_inventorybalance(product_id, warehouse_id);`
- `CREATE INDEX idx_sales_date_sku ON sales_dailysaleslog(date, product_id);`
- `CREATE INDEX idx_po_status_date ON procurement_purchaseorder(status, created_at);`
- `CREATE INDEX idx_audit_chain ON audit_auditlog(timestamp, previous_hash);`
- `CREATE INDEX idx_workflow_status ON automation_workflowexecution(status, initiated_at);`

### Immutability Trigger (PostgreSQL Level):
```sql
CREATE OR REPLACE FUNCTION prevent_audit_tampering()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'AuditLog is strictly append-only. UPDATE and DELETE operations are forbidden.';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_audit_immutable
BEFORE UPDATE OR DELETE ON audit_auditlog
FOR EACH ROW EXECUTE FUNCTION prevent_audit_tampering();
```
