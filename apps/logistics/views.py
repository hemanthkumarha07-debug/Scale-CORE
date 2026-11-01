from django.views import View
from django.shortcuts import render
from apps.accounts.permissions import OperationalRequiredMixin
from .models import Shipment, GoodsReceipt, ShipmentStatus

class LogisticsDashboardView(OperationalRequiredMixin, View):
    """
    Logistics & Inbound Fulfillment Hub.
    Monitors freight in transit, dock receiving, carrier compliance, and put-away records.
    """
    template_name = 'logistics/dashboard.html'

    def get(self, request):
        shipments = Shipment.objects.select_related('purchase_order', 'purchase_order__supplier').order_by('-created_at')[:30]
        receipts = GoodsReceipt.objects.select_related('purchase_order', 'received_by').prefetch_related('items').order_by('-created_at')[:30]
        
        in_transit_count = Shipment.objects.filter(status__in=[ShipmentStatus.DISPATCHED, ShipmentStatus.IN_TRANSIT, ShipmentStatus.OUT_FOR_DELIVERY]).count()
        delayed_count = Shipment.objects.filter(is_delayed=True).count()
        delivered_count = Shipment.objects.filter(status=ShipmentStatus.DELIVERED).count()
        discrepancy_count = GoodsReceipt.objects.filter(discrepancy_detected=True).count()

        return render(request, self.template_name, {
            'shipments': shipments,
            'receipts': receipts,
            'in_transit_count': in_transit_count,
            'delayed_count': delayed_count,
            'delivered_count': delivered_count,
            'discrepancy_count': discrepancy_count,
        })
