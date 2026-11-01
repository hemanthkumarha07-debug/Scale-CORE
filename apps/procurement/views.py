from decimal import Decimal
from django.views.generic import ListView, DetailView, View
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Sum, Count

from .models import PurchaseOrder, PurchaseOrderItem, POStatus, POCategory, ProcurementPolicy
from .services import AutonomousProcurementService
from apps.accounts.permissions import ManagerRequiredMixin, OperationalRequiredMixin


class PurchaseOrderListView(OperationalRequiredMixin, ListView):
    """
    Procurement Lifecycle and Order Management.
    """
    model = PurchaseOrder
    template_name = 'procurement/orders_list.html'
    context_object_name = 'orders'
    paginate_by = 25

    def get_queryset(self):
        qs = PurchaseOrder.objects.select_related('supplier', 'warehouse', 'approved_by').order_by('-created_at')
        status = self.request.GET.get('status')
        category = self.request.GET.get('category')
        if status:
            qs = qs.filter(status=status)
        if category:
            qs = qs.filter(category=category)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pending_approval_count'] = PurchaseOrder.objects.filter(status=POStatus.AWAITING_APPROVAL).count()
        context['dispatched_count'] = PurchaseOrder.objects.filter(status=POStatus.DISPATCHED).count()
        context['total_commitments'] = PurchaseOrder.objects.filter(
            status__in=[POStatus.AWAITING_APPROVAL, POStatus.APPROVED, POStatus.DISPATCHED]
        ).aggregate(t=Sum('total_amount'))['t'] or Decimal('0.00')

        policy = ProcurementPolicy.objects.filter(is_active=True).first()
        context['auto_dispatch_max'] = policy.auto_dispatch_max_value if policy else Decimal('5000.00')
        return context


class PurchaseOrderDetailView(OperationalRequiredMixin, DetailView):
    """
    Drill-down inspection of an individual Purchase Order.
    """
    model = PurchaseOrder
    template_name = 'procurement/order_detail.html'
    context_object_name = 'order'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.items.select_related('product', 'product__category').all()
        return context


class ApprovePurchaseOrderView(ManagerRequiredMixin, View):
    """
    Manager action: Authorizes and dispatches a Category C order.
    """
    def post(self, request, pk):
        po = get_object_or_404(PurchaseOrder, pk=pk)
        notes = request.POST.get('supervisor_notes', '')
        try:
            AutonomousProcurementService.approve_purchase_order(po, supervisor=request.user, notes=notes)
            messages.success(request, f"Purchase Order {po.po_number} successfully authorized and dispatched.")
        except ValidationError as e:
            messages.error(request, str(e))
        return redirect('procurement:order-detail', pk=pk)


class RejectPurchaseOrderView(ManagerRequiredMixin, View):
    """
    Manager action: Rejects and cancels a purchase order.
    """
    def post(self, request, pk):
        po = get_object_or_404(PurchaseOrder, pk=pk)
        reason = request.POST.get('rejection_reason', 'Rejected by Supervisor')
        try:
            AutonomousProcurementService.reject_purchase_order(po, supervisor=request.user, reason=reason)
            messages.warning(request, f"Purchase Order {po.po_number} was rejected and cancelled.")
        except ValidationError as e:
            messages.error(request, str(e))
        return redirect('procurement:order-detail', pk=pk)
