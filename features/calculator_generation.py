"""Generate a customized ROI calculator from product config + customer context."""
from __future__ import annotations

from pydantic import BaseModel

from data.models import (
    Calculator,
    CalculatorInputField,
    CustomerContext,
    OutputMetric,
    ProductConfig,
)
from llm.router import router


# ---------------------------------------------------------------------------
# AI response schema (intermediate — converted to full models after generation)
# ---------------------------------------------------------------------------

class _AIInputField(BaseModel):
    key: str           # snake_case Python identifier used in formulas
    label: str         # human-readable label
    unit: str          # e.g. "hours/week", "employees", "$"
    description: str   # why this input matters for ROI
    ai_estimate: float # realistic industry-based estimate
    value_driver: str  # which value driver this field feeds


class _AIOutputMetric(BaseModel):
    label: str        # e.g. "Annual Cost Savings"
    unit: str         # e.g. "$", "hours/year", "months"
    description: str  # what this metric represents
    formula: str      # Python arithmetic expression using field keys as variables


class _AICalculatorResponse(BaseModel):
    fields: list[_AIInputField]
    output_metrics: list[_AIOutputMetric]
    rationale: str  # brief explanation of why these metrics were chosen


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

_SYSTEM = """\
You are an expert business value consultant and solutions architect. Your job is to build \
customized ROI calculators that quantify the value of a specific software product for a \
specific customer situation.

Given a product's value drivers and a customer's context, you will:
1. Identify the most impactful metrics to quantify for this customer
2. Define 4-8 calculator input fields tied to those metrics
3. Define 2-5 output metrics with precise arithmetic formulas
4. Pre-fill each input field with a realistic industry-based estimate

Rules:
- Field keys MUST be valid Python identifiers (snake_case, no spaces, no hyphens)
- Output metric formulas MUST be valid Python arithmetic expressions using ONLY the field \
keys you define — no undefined variables
- AI estimates should reflect realistic benchmarks for the given industry and company size
- Be specific and concrete — avoid vague or generic metrics
- Match the output metrics directly to the customer's stated pain points
- Include at least one time-based metric and one financial metric in the output\
"""


def _build_prompt(product: ProductConfig, customer: CustomerContext) -> str:
    drivers = "\n".join(
        f"  - {vd.name}: {vd.description}" for vd in product.value_drivers
    )
    pain_points = "\n".join(f"  - {p}" for p in customer.pain_points)
    use_cases = ", ".join(product.use_cases) if product.use_cases else "not specified"

    return f"""\
Product: {product.name}
Description: {product.description}
Use cases: {use_cases}

Value Drivers:
{drivers}

Customer Context:
  Company: {customer.company_name}
  Industry: {customer.industry}
  Size: {customer.company_size}
  Pain Points:
{pain_points}
  Additional Notes: {customer.notes or "none"}

Build a customized ROI calculator for this product/customer combination. \
Be specific to this customer's industry and pain points.\
"""


# ---------------------------------------------------------------------------
# Public function
# ---------------------------------------------------------------------------

def generate_calculator(product: ProductConfig, customer: CustomerContext) -> Calculator:
    """Call the LLM to generate a Calculator for the given product + customer."""
    provider = router.get_provider(quality_required=True)
    prompt = _build_prompt(product, customer)

    ai_response, _ = provider.complete_structured(
        system=_SYSTEM,
        user=prompt,
        schema=_AICalculatorResponse,
        temperature=0.2,
    )

    fields = [
        CalculatorInputField(
            key=f.key,
            label=f.label,
            unit=f.unit,
            description=f.description,
            ai_estimate=f.ai_estimate,
            value_driver=f.value_driver,
        )
        for f in ai_response.fields
    ]

    output_metrics = [
        OutputMetric(
            label=m.label,
            unit=m.unit,
            description=m.description,
            formula=m.formula,
        )
        for m in ai_response.output_metrics
    ]

    return Calculator(
        fields=fields,
        output_metrics=output_metrics,
        rationale=ai_response.rationale,
    )
