# SPDX-FileCopyrightText: Copyright (c) 2024-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""summarization.py: File contains Function class"""

import asyncio
import os
import time
from pathlib import Path

from langchain_community.callbacks import get_openai_callback
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables.base import RunnableSequence
from schema import Schema

from vss_ctx_rag.base.function import Function
from vss_ctx_rag.tools.health.rag_health import SummaryMetrics
from vss_ctx_rag.tools.storage.storage_tool import StorageTool
from vss_ctx_rag.utils.ctx_rag_batcher import Batcher
from vss_ctx_rag.utils.ctx_rag_logger import Metrics, logger
from vss_ctx_rag.utils.globals import (
    DEFAULT_SUMM_RECURSION_LIMIT,
    DEFAULT_SUMM_TIMEOUT_SEC,
    LLM_TOOL_NAME,
)
from vss_ctx_rag.utils.utils import (
    remove_think_tags,
    call_token_safe,
    add_timestamps_to_doc,
)
from vss_ctx_rag.functions.summarization.config import SummarizationConfig
from vss_ctx_rag.models.function_models import (
    register_function,
    register_function_config,
)


@register_function_config("batch_summarization")
class BatchSummarizationConfig(SummarizationConfig):
    pass


@register_function(config=BatchSummarizationConfig)
class BatchSummarization(Function):
    """Batch Summarization Function"""

    config: dict
    batch_prompt: str
    aggregation_prompt: str
    output_parser = StrOutputParser()
    batch_size: int
    curr_batch: str
    curr_batch_size: int
    batch_pipeline: RunnableSequence
    aggregation_pipeline: RunnableSequence
    db: StorageTool
    timeout: int = DEFAULT_SUMM_TIMEOUT_SEC  # seconds
    call_schema: Schema = Schema(
        {"start_index": int, "end_index": int}, ignore_extra_keys=True
    )
    metrics = SummaryMetrics()
    uuid: str

    def setup(self):
        # fixed params
        prompts = self.get_param("prompts")
        self.batch_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", prompts.get("caption_summarization")),
                ("user", "{input}"),
            ]
        )
        self.aggregation_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", prompts.get("summary_aggregation")),
                ("user", "{input}"),
            ]
        )
        self.output_parser = StrOutputParser()
        self.batch_pipeline = (
            self.batch_prompt
            | self.get_tool(LLM_TOOL_NAME)
            | self.output_parser
            | remove_think_tags
        )
        self.aggregation_pipeline = (
            self.aggregation_prompt
            | self.get_tool(LLM_TOOL_NAME)
            | self.output_parser
            | remove_think_tags
        )
        self.batch_size = self.get_param("batch_size")
        self.db = self.get_tool("db")
        self.timeout = self.get_param("timeout_sec", default=DEFAULT_SUMM_TIMEOUT_SEC)

        # working params
        self.batcher = Batcher(self.batch_size)
        self.recursion_limit = self.get_param(
            "summ_rec_lim", default=DEFAULT_SUMM_RECURSION_LIMIT
        )

        self.log_dir = os.environ.get("VIA_LOG_DIR", None)
        self.summary_start_time = None
        self.enable_summary = True

        self.uuid = self.get_param("uuid", default="default")

    async def _process_full_batch(self, batch):
        """Process a full batch immediately"""
        with Metrics(
            "Batch "
            + str(batch._batch_index)
            + " Summary IS LAST "
            + str(batch.as_list()[-1][2]["is_last"]),
            "pink",
        ):
            batch_summary = "."

            logger.info("Batch %d is full. Processing ...", batch._batch_index)
            try:
                with get_openai_callback() as cb:
                    batch_text = " ".join([doc for doc, _, _ in batch.as_list()])
                    batch_summary = await call_token_safe(
                        batch_text,
                        self.batch_pipeline,
                        self.recursion_limit,
                    )
            except Exception as e:
                logger.error(f"Error summarizing batch {batch._batch_index}: {e}")

            self.metrics.summary_tokens += cb.total_tokens
            self.metrics.summary_requests += cb.successful_requests

            chunk_indices = []
            doc_meta_sample = None
            for _, _, doc_meta in batch.as_list():
                if doc_meta_sample is None:
                    doc_meta_sample = doc_meta
                if "chunkIdx" in doc_meta and doc_meta["chunkIdx"] is not None:
                    chunk_indices.append(doc_meta["chunkIdx"])

            # Remove duplicates
            if chunk_indices:
                chunk_indices = list(set(chunk_indices))

            # get start and end times for the batch's caption_summary document
            min_start_pts = None
            max_end_pts = None
            min_start_ntp = None
            max_end_ntp = None
            min_start_ntp_float = None
            max_end_ntp_float = None
            for _, _, meta in batch.as_list():
                if "start_pts" in meta:
                    if min_start_pts is None:
                        min_start_pts = meta["start_pts"]
                    else:
                        min_start_pts = min(min_start_pts, meta["start_pts"])
                if "end_pts" in meta:
                    if max_end_pts is None:
                        max_end_pts = meta["end_pts"]
                    else:
                        max_end_pts = max(max_end_pts, meta["end_pts"])
                if "start_ntp" in meta:
                    if min_start_ntp is None:
                        min_start_ntp = meta["start_ntp"]
                    else:
                        min_start_ntp = min(min_start_ntp, meta["start_ntp"])
                if "end_ntp" in meta:
                    if max_end_ntp is None:
                        max_end_ntp = meta["end_ntp"]
                    else:
                        max_end_ntp = max(max_end_ntp, meta["end_ntp"])
                if "start_ntp_float" in meta:
                    if min_start_ntp_float is None:
                        min_start_ntp_float = meta["start_ntp_float"]
                    else:
                        min_start_ntp_float = min(
                            min_start_ntp_float, meta["start_ntp_float"]
                        )
                if "end_ntp_float" in meta:
                    if max_end_ntp_float is None:
                        max_end_ntp_float = meta["end_ntp_float"]
                    else:
                        max_end_ntp_float = max(
                            max_end_ntp_float, meta["end_ntp_float"]
                        )

            logger.info(f"Min start pts: {min_start_pts}, Max end pts: {max_end_pts}")
            logger.info(f"Min start ntp: {min_start_ntp}, Max end ntp: {max_end_ntp}")
            logger.info(
                f"Min start ntp float: {min_start_ntp_float}, Max end ntp float: {max_end_ntp_float}"
            )

            logger.info("Batch %d summary: %s", batch._batch_index, batch_summary)
            logger.info(
                "Total Tokens: %s, "
                "Prompt Tokens: %s, "
                "Completion Tokens: %s, "
                "Successful Requests: %s, "
                "Total Cost (USD): $%s"
                % (
                    cb.total_tokens,
                    cb.prompt_tokens,
                    cb.completion_tokens,
                    cb.successful_requests,
                    cb.total_cost,
                ),
            )
        try:
            empty_doc_meta = {}
            if doc_meta_sample:
                empty_doc_meta = {
                    key: type(value)() for key, value in doc_meta_sample.items()
                }

            batch_meta = {
                **empty_doc_meta,
                "chunkIdx": -1,
                "batch_i": batch._batch_index,
                "doc_type": "caption_summary",
                "uuid": self.uuid,
                "camera_id": "default",
            }
            if min_start_ntp:
                batch_meta["start_ntp"] = min_start_ntp
            if max_end_ntp:
                batch_meta["end_ntp"] = max_end_ntp
            if min_start_ntp_float:
                batch_meta["start_ntp_float"] = min_start_ntp_float
            if max_end_ntp_float:
                batch_meta["end_ntp_float"] = max_end_ntp_float
            if min_start_pts:
                batch_meta["start_pts"] = min_start_pts
            if max_end_pts:
                batch_meta["end_pts"] = max_end_pts

            # Add the chunk indices if any exist
            if chunk_indices:
                batch_meta["linked_summary_chunks"] = chunk_indices
            # TODO: Use the async method once https://github.com/langchain-ai/langchain-milvus/pull/29 is released
            # await self.db.aadd_summary(summary=batch_summary, metadata=batch_meta)
            logger.debug(f"Metadata being added: {batch_meta}")
            self.db.add_summary(summary=batch_summary, metadata=batch_meta)

        except Exception as e:
            logger.error(f"Error adding summary to database: {e}")

    async def acall(self, state: dict):
        """batch summarization function call

        Args:
            state (dict): should validate against call_schema
        Returns:
            dict: the state dict will contain result:
            {
                # ...
                # The following key is overwritten or added
                "result" : "summary",
                "error_code": "Error String" # Optional
            }
        """
        try:
            logger.info(f"Batch Summarization Acall: {state}")
            with Metrics("OffBatchSumm/Acall", "blue"):
                batches = []
                self.call_schema.validate(state)
                stop_time = time.time() + self.timeout
                target_start_batch_index = self.batcher.get_batch_index(
                    state["start_index"]
                )
                target_end_batch_index = self.batcher.get_batch_index(
                    state["end_index"]
                )
                logger.info(f"Target Batch Start: {target_start_batch_index}")
                logger.info(f"Target Batch End: {target_end_batch_index}")
                if target_end_batch_index == -1:
                    max_batch_index = await self.db.aget_max_batch_index(self.uuid)
                    target_end_batch_index = max_batch_index
                    logger.debug(
                        f"Updated target_end_batch_index to {target_end_batch_index}"
                    )

                while time.time() < stop_time:
                    batches = await self.db.aget_text_data(
                        target_start_batch_index, target_end_batch_index, self.uuid
                    )
                    # Sort batches by batch_i field
                    batches.sort(key=lambda x: x["batch_i"])
                    logger.debug(
                        f"Batches Fetched: {[{k: v for k, v in batch.items() if k != 'vector'} for batch in batches]}"
                    )
                    logger.info(f"Number of Batches Fetched: {len(batches)}")
                    # Need ceiling of results/batch_size for correct batch size target end
                    if (
                        len(batches)
                        == target_end_batch_index - target_start_batch_index + 1
                    ):
                        logger.info(
                            f"Need {target_end_batch_index - target_start_batch_index + 1} batches. Moving forward."
                        )
                        break
                    elif (
                        len(batches)
                        >= target_end_batch_index - target_start_batch_index + 1
                    ):
                        logger.info(
                            f"Found {len(batches)} batches. Taking first {target_end_batch_index - target_start_batch_index + 1} batches."
                        )
                        batches = batches[
                            : target_end_batch_index - target_start_batch_index + 1
                        ]
                        break
                    else:
                        logger.info(
                            f"Need {target_end_batch_index - target_start_batch_index + 1} batches. Waiting ..."
                        )
                        await asyncio.sleep(1)
                        continue

                # Sort batches by batch_i field
                batches.sort(key=lambda x: x["batch_i"])
                logger.info(f"Number of Batches Fetched: {len(batches)}")
                batches = [
                    {k: v for k, v in batch.items() if k == "text"} for batch in batches
                ]

                if len(batches) == 0:
                    state["result"] = ""
                    state["error_code"] = "No batch summaries found"
                    logger.error("No batch summaries found")
                elif len(batches) > 0:
                    with Metrics("summ/acall/batch-aggregation-summary", "pink") as bas:
                        with get_openai_callback() as cb:
                            result = await call_token_safe(
                                batches, self.aggregation_pipeline, self.recursion_limit
                            )
                            state["result"] = result
                        logger.info("Summary Aggregation Done")
                        self.metrics.aggregation_tokens = cb.total_tokens
                        logger.info(
                            "Total Tokens: %s, "
                            "Prompt Tokens: %s, "
                            "Completion Tokens: %s, "
                            "Successful Requests: %s, "
                            "Total Cost (USD): $%s"
                            % (
                                cb.total_tokens,
                                cb.prompt_tokens,
                                cb.completion_tokens,
                                cb.successful_requests,
                                cb.total_cost,
                            ),
                        )
                    self.metrics.aggregation_latency = bas.execution_time
            if self.log_dir:
                log_path = Path(self.log_dir).joinpath("summary_metrics.json")
                self.metrics.dump_json(log_path.absolute())
        except Exception as e:
            logger.error(f"Error in batch summarization: {e}")
            state["error_code"] = f"{e}"
            raise e
        return state

    async def aprocess_doc(self, doc: str, doc_i: int, doc_meta: dict):
        try:
            logger.info("Adding doc %d", doc_i)
            doc_meta.setdefault("is_first", False)
            doc_meta.setdefault("is_last", False)

            with Metrics("summ/aprocess_doc", "red") as bs:
                # Add timestamps to document using utility function
                doc = add_timestamps_to_doc(doc, doc_meta)
                doc_meta["batch_i"] = doc_i // self.batch_size
                batch = self.batcher.add_doc(doc, doc_i, doc_meta)
                if batch.is_full():
                    # Process the batch immediately when full
                    await asyncio.create_task(self._process_full_batch(batch))
            if self.summary_start_time is None:
                self.summary_start_time = bs.start_time
            self.metrics.summary_latency = bs.end_time - self.summary_start_time
        except Exception as e:
            logger.error(e)

    async def areset(self, state: dict):
        # TODO: use async method for drop data
        self.db.reset(state)
        self.summary_start_time = None
        self.batcher.flush()
        self.metrics.reset()
        await asyncio.sleep(0.001)
