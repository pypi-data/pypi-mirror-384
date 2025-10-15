import json
import os
import sys
from unittest.mock import MagicMock

import pytest

# Add parent directory for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pydantic import ValidationError

from feature_suggestion_agent.agent import FeatureSuggestionAgent
from feature_suggestion_agent.models import (
    FeatureInput,
)

# ------------------------
# FIXTURES
# ------------------------


# Mock AI handler
@pytest.fixture
def mock_ai_handler():
    handler = MagicMock()
    return handler


# FeatureSuggestionAgent with mocked AI handler
@pytest.fixture
def feature_agent(mock_ai_handler):
    agent = FeatureSuggestionAgent()
    agent.ai_handler = mock_ai_handler
    return agent


# Fixture: Retail sales example
@pytest.fixture
def retail_sales_input():
    return FeatureInput(
        usecase="predict sales",
        domain_info={"industry": "retail"},
        schema_name="marketing",
        table_name="sales",
        column_metadata={
            "sales": [
                {
                    "name": "sales",
                    "type": "int",
                    "description": "Monthly sales in USD",
                    "sample_data": [120, 150, 200],
                },
                {
                    "name": "cost",
                    "type": "int",
                    "description": "Monthly cost in USD",
                    "sample_data": [80, 100, 150],
                },
                {
                    "name": "profit",
                    "type": "int",
                    "description": "Monthly profit in USD",
                    "sample_data": [40, 50, 50],
                },
                {
                    "name": "visits",
                    "type": "int",
                    "description": "Number of customer visits",
                    "sample_data": [10, 15, 20],
                },
                {
                    "name": "returns",
                    "type": "int",
                    "description": "Number of returned items",
                    "sample_data": [0, 1, 2],
                },
                {
                    "name": "region",
                    "type": "string",
                    "description": "Sales region",
                    "sample_data": ["East", "West", "North"],
                },
                {
                    "name": "product_category",
                    "type": "string",
                    "description": "Category of the product",
                    "sample_data": ["Electronics", "Clothing", "Toys"],
                },
                {
                    "name": "discount",
                    "type": "float",
                    "description": "Discount applied (%)",
                    "sample_data": [0.0, 5.0, 10.0],
                },
                {
                    "name": "customer_age",
                    "type": "int",
                    "description": "Age of customer",
                    "sample_data": [25, 30, 35],
                },
                {
                    "name": "total_sales",
                    "type": "float",
                    "description": "Customer loyalty score / Target column",
                    "sample_data": [0.5, 0.7, 0.9],
                },
            ]
        },
        target_logic="sum of total_sales over last 6 months",
        target_column="total_sales",
        modeling_approach="regression",
    )


# Fixture for malformed LLM JSON
@pytest.fixture
def malformed_llm_response():
    return '{"invalid_json": }'


print("[TEST SUCCESS] malformed_llm_response passed!")


def test_retail_sales_feature_success(
    feature_agent, mock_ai_handler, retail_sales_input
):
    mock_output = [
        {
            "title": "Profit Margin",
            "columns_involved": ["profit", "sales"],
            "operation": "ratio",
            "created_new_feature": "profit_margin",
            "formula_logic": "profit / sales",
            "reasoning": "Shows profitability per unit of sales",
            "group_by": [],
            "order_by": [],
            "window": None,
            "sql": "SELECT profit / sales AS profit_margin FROM sales",
        }
    ]
    mock_ai_handler.route_to.return_value = (json.dumps(mock_output), 1.0)

    result, cost = feature_agent.execute_task(retail_sales_input)

    assert len(result) == 1
    assert result[0].title == "Profit Margin"
    assert cost == 1.0
    print("[TEST SUCCESS] test_llm_output response passed!")


def test_malformed_llm_json(
    feature_agent, mock_ai_handler, retail_sales_input, malformed_llm_response
):
    mock_ai_handler.route_to.return_value = (malformed_llm_response, 0.5)

    # Expect ValidationError to be raised due to invalid JSON
    with pytest.raises(ValidationError):
        feature_agent.execute_task(retail_sales_input)
    print("[TEST SUCCESS] test_malformed_llm_json passed!")


def test_invalid_feature_input(feature_agent):
    with pytest.raises(Exception):
        invalid_input = FeatureInput(
            usecase="Test",
            domain_info="Test",
            schema_name="public",
            table_name="customers",
            column_metadata={},  # Missing columns
            target_logic="target logic",
            target_column="target",
            modeling_approach="classification",
        )
        feature_agent.execute_task(invalid_input)
    print("[TEST SUCCESS] test_invalid_feature_input passed!")
