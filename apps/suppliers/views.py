from django.views.generic import ListView
from .models import Supplier, SupplierProduct
from apps.accounts.permissions import OperationalRequiredMixin


class SupplierListView(OperationalRequiredMixin, ListView):
    """
    Supplier Master Directory & Scorecard.
    Part 13 of the Master Specification.
    """
    model = Supplier
    template_name = 'suppliers/list.html'
    context_object_name = 'suppliers'
    paginate_by = 20

    def get_queryset(self):
        return Supplier.objects.prefetch_related('supplied_products__product').order_by('legal_name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_suppliers'] = Supplier.objects.count()
        context['active_suppliers'] = Supplier.objects.filter(status='ACTIVE').count()
        return context
