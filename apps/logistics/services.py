import uuid
import logging
from decimal import Decimal
from typing import Dict, List, Optional
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError

from .models import Shipment, GoodsReceipt, GoodsReceiptItem, ShipmentStatus
from apps.procurement.models import PurchaseOrder, POStatus
from apps.inventory.services import StockMovementService
from apps.inventory.models import MovementType
from apps.suppliers.services import SupplierEvaluationService
from apps.audit.models import AuditLog

logger = logging.getLogger('scale_core.logistics')


class LogisticsService:
    """
    Logistics & Inbound Fulfillment Service.
    Part 14 of the Master Specification.
    Tracks shipments, records goods receipts, verifies discrepancies, and updates inventory.
    """

    @classmethod
    @transaction.atomic
    def process_goods_receipt(
        cls,
        purchase_order: PurchaseOrder,
        received_items: List[Dict[str, any]],
        operator,
        shipment: Optional[Shipment] = None,
        notes: str = ''
    ) -> GoodsReceipt:
        """
        Processes physical dock arrival of inbound goods.
        Updates PO line items, increments inventory balances, checks for discrepancies,
        and records immutable audit entries.
        """
        receipt_num = f"GRN-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        has_discrepancy = False
        receipt = GoodsReceipt.objects.create(
            receipt_number=receipt_num,
            purchase_order=purchase_order,
            shipment=shipment,
            received_by=operator,
            discrepancy_detected=False,
            notes=notes
        )

        for item_data in received_items:
            po_item = purchase_order.items.get(product_id=item_data['product_id'])
            qty_received = Decimal(str(item_data['quantity_received']))
            qty_damaged = Decimal(str(item_data.get('quantity_damaged', 0)))
            qty_expected = po_item.quantity - po_item.quantity_received

            if qty_received != qty_expected or qty_damaged > 0:
                has_discrepancy = True

            GoodsReceiptItem.objects.create(
                receipt=receipt,
                product=po_item.product,
                quantity_expected=qty_expected,
                quantity_received=qty_received,
                quantity_damaged=qty_damaged,
                notes=item_data.get('notes', '')
            )

            # Update PO line item
            po_item.quantity_received += qty_received
            po_item.save(update_fields=['quantity_received'])

            # Increment physical on-hand inventory for non-damaged goods
            usable_qty = qty_received - qty_damaged
            if usable_qty > 0:
                StockMovementService.record_movement(
                    product=po_item.product,
                    warehouse=purchase_order.warehouse,
                    movement_type=MovementType.GOODS_RECEIPT,
                    quantity=usable_qty,
                    reference_doc_type='GoodsReceipt',
                    reference_doc_id=receipt_num,
                    performed_by=operator,
                    notes=f"Dock receipt for {purchase_order.po_number}"
                )

                # Reduce incoming_stock on balance
                bal = po_item.product.balances.filter(warehouse=purchase_order.warehouse).first()
                if bal:
                    bal.incoming_stock = max(Decimal('0.00'), bal.incoming_stock - usable_qty)
                    bal.save(update_fields=['incoming_stock', 'updated_at'])

        receipt.discrepancy_detected = has_discrepancy
        receipt.save(update_fields=['discrepancy_detected'])

        # Check if PO is completely delivered
        all_completed = all(item.pending_quantity <= 0 for item in purchase_order.items.all())
        purchase_order.status = POStatus.COMPLETED if all_completed else POStatus.PARTIALLY_DELIVERED
        purchase_order.save(update_fields=['status', 'updated_at'])

        # Update shipment status if linked
        if shipment:
            shipment.status = ShipmentStatus.DELIVERED
            shipment.actual_delivery_date = timezone.now().date()
            shipment.save(update_fields=['status', 'actual_delivery_date'])

            # Update supplier delivery compliance metric
            is_on_time = shipment.actual_delivery_date <= shipment.expected_delivery_date
            SupplierEvaluationService.update_supplier_metrics(
                supplier=purchase_order.supplier,
                on_time=is_on_time,
                quality_rating_pct=100.0 if not has_discrepancy else 85.0
            )

        # Record in Immutable Audit Ledger
        AuditLog.record_event(
            event_type='GOODS_RECEIPT_PROCESSED',
            entity_type='GOODS_RECEIPT',
            entity_id=str(receipt.id),
            actor=operator,
            state_after={
                'receipt_number': receipt_num,
                'po_number': purchase_order.po_number,
                'discrepancy_detected': has_discrepancy,
                'po_status': purchase_order.status
            }
        )

        return receipt
