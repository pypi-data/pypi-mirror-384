import random
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from uncountable.integration.job import JobArguments, WebhookJob, register_job
from uncountable.types import (
    base_t,
    identifier_t,
    job_definition_t,
    recipe_links_t,
    set_recipe_outputs_t,
)


@dataclass(kw_only=True)
class PredictionsPayload:
    output_id: base_t.ObjectId
    recipe_ids: list[base_t.ObjectId]


@register_job
class PredictionsExample(WebhookJob[PredictionsPayload]):
    def run(
        self, args: JobArguments, payload: PredictionsPayload
    ) -> job_definition_t.JobResult:
        recipe_data = args.client.get_recipes_data(recipe_ids=payload.recipe_ids)
        formatted_datetime = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")

        for recipe in recipe_data.recipes:
            test_sample_name = f"Predictions Model ({formatted_datetime})"
            created_recipe_id = args.client.create_recipe(
                name=test_sample_name,
                material_family_id=1,
                workflow_id=1,
                definition_key=identifier_t.IdentifierKeyRefName(
                    ref_name="unc_test_sample"
                ),
            ).result_id
            args.client.set_recipe_outputs(
                output_data=[
                    set_recipe_outputs_t.RecipeOutputValue(
                        recipe_id=created_recipe_id,
                        output_id=payload.output_id,
                        experiment_num=1,
                        value_numeric=Decimal(random.random() * 10),
                    )
                ]
            )
            args.client.create_recipe_link(
                recipe_from_key=identifier_t.IdentifierKeyId(id=recipe.recipe_id),
                recipe_to_key=identifier_t.IdentifierKeyId(id=created_recipe_id),
                link_type=recipe_links_t.RecipeLinkType.CHILD,
                name=test_sample_name,
            )

        return job_definition_t.JobResult(success=True)

    @property
    def webhook_payload_type(self) -> type:
        return PredictionsPayload
