"""
Polls SkorplandGPT_ManagedObjectTable to check if the batch job is complete, and if the cost has been tracked.
"""

from skorplandgpt._uuid import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional, cast

from skorplandgpt._logging import verbose_proxy_logger

if TYPE_CHECKING:
    from skorplandgpt.proxy.utils import PrismaClient, ProxyLogging
    from skorplandgpt.router import Router


class CheckBatchCost:
    def __init__(
        self,
        proxy_logging_obj: "ProxyLogging",
        prisma_client: "PrismaClient",
        llm_router: "Router",
    ):
        from skorplandgpt.proxy.utils import PrismaClient, ProxyLogging
        from skorplandgpt.router import Router

        self.proxy_logging_obj: ProxyLogging = proxy_logging_obj
        self.prisma_client: PrismaClient = prisma_client
        self.llm_router: Router = llm_router

    async def check_batch_cost(self):
        """
        Check if the batch JOB has been tracked.
        - get all status="validating" and file_purpose="batch" jobs
        - check if batch is now complete
        - if not, return False
        - if so, return True
        """
        from skorplandgpt_enterprise.proxy.hooks.managed_files import (
            _PROXY_SkorplandGPTManagedFiles,
        )

        from skorplandgpt.batches.batch_utils import (
            _get_file_content_as_dictionary,
            calculate_batch_cost_and_usage,
        )
        from skorplandgpt.skorplandgpt_core_utils.get_llm_provider_logic import get_llm_provider
        from skorplandgpt.skorplandgpt_core_utils.skorplandgpt_logging import Logging as SkorplandGPTLogging
        from skorplandgpt.proxy.openai_files_endpoints.common_utils import (
            _is_base64_encoded_unified_file_id,
            get_batch_id_from_unified_batch_id,
            get_model_id_from_unified_batch_id,
        )

        jobs = await self.prisma_client.db.skorplandgpt_managedobjecttable.find_many(
            where={
                "status": "validating",
                "file_purpose": "batch",
            }
        )

        completed_jobs = []

        for job in jobs:
            # get the model from the job
            unified_object_id = job.unified_object_id
            decoded_unified_object_id = _is_base64_encoded_unified_file_id(
                unified_object_id
            )
            if not decoded_unified_object_id:
                verbose_proxy_logger.info(
                    f"Skipping job {unified_object_id} because it is not a valid unified object id"
                )
                continue
            else:
                unified_object_id = decoded_unified_object_id

            model_id = get_model_id_from_unified_batch_id(unified_object_id)
            batch_id = get_batch_id_from_unified_batch_id(unified_object_id)

            if model_id is None:
                verbose_proxy_logger.info(
                    f"Skipping job {unified_object_id} because it is not a valid model id"
                )
                continue

            verbose_proxy_logger.info(
                f"Querying model ID: {model_id} for cost and usage of batch ID: {batch_id}"
            )

            try:
                response = await self.llm_router.aretrieve_batch(
                    model=model_id,
                    batch_id=batch_id,
                    skorplandgpt_metadata={
                        "user_api_key_user_id": job.created_by or "default-user-id",
                        "batch_ignore_default_logging": True,
                    },
                )
            except Exception as e:
                verbose_proxy_logger.info(
                    f"Skipping job {unified_object_id} because of error querying model ID: {model_id} for cost and usage of batch ID: {batch_id}: {e}"
                )
                continue

            ## RETRIEVE THE BATCH JOB OUTPUT FILE
            managed_files_obj = cast(
                Optional[_PROXY_SkorplandGPTManagedFiles],
                self.proxy_logging_obj.get_proxy_hook("managed_files"),
            )
            if (
                response.status == "completed"
                and response.output_file_id is not None
                and managed_files_obj is not None
            ):
                verbose_proxy_logger.info(
                    f"Batch ID: {batch_id} is complete, tracking cost and usage"
                )
                # track cost
                model_file_id_mapping = {
                    response.output_file_id: {model_id: response.output_file_id}
                }
                _file_content = await managed_files_obj.afile_content(
                    file_id=response.output_file_id,
                    skorplandgpt_parent_otel_span=None,
                    llm_router=self.llm_router,
                    model_file_id_mapping=model_file_id_mapping,
                )

                file_content_as_dict = _get_file_content_as_dictionary(
                    _file_content.content
                )

                deployment_info = self.llm_router.get_deployment(model_id=model_id)
                if deployment_info is None:
                    verbose_proxy_logger.info(
                        f"Skipping job {unified_object_id} because it is not a valid deployment info"
                    )
                    continue
                custom_llm_provider = deployment_info.skorplandgpt_params.custom_llm_provider
                skorplandgpt_model_name = deployment_info.skorplandgpt_params.model

                _, llm_provider, _, _ = get_llm_provider(
                    model=skorplandgpt_model_name,
                    custom_llm_provider=custom_llm_provider,
                )

                batch_cost, batch_usage, batch_models = (
                    await calculate_batch_cost_and_usage(
                        file_content_dictionary=file_content_as_dict,
                        custom_llm_provider=llm_provider,  # type: ignore
                    )
                )

                logging_obj = SkorplandGPTLogging(
                    model=batch_models[0],
                    messages=[{"role": "user", "content": "<retrieve_batch>"}],
                    stream=False,
                    call_type="aretrieve_batch",
                    start_time=datetime.now(),
                    skorplandgpt_call_id=str(uuid.uuid4()),
                    function_id=str(uuid.uuid4()),
                )

                logging_obj.update_environment_variables(
                    skorplandgpt_params={
                        "metadata": {
                            "user_api_key_user_id": job.created_by or "default-user-id",
                        }
                    },
                    optional_params={},
                )

                await logging_obj.async_success_handler(
                    result=response,
                    batch_cost=batch_cost,
                    batch_usage=batch_usage,
                    batch_models=batch_models,
                )

                # mark the job as complete
                completed_jobs.append(job)

            if len(completed_jobs) > 0:
                # mark the jobs as complete
                await self.prisma_client.db.skorplandgpt_managedobjecttable.update_many(
                    where={"id": {"in": [job.id for job in completed_jobs]}},
                    data={"status": "complete"},
                )
