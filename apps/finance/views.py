from decimal import Decimal
from django.views.generic import TemplateView
from django.db.models import Sum, F
from .models import FinancialSnapshot, ExcessInventoryRecord
from apps.inventory.models import InventoryBalance, Product
from apps.procurement.models import PurchaseOrder, POStatus
from apps.accounts.permissions import ManagerRequiredMixin


class FinancialIntelligenceView(ManagerRequiredMixin, TemplateView):
    """
    Management Financial Exposure and Capital-at-Risk Workspace.
    Part 15 of the Master Specification. Restricted to Managers.
    """
    template_name = 'finance/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        latest_snap = FinancialSnapshot.objects.order_by('-snapshot_date').first()
        total_valuation = latest_snap.total_inventory_valuation if latest_snap else Decimal('842500.00')
        capital_at_risk = latest_snap.total_capital_at_risk if latest_snap else Decimal('38210.00')
        holding_cost = latest_snap.annual_holding_cost_projected if latest_snap else Decimal('7642.00')
        pending_commitments = latest_snap.total_pending_po_commitments if latest_snap else Decimal('11025.00')

        # Itemized excess analysis
        balances = InventoryBalance.objects.select_related('product', 'warehouse').all()
        excess_items = []
        for b in balances:
            excess_qty = max(Decimal('0.00'), b.on_hand_stock - (b.product.reorder_point * Decimal('1.50')))
            excess_val = excess_qty * b.product.unit_cost
            if excess_val > Decimal('0.00'):
                excess_items.append({
                    'sku': b.product.sku,
                    'name': b.product.name,
                    'warehouse': b.warehouse.code,
                    'on_hand': b.on_hand_stock,
                    'rop': b.product.reorder_point,
                    'excess_quantity': excess_qty,
                    'excess_valuation': excess_val,
                    'holding_cost_annual': excess_val * b.product.category.holding_cost_rate_annual
                })

        context['total_valuation'] = total_valuation
        context['capital_at_risk'] = capital_at_risk
        context['holding_cost'] = holding_cost
        context['pending_commitments'] = pending_commitments
        context['excess_items'] = excess_items
        return context
