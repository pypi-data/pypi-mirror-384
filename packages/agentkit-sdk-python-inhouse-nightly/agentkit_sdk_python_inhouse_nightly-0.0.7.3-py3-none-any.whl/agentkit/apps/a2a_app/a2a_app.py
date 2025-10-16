# Copyright (c) 2025 Beijing Volcano Engine Technology Co., Ltd. and/or its affiliates.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import time
from typing import Callable, override

import uvicorn
from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.apps import A2AStarletteApplication
from a2a.server.events.event_queue import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.tasks.task_store import TaskStore
from a2a.types import AgentCard

from agentkit.apps.base_app import BaseAgentkitApp
from agentkit.apps.a2a_app.telemetry import telemetry

logger = logging.getLogger(__name__)


def _wrap_agent_executor_execute_func(execute_func: Callable) -> Callable:
    async def wrapper(*args, **kwargs):
        executor_instance: AgentExecutor = args[0]
        context: RequestContext = args[1]
        event_queue: EventQueue = args[2]

        with telemetry.tracer.start_as_current_span(name="a2a_invocation") as span:
            exception = None
            try:
                result = await execute_func(
                    executor_instance, context=context, event_queue=event_queue
                )

            except Exception as e:
                logger.error("Invoke agent execute function failed: %s", e)
                exception = e
                raise e
            finally:
                # handler trace span and metrics
                telemetry.trace_a2a_agent(
                    execute_func,
                    span,
                    context,
                    result,
                    exception,
                )

        return result

    return wrapper


class AgentkitA2aApp(BaseAgentkitApp):
    def __init__(self) -> None:
        super().__init__()

        self._agent_executor: AgentExecutor | None = None
        self._task_store: TaskStore | None = None

    def agent_executor(self, **kwargs) -> Callable:
        """Wrap an AgentExecutor class, init it, then bind it to the app instance."""

        def wrapper(cls: type) -> type[AgentExecutor]:
            if not issubclass(cls, AgentExecutor):
                raise TypeError(
                    f"{cls.__name__} must inherit from `a2a.server.agent_execution.AgentExecutor`"
                )

            if self._agent_executor:
                raise RuntimeError("An executor is already bound to this app instance.")

            # Wrap the execute method for intercepting context and event_queue
            cls.execute = _wrap_agent_executor_execute_func(cls.execute)

            # Initialize and bind the executor instance
            self._agent_executor = cls(**kwargs)

            return cls

        return wrapper

    def task_store(self, **kwargs) -> Callable:
        """Wrap a TaskStore class, init it, then bind it to the app instance."""

        def wrapper(cls: type) -> type[TaskStore]:
            if not issubclass(cls, TaskStore):
                raise TypeError(
                    f"{cls.__name__} must inherit from `a2a.server.tasks.task_store.TaskStore`"
                )

            if self._task_store:
                raise RuntimeError(
                    "A task store is already bound to this app instance."
                )

            self._task_store = cls(**kwargs)
            return cls

        return wrapper

    @override
    def run(self, agent_card: AgentCard, host: str, port: int = 8000):
        if not self._agent_executor:
            raise RuntimeError(
                "At least one executor should be provided via `@agent_executor(...)`."
            )
        if not self._task_store:
            logger.warning(
                "No task store provided. You can provide a task store via `@task_store(...)`. Using in-memory task store instead."
            )
            self._task_store = InMemoryTaskStore()

        a2a_app = A2AStarletteApplication(
            agent_card=agent_card,
            http_handler=DefaultRequestHandler(
                agent_executor=self._agent_executor, task_store=self._task_store
            ),
        ).build()

        uvicorn.run(a2a_app, host=host, port=port)
