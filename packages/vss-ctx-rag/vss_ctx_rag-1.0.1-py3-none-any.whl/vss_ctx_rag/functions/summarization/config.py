# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

"""Summarization configuration models."""

from pydantic import BaseModel, Field
from typing import Optional
from vss_ctx_rag.models.function_models import (
    FunctionModel,
)
from vss_ctx_rag.utils.globals import (
    DEFAULT_SUMM_TIMEOUT_SEC,
    DEFAULT_SUMM_RECURSION_LIMIT,
)


class SummarizationConfig(FunctionModel):
    class Prompts(BaseModel):
        caption: str
        caption_summarization: str
        summary_aggregation: str

    class SummarizationParams(BaseModel):
        batch_size: int = Field(default=6, ge=1)
        batch_max_concurrency: int = Field(default=20, ge=1)
        top_k: Optional[int] = Field(default=5, ge=1)
        prompts: "SummarizationConfig.Prompts"
        is_live: Optional[bool] = False
        summary_duration: Optional[int] = None
        chunk_size: Optional[int] = None
        uuid: Optional[str] = Field(default="default")
        timeout_sec: Optional[int] = Field(default=DEFAULT_SUMM_TIMEOUT_SEC)
        summ_rec_lim: Optional[int] = Field(default=DEFAULT_SUMM_RECURSION_LIMIT)

    params: SummarizationParams
