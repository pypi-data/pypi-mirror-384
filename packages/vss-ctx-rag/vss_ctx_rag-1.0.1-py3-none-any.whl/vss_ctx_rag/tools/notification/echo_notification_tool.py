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

from vss_ctx_rag.tools.notification.notification_tool import NotificationTool
from vss_ctx_rag.utils.ctx_rag_logger import logger
from vss_ctx_rag.models.tool_models import register_tool_config, register_tool
from vss_ctx_rag.models.tool_models import ToolBaseModel


@register_tool_config("echo_notifier")
class EchoNotificationToolConfig(ToolBaseModel):
    """Alert SSE Notifier configuration."""

    pass


@register_tool(config=EchoNotificationToolConfig)
class EchoNotificationTool(NotificationTool):
    """Tool for printing notification on the terminal.
    Implements NotificationTool class
    """

    def __init__(self, name="echo_notifier", config=None, tools=None) -> None:
        super().__init__(name, config, tools)
        self.update_tool(self.config, tools)

    def update_tool(self, config, tools=None):
        self.config = config

    async def notify(self, title: str, message: str, metadata: dict):
        try:
            logger.info("==================Notification==================")
            logger.info(f"Notification: {title}")
            logger.info(f"Message: {message}")
            logger.info(f"Metadata: {metadata}")
            logger.info("================================================")
            return True
        except Exception:
            logger.error("Echo Notification Failed")
            return False
