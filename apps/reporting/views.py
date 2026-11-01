import csv
from django.views.generic import TemplateView, View
from django.http import HttpResponse
from django.utils import timezone
from apps.inventory.models import InventoryBalance, Product
from apps.procurement.models import PurchaseOrder
from apps.suppliers.models import Supplier
from apps.accounts.permissions import ManagerRequiredMixin


class ReportingDashboardView(ManagerRequiredMixin, TemplateView):
    """
    Business Intelligence & Operational Reports Center.
    Part 20 of the Master Specification.
    """
    template_name = 'reporting/dashboard.html'


class ExportInventoryCSVView(ManagerRequiredMixin, View):
    """Exports Inventory Health CSV report."""
    def get(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="scale_inventory_report_{timezone.now().strftime("%Y%m%d")}.csv"'

        writer = csv.writer(response)
        writer.writerow(['SKU', 'Product Name', 'Warehouse', 'On Hand', 'Reserved', 'Available', 'Incoming', 'ROP', 'Safety Stock', 'Unit Cost', 'Valuation'])

        balances = InventoryBalance.objects.select_related('product', 'warehouse').all()
        for b in balances:
            writer.writerow([
                b.product.sku,
                b.product.name,
                b.warehouse.code,
                b.on_hand_stock,
                b.reserved_stock,
                b.available_stock,
                b.incoming_stock,
                b.product.reorder_point,
                b.product.safety_stock,
                b.product.unit_cost,
                b.total_valuation
            ])
        return response


class ExportProcurementCSVView(ManagerRequiredMixin, View):
    """Exports Procurement Commitments CSV report."""
    def get(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="scale_procurement_report_{timezone.now().strftime("%Y%m%d")}.csv"'

        writer = csv.writer(response)
        writer.writerow(['PO Number', 'Supplier', 'Warehouse', 'Total Value', 'Status', 'Category', 'Expected Delivery', 'Created At'])

        pos = PurchaseOrder.objects.select_related('supplier', 'warehouse').all()
        for po in pos:
            writer.writerow([
                po.po_number,
                po.supplier.legal_name,
                po.warehouse.code,
                po.total_amount,
                po.status,
                po.category,
                po.expected_delivery_date,
                po.created_at.strftime('%Y-%m-%d %H:%M')
            ])
        return response
