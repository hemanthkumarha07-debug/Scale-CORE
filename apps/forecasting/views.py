from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions

from .models import ForecastModel, DemandForecast
from .services import LSTMForecastingEngine, DynamicROPDecisionEngine, ForecastBenchmarkEvaluator
from apps.inventory.models import Product, Warehouse
from apps.accounts.permissions import ManagerRequiredMixin


class ForecastingDashboardView(ManagerRequiredMixin, TemplateView):
    """
    Manager view for Predictive Intelligence & Forecasting Telemetry.
    Part 9.6 of the Master Specification.
    """
    template_name = 'forecasting/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sku = self.request.GET.get('sku', 'SKU-ELEC-4091')
        product = Product.objects.filter(sku=sku).first() or Product.objects.first()
        warehouse = Warehouse.objects.first()

        context['products'] = Product.objects.all().order_by('sku')
        context['selected_product'] = product
        context['selected_warehouse'] = warehouse

        if product and warehouse:
            # 1. 30-day forecast projection
            forecast = LSTMForecastingEngine.generate_30day_forecast(product, warehouse)
            context['forecast_data'] = forecast

            # 2. Dynamic ROP decision metrics
            rop_metrics = DynamicROPDecisionEngine.calculate_rop_and_safety_stock(product, warehouse)
            context['rop_metrics'] = rop_metrics

            # 3. Model benchmarks
            benchmarks = ForecastBenchmarkEvaluator.evaluate_models(product, warehouse)
            context['benchmarks'] = benchmarks

        return context


class ForecastPredictionAPIView(APIView):
    """
    REST API endpoint generating 30-day demand forecast.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        sku = request.data.get('sku')
        wh_code = request.data.get('warehouse')

        product = get_object_or_404(Product, sku=sku)
        warehouse = get_object_or_404(Warehouse, code=wh_code) if wh_code else Warehouse.objects.first()

        forecast = LSTMForecastingEngine.generate_30day_forecast(product, warehouse)
        rop_metrics = DynamicROPDecisionEngine.calculate_rop_and_safety_stock(product, warehouse)

        return Response({
            'status': 'success',
            'data': {
                'sku': product.sku,
                'product_name': product.name,
                'warehouse': warehouse.code,
                'forecast_horizon_days': 30,
                'forecast': forecast,
                'rop_metrics': rop_metrics
            }
        })
