import json
import re
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, model_validator


class FeatureOutput(BaseModel):
    title: str = Field(..., description="A concise, descriptive name for the feature.")

    columns_involved: List[str] = Field(
        ..., description="List of all source columns used for this feature."
    )

    operation: str = Field(
        ..., description="The specific operation name used from the allowed list."
    )

    created_new_feature: str = Field(
        ..., description="The name of the new feature column."
    )

    formula_logic: str = Field(
        ...,
        description="A human-readable description or mathematical formula of how the feature is calculated.",
    )

    reasoning: str = Field(
        ..., description="Explain WHY this feature is useful for the model, 1-2 lines."
    )

    group_by: Optional[List[str]] = Field(
        default_factory=list, description="Columns for aggregation/partition."
    )

    order_by: Optional[List[str]] = Field(
        default_factory=list, description="Columns to sort by for window functions."
    )

    window: Optional[int] = Field(
        None, description="Window size for rolling or lag operations."
    )

    sql: str = Field(
        ...,
        description="SQL query to generate this feature. Use column names as provided.",
    )


class FeaturesListModel(BaseModel):
    features: List[FeatureOutput]

    @model_validator(mode="before")
    @classmethod
    def parse_llm_output(cls, raw_llm_output: Any) -> Any:
        """
        Accepts raw LLM output (str or list of dicts) and ensures we get a list of dicts.
        Removes markdown fences if needed and parses JSON automatically.
        """
        if isinstance(raw_llm_output, str):
            cleaned = raw_llm_output.strip()
            # Remove code fences
            if cleaned.startswith("```"):
                cleaned = re.sub(
                    r"^```(?:json)?", "", cleaned, flags=re.IGNORECASE
                ).strip()
                cleaned = re.sub(r"```$", "", cleaned).strip()
            try:
                raw_llm_output = json.loads(cleaned)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON from LLM output: {e}")

        if not isinstance(raw_llm_output, list):
            raise ValueError("LLM output must be a list of feature dicts")

        return {"features": raw_llm_output}


class FeatureInput(BaseModel):
    usecase: str
    domain_info: Union[str, Dict[str, Any]]
    schema_name: str
    table_name: str
    column_metadata: Dict[str, List[Dict[str, Any]]]
    target_logic: str
    target_column: str
    modeling_approach: str
