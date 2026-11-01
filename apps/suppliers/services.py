import logging
from decimal import Decimal
from typing import List, Dict, Optional
from django.db.models import Avg
from .models import Supplier, SupplierProduct, SupplierStatus
from apps.inventory.models import Product

logger = logging.getLogger('scale_core.suppliers')


class SupplierEvaluationService:
    """
    Multi-Factor Supplier Evaluation & Scoring Service.
    Part 12.2 and Part 13 of the Master Specification.
    Evaluates suppliers using:
    - Delivery Reliability Score (45% weight)
    - Quality & Defect-Free Score (35% weight)
    - Lead-Time Compliance Rate (20% weight)
    - Contracted unit price comparison
    """

    @classmethod
    def evaluate_and_rank_suppliers(cls, product: Product) -> List[Dict[str, any]]:
        """
        Retrieves all eligible suppliers for a given product,
        ranks them by composite scoring and price competitiveness.
        """
        supplier_links = SupplierProduct.objects.filter(
            product=product,
            supplier__status=SupplierStatus.ACTIVE
        ).select_related('supplier')

        ranked_list = []
        for link in supplier_links:
            supp = link.supplier
            comp_score = supp.composite_score

            ranked_list.append({
                'supplier_id': str(supp.id),
                'supplier_code': supp.code,
                'supplier_name': supp.legal_name,
                'contracted_price': link.contracted_unit_price,
                'lead_time_days': link.lead_time_days,
                'minimum_order_qty': link.minimum_order_quantity,
                'reliability_score': supp.reliability_score,
                'quality_score': supp.quality_score,
                'lead_time_compliance': supp.lead_time_compliance_rate,
                'composite_score': comp_score,
                'is_preferred': link.is_preferred,
                'payment_terms': supp.get_payment_terms_display()
            })

        # Rank primarily by preferred flag, then composite score descending, then price ascending
        ranked_list.sort(
            key=lambda x: (not x['is_preferred'], -float(x['composite_score']), float(x['contracted_price']))
        )
        return ranked_list

    @classmethod
    def update_supplier_metrics(
        cls,
        supplier: Supplier,
        on_time: bool,
        quality_rating_pct: float
    ):
        """
        Updates supplier scores based on recent goods receipt outcomes.
        """
        # Exponential moving update (smoothing alpha = 0.2)
        alpha = Decimal('0.20')
        new_rel = (Decimal('100.00') if on_time else Decimal('50.00'))
        supplier.reliability_score = (alpha * new_rel) + ((Decimal('1.00') - alpha) * supplier.reliability_score)

        new_qual = Decimal(str(quality_rating_pct))
        supplier.quality_score = (alpha * new_qual) + ((Decimal('1.00') - alpha) * supplier.quality_score)
        supplier.save(update_fields=['reliability_score', 'quality_score', 'updated_at'])
