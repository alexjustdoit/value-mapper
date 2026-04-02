"""Tests for data models — especially OutputMetric.calculate() and formula evaluation."""
from data.models import (
    Calculator,
    CalculatorInputField,
    CustomerContext,
    OutputMetric,
    ProductConfig,
    Scenario,
    ValueDriver,
)


def _make_field(key: str, ai_estimate: float, current_value=None) -> CalculatorInputField:
    return CalculatorInputField(
        key=key,
        label=key.replace("_", " ").title(),
        unit="units",
        description="test field",
        ai_estimate=ai_estimate,
        current_value=current_value,
        value_driver="Test Driver",
    )


def _make_metric(label: str, formula: str, unit: str = "$") -> OutputMetric:
    return OutputMetric(label=label, unit=unit, formula=formula, description="test metric")


class TestEffectiveValue:
    def test_uses_ai_estimate_when_no_override(self):
        field = _make_field("hours", 40.0)
        assert field.effective_value == 40.0

    def test_uses_current_value_when_set(self):
        field = _make_field("hours", 40.0, current_value=50.0)
        assert field.effective_value == 50.0

    def test_current_value_zero_is_valid_override(self):
        field = _make_field("hours", 40.0, current_value=0.0)
        assert field.effective_value == 0.0


class TestOutputMetricCalculate:
    def test_simple_multiplication(self):
        fields = [_make_field("hours_per_week", 10.0), _make_field("weeks_per_year", 52.0)]
        metric = _make_metric("Annual Hours", "hours_per_week * weeks_per_year", unit="hours/year")
        assert metric.calculate(fields) == 520.0

    def test_uses_current_value_over_estimate(self):
        fields = [_make_field("rate", 100.0, current_value=150.0), _make_field("count", 5.0)]
        metric = _make_metric("Total", "rate * count")
        assert metric.calculate(fields) == 750.0

    def test_formula_error_returns_zero(self):
        fields = [_make_field("x", 10.0)]
        metric = _make_metric("Bad", "undefined_var * x")
        assert metric.calculate(fields) == 0.0

    def test_division_by_zero_returns_zero(self):
        fields = [_make_field("cost", 1000.0), _make_field("savings", 0.0)]
        metric = _make_metric("Payback", "cost / savings")
        assert metric.calculate(fields) == 0.0

    def test_complex_formula(self):
        fields = [
            _make_field("hours_saved", 5.0),
            _make_field("num_employees", 10.0),
            _make_field("hourly_rate", 50.0),
            _make_field("weeks", 52.0),
        ]
        metric = _make_metric("Annual Savings", "hours_saved * num_employees * hourly_rate * weeks")
        assert metric.calculate(fields) == 5.0 * 10.0 * 50.0 * 52.0

    def test_builtins_blocked(self):
        fields = [_make_field("x", 5.0)]
        metric = _make_metric("Bad", "__import__('os').getcwd()")
        assert metric.calculate(fields) == 0.0

    def test_safe_builtins_available(self):
        fields = [_make_field("a", 10.0), _make_field("b", 20.0)]
        metric = _make_metric("Max", "max(a, b)", unit="units")
        assert metric.calculate(fields) == 20.0


class TestFormatValue:
    def test_dollar_format(self):
        fields = [_make_field("x", 50000.0)]
        metric = _make_metric("Savings", "x", unit="$")
        assert metric.format_value(fields) == "$50,000"

    def test_percent_format(self):
        fields = [_make_field("x", 12.5)]
        metric = _make_metric("ROI", "x", unit="%")
        assert metric.format_value(fields) == "12.5%"


class TestProductConfig:
    def test_creates_with_defaults(self):
        product = ProductConfig(
            name="FlowSync",
            description="Workflow automation",
            value_drivers=[ValueDriver(name="Time Savings", description="Saves time")],
        )
        assert product.id
        assert product.created_at
        assert product.use_cases == []

    def test_model_roundtrip(self):
        product = ProductConfig(
            name="Test",
            description="desc",
            value_drivers=[ValueDriver(name="v", description="d")],
        )
        restored = ProductConfig.model_validate_json(product.model_dump_json())
        assert restored.name == product.name
        assert restored.id == product.id


class TestScenario:
    def test_creates_without_calculator(self):
        product = ProductConfig(
            name="P", description="d",
            value_drivers=[ValueDriver(name="v", description="d")]
        )
        customer = CustomerContext(
            company_name="Acme", industry="Tech", company_size="100",
            pain_points=["too slow"]
        )
        scenario = Scenario(name="Test", product_snapshot=product, customer=customer)
        assert scenario.calculator is None
        assert scenario.id
