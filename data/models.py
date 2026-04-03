from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


class ValueDriver(BaseModel):
    name: str
    description: str


class ProductConfig(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    value_drivers: list[ValueDriver]
    use_cases: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CustomerContext(BaseModel):
    company_name: str
    industry: str
    company_size: str
    pain_points: list[str]
    notes: str = ""


class CalculatorInputField(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    key: str  # snake_case Python identifier, used as variable in output metric formulas
    label: str
    unit: str
    description: str
    ai_estimate: float
    current_value: Optional[float] = None  # SA override; None means use ai_estimate
    value_driver: str  # name of the value driver this field feeds into

    @property
    def effective_value(self) -> float:
        return self.current_value if self.current_value is not None else self.ai_estimate


class OutputMetric(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    label: str
    unit: str
    description: str
    formula: str  # Python arithmetic expression using CalculatorInputField.key as variables

    def calculate(self, fields: list[CalculatorInputField]) -> float:
        variables = {f.key: f.effective_value for f in fields}
        safe_env = {
            "__builtins__": {},
            "max": max,
            "min": min,
            "abs": abs,
            "round": round,
        }
        try:
            return float(eval(self.formula, safe_env, variables))
        except Exception:
            return 0.0

    def format_value(self, fields: list[CalculatorInputField]) -> str:
        value = self.calculate(fields)
        unit = self.unit.strip()
        if unit == "$":
            return f"${value:,.0f}"
        if unit.startswith("$"):
            return f"${value:,.0f} {unit[1:].strip()}"
        if unit == "%":
            return f"{value:.1f}%"
        if "month" in unit.lower() and value < 24:
            return f"{value:.1f} {unit}"
        return f"{value:,.1f} {unit}"


class Calculator(BaseModel):
    fields: list[CalculatorInputField]
    output_metrics: list[OutputMetric]
    rationale: str


class Scenario(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    notes: str = ""  # SA's freeform notes about this calculator
    product_snapshot: ProductConfig  # frozen copy with any ad-hoc edits applied
    source_product_id: Optional[str] = None  # reference back to the library product
    customer: CustomerContext
    calculator: Optional[Calculator] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
