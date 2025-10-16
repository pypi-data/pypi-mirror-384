import logging
import sys
from typing import Optional

from pydantic import ValidationError
from sfn_blueprint import Context, SFNAIHandler, accum_dicts, self_correcting_sql

from feature_suggestion_agent.config import FeatureCreationConfig
from feature_suggestion_agent.constants import FeatureSuggestionPrompts
from feature_suggestion_agent.models import (
    FeatureInput,
    FeatureOutputSqlQueryValidation,
    FeaturesListModel,
)


class FeatureSuggestionAgent:

    def __init__(self, config: Optional[FeatureCreationConfig] = None):
        """
        Initialize the agent with configuration.

        Args:
            config: Optional FeatureCreationConfig instance. If not provided, a default will be used.
        """
        # Initialize configuration
        self.config = config or FeatureCreationConfig()
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:  # Only add handlers if none exist
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
            )
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

        # Initialize sfn_blueprint components
        self.ai_handler = SFNAIHandler()

    def __call__(self, validated_input: FeatureInput):
        return self.execute_task(validated_input)

    def execute_task(self, validated_input):
        # extract inputs from validated_input
        usecase = validated_input.usecase
        domain_info = validated_input.domain_info
        column_metadata = validated_input.column_metadata
        target_logic = validated_input.target_logic
        target_column = validated_input.target_column
        modeling_approach = validated_input.modeling_approach
        table_name = validated_input.table_name
        schema_name = validated_input.schema_name

        context = f"### Database Summary\n\n**Schema:** {schema_name}\n **Table:** {table_name}\n\n#### Column Statistics\n{column_metadata}"

        instance = FeatureSuggestionPrompts()
        system_prompt = FeatureSuggestionPrompts.feature_suggestion_system_prompt()
        user_prompt = instance.feature_suggestion_user_prompt(
            usecase,
            domain_info,
            schema_name,
            table_name,
            column_metadata,
            target_logic,
            target_column,
            modeling_approach,
        )
        llm_response, cost = self.llm_call(system_prompt, user_prompt)
        parsed_response = self.llm_response_parser(llm_response)

        verify_output = []
        if validated_input.sql_query_validation:
            verify_output, sql_cost = self.validate_sql_query(
                validated_input, parsed_response, context
            )
            cost = accum_dicts([cost, sql_cost])

        return parsed_response, cost, verify_output

    def validate_sql_query(self, validated_input, parsed_response, context):
        verify_output = []
        total_cost = []
        with Context(
            AI_PROVIDER=self.config.ai_provider,
            AI_MODEL=self.config.model_name,
            AI_TEMPERATURE=self.config.temperature,
            AI_MAX_TOKENS=self.config.max_tokens,
            DEBUG=1,
        ):
            for feature in parsed_response:
                success, correct_query, result, message, cost = self_correcting_sql(
                    session=validated_input.session,
                    sql_query=feature.sql,
                    dialect=validated_input.sql_dialect,
                    context=context,
                )

                verify_output.append(
                    FeatureOutputSqlQueryValidation(
                        title=feature.title,
                        original_sql=feature.sql,
                        corrected_sql=correct_query,
                        is_valid=success,
                        validation_message=message,
                    )
                )

                total_cost.append(cost)

        return verify_output, accum_dicts(total_cost)

    def llm_call(self, system_prompt, user_prompt):

        try:
            response, cost = self.ai_handler.route_to(
                llm_provider=self.config.ai_provider,
                configuration={
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": self.config.temperature,
                    "max_tokens": self.config.max_tokens,
                },
                model=self.config.model_name,
            )

            return response, cost

        except Exception as e:
            self.logger.error(f"Error in response: {str(e)}")
            raise e

    def llm_response_parser(self, llm_response):
        """
        Parses LLM output and returns a list of FeatureOutput objects.
        Supports raw JSON strings (with or without code fences) or already-parsed lists of dicts.
        """

        try:

            # Validate each dictionary as FeatureOutput
            features_model = FeaturesListModel.model_validate(llm_response)

            self.logger.info("LLM parsed output is valid!")
            return features_model.features

        except (ValidationError, TypeError, KeyError) as e:
            self.logger.error(f"Error in parsing LLM response: {str(e)}")
            raise e
