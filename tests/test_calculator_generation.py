"""Tests for calculator generation — LLM calls are mocked."""
from unittest.mock import MagicMock, patch

import pytest

from data.models import CustomerContext, ProductConfig, ValueDriver
from features.calculator_generation import _AICalculatorResponse, _AIInputField, _AIOutputMetric


def _make_product() -> ProductConfig:
    return ProductConfig(
        name="FlowSync",
        description="Workflow automation platform that eliminates manual data entry.",
        value_drivers=[
            ValueDriver(name="Time Savings", description="Automates repetitive manual tasks"),
            ValueDriver(name="Error Reduction", description="Eliminates data entry errors"),
        ],
        use_cases=["Invoice reconciliation", "Inventory sync"],
    )


def _make_customer() -> CustomerContext:
    return CustomerContext(
        company_name="Meridian Financial",
        industry="Financial Services",
        company_size="500 employees",
        pain_points=[
            "3 analysts spend 60% of time on manual reconciliation",
            "Error rate in data entry causes downstream rework",
        ],
        notes="Considering a Q3 rollout",
    )


def _make_ai_response() -> _AICalculatorResponse:
    return _AICalculatorResponse(
        fields=[
            _AIInputField(
                key="analysts",
                label="Number of analysts doing manual work",
                unit="employees",
                description="FTEs spending time on reconciliation",
                ai_estimate=3.0,
                value_driver="Time Savings",
            ),
            _AIInputField(
                key="hours_per_week",
                label="Hours per analyst per week on manual tasks",
                unit="hours/week",
                description="Time each analyst spends on manual reconciliation",
                ai_estimate=24.0,
                value_driver="Time Savings",
            ),
            _AIInputField(
                key="hourly_rate",
                label="Average analyst hourly cost",
                unit="$/hour",
                description="Fully-loaded cost per analyst hour",
                ai_estimate=75.0,
                value_driver="Time Savings",
            ),
            _AIInputField(
                key="error_rate_pct",
                label="Current data entry error rate",
                unit="%",
                description="Percentage of entries requiring rework",
                ai_estimate=5.0,
                value_driver="Error Reduction",
            ),
        ],
        output_metrics=[
            _AIOutputMetric(
                label="Annual Time Saved",
                unit="hours/year",
                description="Total analyst hours freed per year",
                formula="analysts * hours_per_week * 52",
            ),
            _AIOutputMetric(
                label="Annual Cost Savings",
                unit="$",
                description="Cost of analyst time recovered",
                formula="analysts * hours_per_week * 52 * hourly_rate",
            ),
        ],
        rationale="These metrics directly address the stated pain around manual reconciliation.",
    )


class TestGenerateCalculator:
    def test_returns_calculator_with_fields_and_metrics(self):
        from features.calculator_generation import generate_calculator

        mock_provider = MagicMock()
        mock_provider.complete_structured.return_value = (_make_ai_response(), MagicMock())

        with patch("features.calculator_generation.router") as mock_router:
            mock_router.get_provider.return_value = mock_provider
            result = generate_calculator(_make_product(), _make_customer())

        assert len(result.fields) == 4
        assert len(result.output_metrics) == 2
        assert result.rationale

    def test_field_keys_and_estimates_preserved(self):
        from features.calculator_generation import generate_calculator

        mock_provider = MagicMock()
        mock_provider.complete_structured.return_value = (_make_ai_response(), MagicMock())

        with patch("features.calculator_generation.router") as mock_router:
            mock_router.get_provider.return_value = mock_provider
            result = generate_calculator(_make_product(), _make_customer())

        keys = {f.key for f in result.fields}
        assert "analysts" in keys
        assert "hours_per_week" in keys

        analysts_field = next(f for f in result.fields if f.key == "analysts")
        assert analysts_field.ai_estimate == 3.0
        assert analysts_field.current_value is None

    def test_formulas_calculate_correctly(self):
        from features.calculator_generation import generate_calculator

        mock_provider = MagicMock()
        mock_provider.complete_structured.return_value = (_make_ai_response(), MagicMock())

        with patch("features.calculator_generation.router") as mock_router:
            mock_router.get_provider.return_value = mock_provider
            result = generate_calculator(_make_product(), _make_customer())

        time_metric = next(m for m in result.output_metrics if "Time" in m.label)
        # analysts=3, hours_per_week=24, 52 weeks → 3 * 24 * 52 = 3744
        assert time_metric.calculate(result.fields) == 3 * 24 * 52

    def test_uses_quality_provider(self):
        from features.calculator_generation import generate_calculator

        mock_provider = MagicMock()
        mock_provider.complete_structured.return_value = (_make_ai_response(), MagicMock())

        with patch("features.calculator_generation.router") as mock_router:
            mock_router.get_provider.return_value = mock_provider
            generate_calculator(_make_product(), _make_customer())

        mock_router.get_provider.assert_called_once_with(quality_required=True)
