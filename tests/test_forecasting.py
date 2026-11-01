from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from apps.inventory.models import Warehouse, ProductCategory, Product, InventoryBalance
from apps.forecasting.services import (
    TimeSeriesDataPipeline, LSTMForecastingEngine,
    DynamicROPDecisionEngine, ForecastBenchmarkEvaluator
)
from apps.sales.models import DailySalesLog


class ForecastingAndROPTests(TestCase):
    """
    Test suite for Phase 4: Demand Forecasting and Dynamic Reorder Point Engine.
    """

    def setUp(self):
        self.wh = Warehouse.objects.create(code='WH-FC-01', name='Forecasting Test Hub')
        self.cat = ProductCategory.objects.create(code='CAT-F', name='Sensors')
        self.product = Product.objects.create(
            sku='SKU-FC-101',
            name='Industrial Thermal Sensor',
            category=self.cat,
            unit_cost=Decimal('45.00'),
            unit_price=Decimal('70.00'),
            reorder_point=Decimal('150.00'),
            safety_stock=Decimal('50.00'),
            minimum_order_qty=Decimal('50.00'),
            order_multiple=Decimal('10.00'),
            lead_time_days_avg=Decimal('7.00'),
            lead_time_days_std=Decimal('1.50'),
            service_level_target=Decimal('0.950')
        )
        self.balance = InventoryBalance.objects.create(
            product=self.product,
            warehouse=self.wh,
            on_hand_stock=Decimal('80.00'),
            reserved_stock=Decimal('10.00'),
            incoming_stock=Decimal('0.00')
        )

        # Seed 30 days of sales with 1 stockout day to verify censoring correction
        today = timezone.now().date()
        for i in range(30):
            d = today - timezone.timedelta(days=i)
            was_stockout = (i == 5)
            units = Decimal('0.00') if was_stockout else Decimal('12.00')
            DailySalesLog.objects.create(
                date=d,
                product=self.product,
                warehouse=self.wh,
                units_sold=units,
                sales_revenue=units * Decimal('70.00'),
                was_stockout_day=was_stockout
            )

    def test_time_series_data_pipeline_and_censoring_correction(self):
        """Verify pipeline cleanses stockout day without treating it as zero demand (Part 9.1)."""
        df = TimeSeriesDataPipeline.extract_demand_series(self.product, self.wh)
        self.assertFalse(df.empty)
        self.assertIn('rolling_mean_7', df.columns)
        self.assertIn('lag_1', df.columns)

        # The stockout day units_sold must be interpolated to positive value > 0
        stockout_rows = df[df['was_stockout_day']]
        if not stockout_rows.empty:
            self.assertGreater(stockout_rows['units_sold'].values[0], 0.0)

    def test_dynamic_rop_and_safety_stock_formula(self):
        """Verify deterministic ROP = (D_bar * L) + SS (Part 10.1)."""
        metrics = DynamicROPDecisionEngine.calculate_rop_and_safety_stock(self.product, self.wh)

        self.assertGreater(metrics['safety_stock'], Decimal('0.00'))
        self.assertGreater(metrics['reorder_point'], Decimal('0.00'))
        self.assertEqual(
            metrics['reorder_point'],
            metrics['lead_time_demand'] + metrics['safety_stock']
        )
        # Available stock is 80 - 10 = 70. Since 70 < ROP (~120-150), is_critical must be True
        self.assertTrue(metrics['is_critical'])
        self.assertGreater(metrics['recommended_order_quantity'], Decimal('0.00'))

    def test_lstm_30day_forecast_generation(self):
        """Verify 30-day forecast horizon generates exactly 30 projections (Part 9.3)."""
        forecast = LSTMForecastingEngine.generate_30day_forecast(self.product, self.wh)
        self.assertEqual(len(forecast), 30)
        self.assertEqual(forecast[0]['day'], 1)
        self.assertEqual(forecast[29]['day'], 30)
        self.assertGreater(forecast[0]['predicted_demand'], 0.0)
        self.assertGreaterEqual(forecast[0]['confidence_upper'], forecast[0]['confidence_lower'])

    def test_forecast_benchmark_evaluation(self):
        """Verify benchmarking against Moving Average and Exponential Smoothing (Part 9.5)."""
        benchmarks = ForecastBenchmarkEvaluator.evaluate_models(self.product, self.wh)
        self.assertIn('LSTM', benchmarks)
        self.assertIn('ExponentialSmoothing', benchmarks)
        self.assertIn('MovingAverage', benchmarks)

        # Verify metric keys
        for m in ['mae', 'rmse', 'wape', 'bias']:
            self.assertIn(m, benchmarks['LSTM'])
            self.assertIn(m, benchmarks['MovingAverage'])
