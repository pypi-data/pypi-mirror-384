# !/usr/bin/env python3
import os
from pathlib import Path
import logging

from dotenv import load_dotenv

env_path = Path(os.path.dirname(os.path.abspath(__file__))) / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    parent_env_path = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) / '.env'
    if parent_env_path.exists():
        load_dotenv(dotenv_path=parent_env_path)
    else:
        print("Warning: no .env file found")

logger = logging.getLogger(__name__)
level = os.environ.get("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=level,
    format='%(asctime)s.%(msecs)03d - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger.info("Initializing Agent server")

import asyncio
import platform
from concurrent import futures
import grpc
import uuid
import datetime

from lybic import LybicClient, LybicAuth, Sandbox
import gui_agents.cli_app as app
from gui_agents.proto import agent_pb2, agent_pb2_grpc
from gui_agents.agents.stream_manager import stream_manager, StreamMessage
from gui_agents.agents.agent_s import load_config
from gui_agents.proto.pb.agent_pb2 import LLMConfig, StageModelConfig, CommonConfig, Authorization, InstanceMode
from gui_agents import Registry, GlobalState, AgentS2, HardwareInterface, __version__


class AgentServicer(agent_pb2_grpc.AgentServicer):
    """
    Implements the Agent gRPC service.
    """

    def __init__(self, max_concurrent_task_num: int = 1, log_dir: str = "runtime"):
        """
        Initialize the AgentServicer with concurrency and runtime state.
        
        Parameters:
            max_concurrent_task_num (int): Maximum number of agent tasks allowed to run concurrently; defaults to 1.
            log_dir (str): Directory for logging and task-related files.
        """
        self.max_concurrent_task_num = max_concurrent_task_num
        self.tasks = {}
        self.global_common_config = agent_pb2.CommonConfig(id="global")
        self.task_lock = asyncio.Lock()
        self.log_dir = log_dir

    async def GetAgentTaskStream(self, request, context):
        """
        Stream TaskStream messages for the given task ID to the client.
        
        If the task ID does not exist, sets gRPC `NOT_FOUND` on the context and returns. Yields GetAgentTaskStreamResponse messages containing the taskId, stage, and message produced by the stream manager. Stops when the client cancels the stream; on internal errors sets gRPC `INTERNAL` on the context. Unregisters the task from the stream manager when streaming ends.
         
        Returns:
            GetAgentTaskStreamResponse: Streamed responses carrying TaskStream payloads with `taskId`, `stage`, and `message`.
        """
        task_id = request.taskId
        logger.info(f"Received GetAgentTaskStream request for taskId: {task_id}")

        async with self.task_lock:
            task_info = self.tasks.get(task_id)

        if not task_info:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Task with ID {task_id} not found.")
            return

        try:
            async for msg in stream_manager.get_message_stream(task_id):
                yield agent_pb2.GetAgentTaskStreamResponse(
                    taskStream=agent_pb2.TaskStream(
                        taskId=task_id,
                        stage=msg.stage,
                        message=msg.message,
                        timestamp=msg.timestamp
                    )
                )
        except asyncio.CancelledError:
            logger.info(f"GetAgentTaskStream for {task_id} cancelled by client.")
        except Exception as e:
            logger.exception(f"Error in GetAgentTaskStream for task {task_id}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"An error occurred during streaming: {e}")

    async def GetAgentInfo(self, request, context):
        """
        Provide agent server metadata.
        
        Returns:
            agent_pb2.AgentInfo: An AgentInfo message containing the server version, the configured maximum concurrent task count (`maxConcurrentTasks`), the current log level (`log_level`), and the host name (`domain`).
        """
        return agent_pb2.AgentInfo(
            version=__version__,
            maxConcurrentTasks=self.max_concurrent_task_num,
            log_level=level,
            domain=platform.node(),
        )

    def _setup_task_state(self, task_id: str) -> Registry:
        """Setup global state and registry for task execution with task isolation"""
        # Create timestamp-based directory structure like cli_app.py
        datetime_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        timestamp_dir = Path(self.log_dir) / f"{datetime_str}_{task_id[:8]}"  # Include task_id prefix
        cache_dir = timestamp_dir / "cache" / "screens"
        state_dir = timestamp_dir / "state"

        cache_dir.mkdir(parents=True, exist_ok=True)
        state_dir.mkdir(parents=True, exist_ok=True)

        # Create task-specific registry
        task_registry = Registry()

        # Register global state for this task in task-specific registry
        global_state = GlobalState(
            screenshot_dir=str(cache_dir),
            tu_path=str(state_dir / "tu.json"),
            search_query_path=str(state_dir / "search_query.json"),
            completed_subtasks_path=str(state_dir / "completed_subtasks.json"),
            failed_subtasks_path=str(state_dir / "failed_subtasks.json"),
            remaining_subtasks_path=str(state_dir / "remaining_subtasks.json"),
            termination_flag_path=str(state_dir / "termination_flag.json"),
            running_state_path=str(state_dir / "running_state.json"),
            display_info_path=str(timestamp_dir / "display.json"),
            agent_log_path=str(timestamp_dir / "agent_log.json")
        )

        # Register in task-specific registry using instance method
        registry_key = "GlobalStateStore"
        task_registry.register_instance(registry_key, global_state)

        logger.info(f"Created task-specific registry for task {task_id}")

        return task_registry

    async def _run_task(self, task_id: str, backend_kwargs):
        """
        Run the lifecycle of a single agent task: mark it running, execute the agent, record final state, emit stream messages, and unregister the task.

        Parameters:
        	task_id (str): Identifier of the task to run.
        	backend_kwargs (dict): Backend configuration passed to the HardwareInterface (e.g., platform, org/api fields, sandbox id).

        Notes:
        	- Updates the task entry in self.tasks (status and final_state).
        	- Emits task lifecycle messages via stream_manager and unregisters the task when finished.
        	- Exceptions are caught, the task status is set to "error", and an error message is emitted.
        	- Supports task cancellation via asyncio.CancelledError.
        """
        async with self.task_lock:
            self.tasks[task_id]["status"] = "running"
            agent = self.tasks[task_id]["agent"]
            steps = self.tasks[task_id]["max_steps"]
            query = self.tasks[task_id]["query"]

            # Register task with stream manager
            await stream_manager.register_task(task_id)

        try:
            # Send message through stream manager
            await stream_manager.add_message(task_id, "starting", "Task starting")

            # Create task-specific registry
            task_registry = self._setup_task_state(task_id)

            # Set task_id for the agent. This is needed so that agent.reset() can find the right components.
            if hasattr(agent, 'set_task_id'):
                agent.set_task_id(task_id)

            hwi = HardwareInterface(backend='lybic', **backend_kwargs)

            # We need to set the registry for the main thread context before reset
            Registry.set_task_registry(task_id, task_registry)
            agent.reset()
            Registry.remove_task_registry(task_id) # Clean up main thread's local

            # Run the blocking function in a separate thread, passing the context
            mode: InstanceMode | None = backend_kwargs.get("mode")
            if mode and mode == InstanceMode.NORMAL:
                await asyncio.to_thread(app.run_agent_normal, agent, query, hwi, steps, False, task_id=task_id, task_registry=task_registry)
            else:
                await asyncio.to_thread(app.run_agent_fast, agent, query, hwi, steps, False, task_id=task_id, task_registry=task_registry)

            # The final state is now determined inside the thread. We'll assume success if no exception.
            final_state = "completed"

            async with self.task_lock:
                self.tasks[task_id]["final_state"] = final_state
                self.tasks[task_id]["status"] = "finished"

            if final_state and final_state == "completed":
                await stream_manager.add_message(task_id, "finished", "Task completed successfully")
            else:
                status = final_state if final_state else 'unknown'
                await stream_manager.add_message(task_id, "finished", f"Task finished with status: {status}")

        except asyncio.CancelledError:
            logger.info(f"Task {task_id} was cancelled")
            async with self.task_lock:
                self.tasks[task_id]["status"] = "cancelled"
            await stream_manager.add_message(task_id, "cancelled", "Task was cancelled by user request")
        except Exception as e:
            logger.exception(f"Error during task execution for {task_id}: {e}")
            async with self.task_lock:
                self.tasks[task_id]["status"] = "error"
            await stream_manager.add_message(task_id, "error", f"An error occurred: {e}")
        finally:
            logger.info(f"Task {task_id} processing finished.")
            # Registry cleanup is now handled within the worker thread
            await stream_manager.unregister_task(task_id)

    async def _make_backend_kwargs(self, request):
        """
        Builds the backend keyword arguments required to provision or select a compute sandbox for the task, based on the provided request and the service's global configuration.
        
        Parameters:
            request: The incoming gRPC request containing optional `runningConfig` and `sandbox` fields. If `runningConfig.authorizationInfo` is present, it will be used to set Lybic authorization for this servicer instance.
        
        Returns:
            dict: A mapping with at least:
                - "platform": platform identifier (e.g., "Windows" or "Ubuntu").
                - "precreate_sid": sandbox id to use or an empty string if none.
            When the backend is "lybic", the dict may also include:
                - "org_id": organization id for Lybic.
                - "api_key": API key for Lybic.
                - "endpoint": Lybic API endpoint.
        
        Side effects:
            - May call self._create_sandbox(...) to create or retrieve a sandbox and determine the platform.
        """
        backend_kwargs = {}
        platform_map = {
            agent_pb2.SandboxOS.WINDOWS: "Windows",
            agent_pb2.SandboxOS.LINUX: "Ubuntu",
        }
        backend = "lybic"
        shape = "beijing-2c-4g-cpu" # default shape # todo: check shape exist by using lybic sdk >=0.8.0b3
        if request.HasField("runningConfig"):
            if request.runningConfig.backend:
                backend = request.runningConfig.backend
            backend_kwargs["mode"] = request.runningConfig.mode

        platform_str = platform.system()
        sid = ''
        sandbox_pb = None

        if backend == 'lybic':
            auth_info = (request.runningConfig.authorizationInfo
                         if request.HasField("runningConfig") and request.runningConfig.HasField("authorizationInfo")
                         else self.global_common_config.authorizationInfo)
            if not auth_info or not auth_info.orgID or not auth_info.apiKey:
                raise ValueError("Lybic backend requires valid authorization (orgID and apiKey)")

            lybic_auth = LybicAuth(
                org_id=auth_info.orgID,
                api_key=auth_info.apiKey,
                endpoint=auth_info.apiEndpoint or "https://api.lybic.cn/"
            )

            if request.HasField("sandbox"):
                shape = request.sandbox.shapeName
                sid = request.sandbox.id
                if sid:
                    logger.info(f"Using existing sandbox with id: {sid}")
                    sandbox_pb = await self._get_sandbox_pb(sid, lybic_auth)  # if not exist raise NotFound
                    platform_str = platform_map.get(sandbox_pb.os, platform.system())
                else:
                    sandbox_pb = await self._create_sandbox(shape, lybic_auth)
                    sid, platform_str = sandbox_pb.id, platform_map.get(sandbox_pb.os, platform.system())

                if request.sandbox.os != agent_pb2.SandboxOS.OSUNDEFINED:
                    platform_str = platform_map.get(request.sandbox.os, platform.system())
            else:
                sandbox_pb = await self._create_sandbox(shape, lybic_auth)
                sid, platform_str = sandbox_pb.id, platform_map.get(sandbox_pb.os, platform.system())
        else:
            if request.HasField("sandbox") and request.sandbox.os != agent_pb2.SandboxOS.OSUNDEFINED:
                platform_str = platform_map.get(request.sandbox.os, platform.system())

        backend_kwargs["sandbox"] = sandbox_pb
        backend_kwargs["platform"] = platform_str
        backend_kwargs["precreate_sid"] = sid

        # Add Lybic authorization info if available
        if backend == 'lybic':
            auth_info = (request.runningConfig.authorizationInfo
                         if request.HasField("runningConfig") and request.runningConfig.HasField("authorizationInfo")
                         else self.global_common_config.authorizationInfo)
            if not auth_info or not auth_info.orgID or not auth_info.apiKey:
                raise ValueError("Lybic backend requires valid authorization (orgID and apiKey)")
            if auth_info.orgID:
                backend_kwargs['org_id'] = auth_info.orgID
            if auth_info.apiKey:
                backend_kwargs['api_key'] = auth_info.apiKey
            if auth_info.apiEndpoint:
                backend_kwargs['endpoint'] = auth_info.apiEndpoint

        return backend_kwargs

    async def _make_agent(self,request):
        """
        Builds and returns an AgentS2 configured for the incoming request by applying model and provider overrides to the tool configurations.
        
        Parameters:
            request: gRPC request message that may contain a runningConfig with a stageModelConfig. If present, stageModelConfig values take precedence over the global common config.
        
        Returns:
            AgentS2: An agent instance with platform set to "windows", screen_size [1280, 720], takeover and search disabled, and a tools_config where tool entries have been updated with provider, model_name/model, and optionally overridden api_key and base_url/endpoint based on the stage model configuration.
        
        Raises:
            Exception: If neither the request nor the global common config contains a StageModelConfig.
        """
        tools_config, tools_dict = load_config()

        stage_config: StageModelConfig
        if request.HasField("runningConfig") and request.runningConfig.HasField("stageModelConfig"):
            stage_config = request.runningConfig.stageModelConfig
            logger.info("Applying task model configurations to this task.")
        elif self.global_common_config.HasField("stageModelConfig"):
            stage_config = self.global_common_config.stageModelConfig
        else:
            raise Exception("No model configurations found.")

        logger.info("Applying global model configurations to this task.")

        def apply_config(tool_name, llm_config:LLMConfig):
            """
            Apply an LLM configuration to an existing tool entry in the local tools_dict.
            
            If a tool with the given name exists in tools_dict and the LLM config specifies a modelName,
            this function updates the tool's provider, model_name, and model fields. It also overrides
            sensitive connection fields when present: apiKey is copied to the tool's api_key, and
            apiEndpoint is copied to base_url and endpoint_url. Actions are logged for any overrides.
            
            Parameters:
                tool_name (str): Name of the tool to update in tools_dict.
                llm_config (LLMConfig): LLM configuration containing provider, modelName, apiKey, and apiEndpoint.
            
            Returns:
                None
            """
            if tool_name in tools_dict and llm_config.modelName:
                tool_cfg = tools_dict[tool_name]
                tool_cfg['provider'] = llm_config.provider
                tool_cfg['model_name'] = llm_config.modelName
                tool_cfg['model'] = llm_config.modelName

                # IMPORTANT Override api key and endpoint
                if llm_config.apiKey:
                    tool_cfg['api_key'] = llm_config.apiKey
                    logger.info(f"Override api_key for tool '{tool_name}'")
                if llm_config.apiEndpoint:
                    tool_cfg['base_url'] = llm_config.apiEndpoint
                    tool_cfg['endpoint_url'] = llm_config.apiEndpoint  # for some engines that use endpoint_url
                    logger.info(f"Override base_url for tool '{tool_name}': {llm_config.apiEndpoint}")

                logger.info(f"Override tool '{tool_name}' with model '{llm_config.modelName}'.")

        if stage_config.HasField("embeddingModel"):
            apply_config('embedding', stage_config.embeddingModel)

        if stage_config.HasField("groundingModel"):
            apply_config('grounding', stage_config.groundingModel)

        if stage_config.HasField("actionGeneratorModel"):
            common_llm_config = stage_config.actionGeneratorModel
            # Apply common config to all other LLM-based tools
            for tool_name, _ in tools_dict.items():
                if tool_name not in ['embedding', 'grounding']:
                    apply_config(tool_name, common_llm_config)
        
        # After modifications, merge changes from tools_dict back into tools_config
        for tool_entry in tools_config['tools']:
            tool_name = tool_entry['tool_name']
            if tool_name in tools_dict:
                modified_data = tools_dict[tool_name]
                # Ensure all modified fields are synced back to tools_config
                for key, value in modified_data.items():
                    if key in ['provider', 'model_name', 'api_key', 'base_url', 'model']:
                        tool_entry[key] = value

        return AgentS2(
            platform="windows",  # Sandbox system
            screen_size=[1280, 720],
            enable_takeover=False,
            enable_search=False,
            tools_config=tools_config,
        )

    async def RunAgentInstruction(self, request, context):
        """
        Stream task progress for a newly created instruction-run agent while managing task lifecycle and concurrency.
        
        Parameters:
            request: The RunAgentInstruction request proto containing the instruction and runtime configuration.
            context: gRPC context used to set status codes and details on error or resource exhaustion.
        
        Returns:
            An iterator that yields TaskStream messages with fields: taskId, stage, message, and timestamp.
        
        Notes:
            - Enforces the servicer's max concurrent task limit and sets gRPC StatusCode.RESOURCE_EXHAUSTED if exceeded.
            - Registers and starts a background task to execute the agent; cancels that background task if the client cancels the stream.
            - On internal streaming errors, sets gRPC StatusCode.INTERNAL with an explanatory detail.
        """
        task_id = str(uuid.uuid4())
        logger.info(f"Received RunAgentInstruction request, assigning taskId: {task_id}")

        task_future = None

        async with self.task_lock:
            active_tasks = sum(1 for t in self.tasks.values() if t['status'] in ['pending', 'running'])
            if active_tasks >= self.max_concurrent_task_num:
                context.set_code(grpc.StatusCode.RESOURCE_EXHAUSTED)
                context.set_details(f"Max concurrent tasks ({self.max_concurrent_task_num}) reached.")
                return

            queue = asyncio.Queue()
            agent = await self._make_agent(request)
            backend_kwargs = await self._make_backend_kwargs(request)
            max_steps = 50
            if request.HasField("runningConfig") and request.runningConfig.steps:
                max_steps = request.runningConfig.steps

            self.tasks[task_id] = {
                "request": request,
                "status": "pending",
                "final_state": None,
                "queue": queue,
                "future": None,
                "query": request.instruction,
                "agent": agent,
                "max_steps": max_steps,
                "sandbox": backend_kwargs["sandbox"],
            }

            # This property is used to pass sandbox information.
            # It has now completed its mission and needs to be deleted, otherwise other backends may crash.
            del backend_kwargs["sandbox"]

            task_future = asyncio.create_task(self._run_task(task_id, backend_kwargs))
            self.tasks[task_id]["future"] = task_future
        try:
            async for msg in stream_manager.get_message_stream(task_id):
                yield agent_pb2.TaskStream(
                    taskId=task_id,
                    stage=msg.stage,
                    message=msg.message,
                    timestamp=msg.timestamp
                )
        except asyncio.CancelledError:
            logger.info(f"RunAgentInstruction stream for {task_id} cancelled by client.")
            if task_future:
                task_future.cancel()
                # Set cancellation flag in global state for agents to check
                try:
                    global_state: GlobalState = Registry.get_from_context("GlobalStateStore", task_id)
                    if global_state:
                        global_state.set_running_state("cancelled")
                        logger.info(f"Set running state to 'cancelled' for task {task_id} due to client disconnect.")
                    else:
                        logger.warning(f"Could not find GlobalState for task {task_id} to set cancellation flag on client disconnect.")
                except Exception as e:
                    logger.error(f"Error setting cancellation flag for task {task_id} on client disconnect: {e}")
        except Exception as e:
            logger.exception(f"Error in RunAgentInstruction stream for task {task_id}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"An error occurred during streaming: {e}")

    async def RunAgentInstructionAsync(self, request, context):
        """
        Start a new agent task in the background and return a task identifier immediately.
        
        If the server has reached its configured maximum concurrent tasks, the RPC sets
        gRPC status RESOURCE_EXHAUSTED and returns no response.
        
        Returns:
            agent_pb2.RunAgentInstructionAsyncResponse: Response containing the generated `taskId`.
        """
        task_id = str(uuid.uuid4())
        logger.info(f"Received RunAgentInstructionAsync request, assigning taskId: {task_id}")

        async with self.task_lock:
            active_tasks = sum(1 for t in self.tasks.values() if t['status'] in ['pending', 'running'])
            if active_tasks >= self.max_concurrent_task_num:
                context.set_code(grpc.StatusCode.RESOURCE_EXHAUSTED)
                context.set_details(f"Max concurrent tasks ({self.max_concurrent_task_num}) reached.")
                return

            agent = await self._make_agent(request=request)
            backend_kwargs = await self._make_backend_kwargs(request)
            max_steps = 50
            if request.HasField("runningConfig") and request.runningConfig.steps:
                max_steps = request.runningConfig.steps

            # Create queue for this task
            queue = asyncio.Queue()

            self.tasks[task_id] = {
                "request": request,
                "status": "pending",
                "final_state": None,
                "queue": queue,
                "future": None,
                "query": request.instruction,
                "agent": agent,
                "max_steps": max_steps,
                "sandbox": backend_kwargs["sandbox"],
            }
            # This property is used to pass sandbox information.
            # It has now completed its mission and needs to be deleted, otherwise other backends may crash.
            del backend_kwargs["sandbox"]

            # Start the task in background
            task_future = asyncio.create_task(self._run_task(task_id, backend_kwargs))

            self.tasks[task_id]["future"] = task_future

        return agent_pb2.RunAgentInstructionAsyncResponse(taskId=task_id)

    async def QueryTaskStatus(self, request, context):
        """
        Retrieve the current status and a human-readable message for the task identified by `request.taskId`.
        
        If the task is not found, the response uses `TaskStatus.NOT_FOUND` and a descriptive message. Internal task states are mapped to protobuf `TaskStatus` values: finished maps to `SUCCESS` (message includes `final_state` when available), error maps to `FAILURE`, and pending/running map to the corresponding statuses; when a controller is present and has recorded thoughts, the latest thought is used as the message.
        
        Parameters:
            request: RPC request containing `taskId` (the ID of the task to query).
            context: gRPC context (not used for parameter descriptions).
        
        Returns:
            QueryTaskStatusResponse: the task ID, mapped `status`, a short `message` describing the current state, a `result` string (empty if none), and the `sandbox` value echoed from the original request.
        """
        task_id = request.taskId
        async with self.task_lock:
            task_info = self.tasks.get(task_id)

        if not task_info:
            return agent_pb2.QueryTaskStatusResponse(
                taskId=task_id,
                status=agent_pb2.TaskStatus.NOT_FOUND,
                message=f"Task with ID {task_id} not found."
            )

        status = task_info["status"]
        final_state = task_info.get("final_state")

        status_map = {
            "pending": agent_pb2.TaskStatus.PENDING,
            "running": agent_pb2.TaskStatus.RUNNING,
            "fulfilled": agent_pb2.TaskStatus.SUCCESS,
            "rejected": agent_pb2.TaskStatus.FAILURE,
            "cancelled": agent_pb2.TaskStatus.CANCELLED,
        }

        if status == "finished":
            task_status = agent_pb2.TaskStatus.SUCCESS
            message = f"Task finished with status: {final_state}" if final_state else "Task finished."
            result = ""
        elif status == "error":
            task_status = agent_pb2.TaskStatus.FAILURE
            message = "Task failed with an exception."
            result = ""
        elif status == "cancelled":
            task_status = agent_pb2.TaskStatus.CANCELLED
            message = "Task was cancelled by user request."
            result = ""
        else:  # pending or running
            task_status = status_map.get(status, agent_pb2.TaskStatus.TASKSTATUSUNDEFINED)
            message = "Task is running."
            result = ""

        return agent_pb2.QueryTaskStatusResponse(
            taskId=task_id,
            status=task_status,
            message=message,
            result=result,
            sandbox=task_info["sandbox"]
        )

    async def CancelTask(self, request, context):
        """
        Cancel a running task by its taskId.

        If the task exists and is running, it will be cancelled and a success response is returned.
        If the task is not found or already completed, an appropriate response is returned.

        Parameters:
            request: CancelTaskRequest containing the taskId to cancel
            context: gRPC context for setting status codes and details

        Returns:
            CancelTaskResponse: Response containing taskId, success status, and message
        """
        task_id = request.taskId
        logger.info(f"Received CancelTask request for taskId: {task_id}")

        async with self.task_lock:
            task_info = self.tasks.get(task_id)

        if not task_info:
            return agent_pb2.CancelTaskResponse(
                taskId=task_id,
                success=False,
                message=f"Task with ID {task_id} not found."
            )

        status = task_info["status"]
        task_future = task_info.get("future")

        # Check if task can be cancelled
        if status in ["finished", "error"]:
            return agent_pb2.CancelTaskResponse(
                taskId=task_id,
                success=False,
                message=f"Task {task_id} is already {status} and cannot be cancelled."
            )
        elif status == "cancelled":
            return agent_pb2.CancelTaskResponse(
                taskId=task_id,
                success=True,
                message=f"Task {task_id} was already cancelled."
            )
        elif status in ["pending", "running"] and task_future:
            try:
                # Cancel the task future
                task_future.cancel()
                task_info["status"] = "cancelled"

                # Set cancellation flag in global state for agents to check
                global_state: GlobalState = Registry.get_from_context("GlobalStateStore", task_id)  # type: ignore
                global_state.set_running_state("cancelled")

                # Send cancellation message through stream manager
                await stream_manager.add_message(task_id, "cancelled", "Task was cancelled by user request")

                logger.info(f"Task {task_id} successfully cancelled")
                return agent_pb2.CancelTaskResponse(
                    taskId=task_id,
                    success=True,
                    message=f"Task {task_id} has been successfully cancelled."
                )
            except Exception as e:
                logger.error(f"Failed to cancel task {task_id}: {e}")
                return agent_pb2.CancelTaskResponse(
                    taskId=task_id,
                    success=False,
                    message=f"Failed to cancel task {task_id}: {e}"
                )
        else:
            return agent_pb2.CancelTaskResponse(
                taskId=task_id,
                success=False,
                message=f"Task {task_id} is in state '{status}' and cannot be cancelled."
            )

    def _mask_config_secrets(self, config: CommonConfig) -> CommonConfig:
        """
        Return a deep copy of a CommonConfig with sensitive API keys replaced by "********".
        
        Creates a copy of the provided CommonConfig and masks secrets to avoid leaking credentials. Specifically, it masks authorizationInfo.apiKey and any LLMConfig.apiKey fields present inside stageModelConfig (for example: embeddingModel, groundingModel, actionGeneratorModel, and other stage LLM fields).
        
        Parameters:
            config (CommonConfig): The original configuration that may contain sensitive API keys.
        
        Returns:
            CommonConfig: A copy of `config` where discovered API keys have been replaced with "********".
        """
        config_copy = CommonConfig()
        config_copy.CopyFrom(config)

        # Mask authorizationInfo.apiKey
        if config_copy.HasField("authorizationInfo") and config_copy.authorizationInfo.apiKey:
            config_copy.authorizationInfo.apiKey = "********"

        # Mask stageModelConfig API keys
        if config_copy.HasField("stageModelConfig"):
            stage_config = config_copy.stageModelConfig

            # List of all LLMConfig fields in StageModelConfig
            llm_config_fields = [
                "contextFusionModel", "subtaskPlannerModel", "trajReflectorModel",
                "memoryRetrivalModel", "groundingModel", "taskEvaluatorModel",
                "actionGeneratorModel", "actionGeneratorWithTakeoverModel",
                "fastActionGeneratorModel", "fastActionGeneratorWithTakeoverModel",
                "dagTranslatorModel", "embeddingModel", "queryFormulatorModel",
                "narrativeSummarizationModel", "textSpanModel", "episodeSummarizationModel"
            ]

            # Check all LLMConfig fields and mask their API keys
            for field_name in llm_config_fields:
                if stage_config.HasField(field_name):
                    llm_config = getattr(stage_config, field_name)
                    if llm_config and llm_config.apiKey:
                        llm_config.apiKey = "********"

        return config_copy

    def _mask_llm_config_secrets(self, llm_config: LLMConfig) -> LLMConfig:
        """
        Return a copy of the given LLMConfig with sensitive fields masked.
        
        Parameters:
            llm_config (LLMConfig): The original LLM configuration to mask.
        
        Returns:
            LLMConfig: A copy of `llm_config` where the `apiKey` (if present) is replaced with `"********"`.
        """
        config_copy = LLMConfig()
        config_copy.CopyFrom(llm_config)

        if config_copy.apiKey:
            config_copy.apiKey = "********"

        return config_copy

    async def GetGlobalCommonConfig(self, request, context):
        """
        Return a masked copy of the global common configuration to avoid exposing secrets.
        
        The returned configuration is a deep copy of the server's global common config with sensitive fields (such as API keys) replaced by asterisks.
        
        Returns:
            CommonConfig: A copy of the global common configuration with sensitive values masked.
        """
        masked_config = self._mask_config_secrets(self.global_common_config)
        logger.debug("Returned masked global common config")
        return masked_config

    async def GetCommonConfig(self, request, context):
        """
        Return a masked copy of the saved CommonConfig for the task identified by request.id.
        
        Parameters:
            request: RPC request containing `id` (the task identifier) whose configuration is being fetched.
            context: gRPC context used to report NOT_FOUND when no configuration exists for the given task id.
        
        Returns:
            agent_pb2.CommonConfig: A copy of the task's CommonConfig with sensitive fields masked, or an empty CommonConfig if no task with the given id exists (in which case the gRPC context is set to NOT_FOUND).
        """
        async with self.task_lock:
            if request.id == "global":
                return await self.GetGlobalCommonConfig(request, context)
            else:
                task_info = self.tasks.get(request.id)
        if task_info and task_info.get("request"):
            if task_info["request"].HasField("runningConfig"):
                original_config = task_info["request"].runningConfig
                masked_config = self._mask_config_secrets(original_config)
            else:
                masked_config = agent_pb2.CommonConfig(id=request.id)

            logger.debug(f"Returned masked config for task {request.id}")
            return masked_config
        context.set_code(grpc.StatusCode.NOT_FOUND)
        context.set_details(f"Config for task {request.id} not found.")
        return agent_pb2.CommonConfig()

    def _new_lybic_client(self, lybic_auth: LybicAuth) -> LybicClient:
        """
        Create and return a new LybicClient.
        """
        return LybicClient(lybic_auth)

    async def SetGlobalCommonConfig(self, request, context):
        """
        Set the server's global common configuration.
        
        Sets request.commonConfig.id to "global" and stores it as the servicer's global_common_config.
        
        Parameters:
            request: gRPC request containing `commonConfig` to apply.
        
        Returns:
            agent_pb2.SetCommonConfigResponse: Response with `success=True` and the configuration `id`.
        """
        if os.environ.get("ALLOW_SET_GLOBAL_CONFIG", "0")=="0":
            context.set_code(grpc.StatusCode.PERMISSION_DENIED)
            context.set_details("Permission denied.")
            return agent_pb2.SetCommonConfigResponse()
        logger.info("Setting new global common config.")
        request.commonConfig.id = "global"
        self.global_common_config = request.commonConfig

        return agent_pb2.SetCommonConfigResponse(success=True, id=self.global_common_config.id)

    async def SetGlobalCommonLLMConfig(self, request, context):
        """
        Update the global stage action-generator LLM configuration.
        
        If the global common config lacks a stageModelConfig, one is created. The request's `llmConfig` is copied into global_common_config.stageModelConfig.actionGeneratorModel and returned.
        
        Returns:
            llmConfig: The `LLMConfig` message that was stored in the global configuration.
        """
        if os.environ.get("ALLOW_SET_GLOBAL_CONFIG", "0")=="0":
            context.set_code(grpc.StatusCode.PERMISSION_DENIED)
            context.set_details("Permission denied.")
            return agent_pb2.LLMConfig()
        if not self.global_common_config.HasField("stageModelConfig"):
            self.global_common_config.stageModelConfig.SetInParent()
        self.global_common_config.stageModelConfig.actionGeneratorModel.CopyFrom(request.llmConfig)
        logger.info(f"Global common LLM config updated to: {request.llmConfig.modelName}")
        return request.llmConfig

    async def SetGlobalGroundingLLMConfig(self, request, context):
        """
        Update the global grounding LLM configuration used by the agent.
        
        Ensures the global common config has a stageModelConfig, copies the provided `llmConfig` into
        `global_common_config.stageModelConfig.groundingModel`, and logs the update.
        
        Parameters:
        	request (SetGlobalGroundingLLMConfigRequest): Request containing `llmConfig` to apply.
        	context: gRPC context (not documented).
        
        Returns:
        	LLMConfig: The `llmConfig` that was applied.
        """
        if os.environ.get("ALLOW_SET_GLOBAL_CONFIG", "0")=="0":
            context.set_code(grpc.StatusCode.PERMISSION_DENIED)
            context.set_details("Permission denied.")
            return agent_pb2.LLMConfig()
        if not self.global_common_config.HasField("stageModelConfig"):
            self.global_common_config.stageModelConfig.SetInParent()
        self.global_common_config.stageModelConfig.groundingModel.CopyFrom(request.llmConfig)
        logger.info(f"Global grounding LLM config updated to: {request.llmConfig.modelName}")
        return request.llmConfig

    async def SetGlobalEmbeddingLLMConfig(self, request, context):
        """
        Ensure the global common config has a stage model config and set its embedding model to the provided LLM configuration.
        
        Parameters:
            request: RPC request containing `llmConfig` to apply as the global embedding model.
        
        Returns:
            The `llmConfig` that was set as the global embedding model.
        """
        if os.environ.get("ALLOW_SET_GLOBAL_CONFIG", "0")=="0":
            context.set_code(grpc.StatusCode.PERMISSION_DENIED)
            context.set_details("Permission denied.")
            return agent_pb2.LLMConfig()
        if not self.global_common_config.HasField("stageModelConfig"):
            self.global_common_config.stageModelConfig.SetInParent()
        self.global_common_config.stageModelConfig.embeddingModel.CopyFrom(request.llmConfig)
        logger.info(f"Global embedding LLM config updated to: {request.llmConfig.modelName}")
        return request.llmConfig

    async def _create_sandbox(self, shape: str, lybic_auth: LybicAuth) -> agent_pb2.Sandbox:
        """
        Create a sandbox with the given shape via the Lybic service and return its identifier and operating system.

        Parameters:
            shape (str): The sandbox shape to create (provider-specific size/OS configuration).
            lybic_auth (LybicAuth): The authentication object for Lybic.

        Returns:
            agent_pb2.Sandbox: A protobuf message containing sandbox details.
        """
        lybic_client = self._new_lybic_client(lybic_auth)
        sandbox_service = Sandbox(lybic_client)
        result = await sandbox_service.create(shape=shape)
        sandbox = await sandbox_service.get(result.id)
        await lybic_client.close()

        return agent_pb2.Sandbox(
            id=sandbox.sandbox.id,
            os=self._lybic_sandbox_os_to_pb_enum(sandbox.sandbox.shape),
            shapeName=sandbox.sandbox.shapeName,
            hardwareAcceleratedEncoding=sandbox.sandbox.shape.hardwareAcceleratedEncoding,
            virtualization=sandbox.sandbox.shape.virtualization,
            architecture=sandbox.sandbox.shape.architecture,
        )

    @staticmethod
    def _lybic_sandbox_os_to_pb_enum(os) -> agent_pb2.SandboxOS:
        """
        Converts a sandbox OS string to an enum value.
        """
        os_raw = getattr(os, "os", "") or ""
        os_upper = str(os_raw).upper()
        if "WIN" in os_upper:
            os_enum = agent_pb2.SandboxOS.WINDOWS
        elif "LINUX" in os_upper or "UBUNTU" in os_upper:
            os_enum = agent_pb2.SandboxOS.LINUX
        elif "ANDROID" in os_upper:
            os_enum = agent_pb2.SandboxOS.ANDROID
        else:
            os_enum = agent_pb2.SandboxOS.OSUNDEFINED
        return os_enum

    async def _get_sandbox_pb(self, sid: str, lybic_auth: LybicAuth) -> agent_pb2.Sandbox:
        """
        Retrieves sandbox details for a given sandbox ID and returns them as a protobuf message.
        """
        if not lybic_auth:
            raise ValueError("Lybic client not initialized. Please call SetGlobalCommonConfig before")

        lybic_client = self._new_lybic_client(lybic_auth)
        sandbox_service = Sandbox(lybic_client)
        sandbox_details = await sandbox_service.get(sid)
        await lybic_client.close()

        return agent_pb2.Sandbox(
            id=sandbox_details.sandbox.id,
            os=self._lybic_sandbox_os_to_pb_enum(sandbox_details.sandbox.shape),
            shapeName=sandbox_details.sandbox.shapeName,
            hardwareAcceleratedEncoding=sandbox_details.sandbox.shape.hardwareAcceleratedEncoding,
            virtualization=sandbox_details.sandbox.shape.virtualization,
            architecture=sandbox_details.sandbox.shape.architecture,
        )

async def serve():
    """
    Start and run the Agent gRPC server and block until it terminates.
    
    This coroutine initializes and starts an aio gRPC server that serves the AgentServicer and remains running until server shutdown. It reads the following environment variables to control behavior:
    - GRPC_PORT: port to listen on (default "50051")
    - GRPC_MAX_WORKER_THREADS: maximum thread pool workers for the server (default "100")
    
    The function also registers the servicer with the server, configures the stream_manager to use the current asyncio event loop, and then starts and awaits server termination.
    """
    port = os.environ.get("GRPC_PORT", 50051)
    max_workers = int(os.environ.get("GRPC_MAX_WORKER_THREADS", 100))
    task_num = int(os.environ.get("TASK_MAX_TASKS", 5))
    servicer = AgentServicer(max_concurrent_task_num=task_num, log_dir=app.log_dir)
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers))
    agent_pb2_grpc.add_AgentServicer_to_server(servicer, server)
    server.add_insecure_port(f'[::]:{port}')
    logger.info(f"Agent gRPC server started on port {port}")

    stream_manager.set_loop(asyncio.get_running_loop())

    await server.start()
    await server.wait_for_termination()

def main():
    """Entry point for the gRPC server."""
    has_display, pyautogui_available, _ = app.check_display_environment()
    compatible_backends, incompatible_backends = app.get_compatible_backends(has_display, pyautogui_available)
    app.validate_backend_compatibility('lybic', compatible_backends, incompatible_backends)
    asyncio.run(serve())

if __name__ == '__main__':
    main()
