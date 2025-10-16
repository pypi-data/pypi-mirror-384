from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from collections.abc import AsyncGenerator, Callable, Coroutine, Generator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, TypeVar, cast

import msgspec
import websockets.exceptions
from httpx import (
    AsyncClient,
    codes as http_status,
)
from pydantic import BaseModel
from websockets.asyncio import client as asyncio_websockets_client
from websockets.asyncio.client import ClientConnection, connect

from exponent.commands.utils import ConnectionTracker
from exponent.core.config import is_editable_install
from exponent.core.remote_execution import files, system_context
from exponent.core.remote_execution.cli_rpc_types import (
    BashToolInput,
    BatchToolExecutionRequest,
    BatchToolExecutionResponse,
    CliRpcRequest,
    CliRpcResponse,
    ErrorResponse,
    ErrorToolResult,
    GenerateUploadUrlRequest,
    GenerateUploadUrlResponse,
    GetAllFilesRequest,
    GetAllFilesResponse,
    HttpRequest,
    KeepAliveCliChatRequest,
    KeepAliveCliChatResponse,
    SwitchCLIChatRequest,
    SwitchCLIChatResponse,
    TerminateRequest,
    TerminateResponse,
    ToolExecutionRequest,
    ToolExecutionResponse,
    ToolResultType,
)
from exponent.core.remote_execution.code_execution import (
    execute_code_streaming,
)
from exponent.core.remote_execution.files import file_walk
from exponent.core.remote_execution.http_fetch import fetch_http_content
from exponent.core.remote_execution.session import (
    RemoteExecutionClientSession,
    get_session,
    send_exception_log,
)
from exponent.core.remote_execution.tool_execution import (
    execute_bash_tool,
    execute_tool,
    truncate_result,
)
from exponent.core.remote_execution.types import (
    ChatSource,
    CLIConnectedState,
    CreateChatResponse,
    HeartbeatInfo,
    RemoteExecutionResponseType,
    RunWorkflowRequest,
    StreamingCodeExecutionRequest,
    WorkflowInput,
    WorkflowTriggerRequest,
    WorkflowTriggerResponse,
)
from exponent.core.remote_execution.utils import (
    deserialize_api_response,
)
from exponent.utils.version import get_installed_version

logger = logging.getLogger(__name__)


TModel = TypeVar("TModel", bound=BaseModel)


@dataclass
class WSDisconnected:
    error_message: str | None = None


@dataclass
class SwitchCLIChat:
    new_chat_uuid: str


REMOTE_EXECUTION_CLIENT_EXIT_INFO = WSDisconnected | SwitchCLIChat

# UUID for a single run of the CLI
cli_uuid = uuid.uuid4()


class RemoteExecutionClient:
    def __init__(
        self,
        session: RemoteExecutionClientSession,
        file_cache: files.FileCache | None = None,
    ):
        self.current_session = session
        self.file_cache = file_cache or files.FileCache(session.working_directory)

        # for active code executions, track whether they should be halted
        # correlation_id -> should_halt
        self._halt_states: dict[str, bool] = {}
        self._halt_lock = asyncio.Lock()

        # Track last request time for timeout functionality
        self._last_request_time: float | None = None

        # Track pending upload URL requests
        self._pending_upload_requests: dict[
            str, asyncio.Future[GenerateUploadUrlResponse]
        ] = {}
        self._upload_request_lock = asyncio.Lock()
        self._websocket: ClientConnection | None = None

    @property
    def working_directory(self) -> str:
        return self.current_session.working_directory

    @property
    def api_client(self) -> AsyncClient:
        return self.current_session.api_client

    @property
    def ws_client(self) -> AsyncClient:
        return self.current_session.ws_client

    async def add_code_execution_to_halt_states(self, correlation_id: str) -> None:
        async with self._halt_lock:
            self._halt_states[correlation_id] = False

    async def halt_all_code_executions(self) -> None:
        logger.info(f"Halting all code executions: {self._halt_states}")
        async with self._halt_lock:
            self._halt_states = {
                correlation_id: True for correlation_id in self._halt_states.keys()
            }

    async def clear_halt_state(self, correlation_id: str) -> None:
        async with self._halt_lock:
            self._halt_states.pop(correlation_id, None)

    def get_halt_check(self, correlation_id: str) -> Callable[[], bool]:
        def should_halt() -> bool:
            # Don't need to lock here, since just reading from dict
            return self._halt_states.get(correlation_id, False)

        return should_halt

    async def _timeout_monitor(
        self, timeout_seconds: int | None
    ) -> WSDisconnected | None:
        """Monitor for inactivity timeout and return WSDisconnected if timeout occurs.

        If timeout_seconds is None, keeps looping indefinitely until cancelled.
        """
        try:
            while True:
                await asyncio.sleep(1)
                if (
                    timeout_seconds is not None
                    and self._last_request_time is not None
                    and time.time() - self._last_request_time > timeout_seconds
                ):
                    logger.info(
                        f"No requests received for {timeout_seconds} seconds. Shutting down..."
                    )
                    return WSDisconnected(
                        error_message=f"Timeout after {timeout_seconds} seconds of inactivity"
                    )
        except asyncio.CancelledError:
            # Handle cancellation gracefully
            return None

    async def _handle_websocket_message(
        self,
        msg: str,
        websocket: ClientConnection,
        requests: asyncio.Queue[CliRpcRequest],
    ) -> REMOTE_EXECUTION_CLIENT_EXIT_INFO | None:
        """Handle an incoming websocket message.
        Returns None to continue processing, or a REMOTE_EXECUTION_CLIENT_EXIT_INFO to exit."""

        self._last_request_time = time.time()

        msg_data = json.loads(msg)
        if msg_data["type"] == "result":
            data = json.dumps(msg_data["data"])
            try:
                response = msgspec.json.decode(data, type=CliRpcResponse)
                if isinstance(response.response, GenerateUploadUrlResponse):
                    async with self._upload_request_lock:
                        if response.request_id in self._pending_upload_requests:
                            future = self._pending_upload_requests.pop(
                                response.request_id
                            )
                            future.set_result(response.response)
            except Exception as e:
                logger.error(f"Error handling upload URL response: {e}")
            return None
        elif msg_data["type"] != "request":
            return None

        data = json.dumps(msg_data["data"])
        try:
            request = msgspec.json.decode(data, type=CliRpcRequest)
        except msgspec.DecodeError as e:
            # Try and decode to get request_id if possible
            request = msgspec.json.decode(data)
            if isinstance(request, dict) and "request_id" in request:
                request_id = request["request_id"]
                if (
                    request.get("request", {}).get("type", {}) == "tool_execution"
                ) and (
                    "tool_input" in request["request"]
                    and "tool_name" in request["request"]["tool_input"]
                ):
                    tool_name = request["request"]["tool_input"]["tool_name"]
                    logger.error(
                        f"Error tool {tool_name} received in a request."
                        "Please ensure you are running the latest version of Indent. If this issue persists, please contact support."
                    )
                    await websocket.send(
                        json.dumps(
                            {
                                "type": "result",
                                "data": msgspec.to_builtins(
                                    CliRpcResponse(
                                        request_id=request_id,
                                        response=ErrorResponse(
                                            error_message=f"Unknown tool: {tool_name}. If you are running an older version of Indent, please upgrade to the latest version to ensure compatibility."
                                        ),
                                    )
                                ),
                            }
                        )
                    )
                else:
                    logger.error(
                        "Error decoding cli rpc request. Please ensure you are running the latest version of Indent."
                    )
                    await websocket.send(
                        json.dumps(
                            {
                                "type": "result",
                                "data": msgspec.to_builtins(
                                    CliRpcResponse(
                                        request_id=request_id,
                                        response=ErrorResponse(
                                            error_message=f"Unknown cli rpc request type: {request}",
                                        ),
                                    )
                                ),
                            }
                        )
                    )

                return None
            else:
                # If we couldn't get a request_id, re-raise and fail noisily
                raise e

        if isinstance(request.request, TerminateRequest):
            await self.halt_all_code_executions()
            await websocket.send(
                json.dumps(
                    {
                        "type": "result",
                        "data": msgspec.to_builtins(
                            CliRpcResponse(
                                request_id=request.request_id,
                                response=TerminateResponse(),
                            )
                        ),
                    }
                )
            )
            return None
        elif isinstance(request.request, SwitchCLIChatRequest):
            await websocket.send(
                json.dumps(
                    {
                        "type": "result",
                        "data": msgspec.to_builtins(
                            CliRpcResponse(
                                request_id=request.request_id,
                                response=SwitchCLIChatResponse(),
                            )
                        ),
                    }
                )
            )
            return SwitchCLIChat(new_chat_uuid=request.request.new_chat_uuid)
        elif isinstance(request.request, KeepAliveCliChatRequest):
            await websocket.send(
                json.dumps(
                    {
                        "type": "result",
                        "data": msgspec.to_builtins(
                            CliRpcResponse(
                                request_id=request.request_id,
                                response=KeepAliveCliChatResponse(),
                            )
                        ),
                    }
                )
            )
            return None
        else:
            if isinstance(request.request, ToolExecutionRequest) and isinstance(
                request.request.tool_input, BashToolInput
            ):
                await self.add_code_execution_to_halt_states(request.request_id)
            elif isinstance(request.request, BatchToolExecutionRequest):
                # Add halt state if any of the batch tools are bash commands
                if any(
                    isinstance(tool_input, BashToolInput)
                    for tool_input in request.request.tool_inputs
                ):
                    await self.add_code_execution_to_halt_states(request.request_id)

            await requests.put(request)
            return None

    async def _setup_tasks(
        self,
        beats: asyncio.Queue[HeartbeatInfo],
        requests: asyncio.Queue[CliRpcRequest],
        results: asyncio.Queue[CliRpcResponse],
    ) -> list[asyncio.Task[None]]:
        """Setup heartbeat and executor tasks."""

        async def beat() -> None:
            while True:
                info = await self.get_heartbeat_info()
                await beats.put(info)
                await asyncio.sleep(3)

        # Lock to ensure that only one executor can grab a
        # request at a time.
        requests_lock = asyncio.Lock()

        # Lock to ensure that only one executor can put a
        # result in the results queue at a time.
        results_lock = asyncio.Lock()

        async def executor() -> None:
            # We use locks here to protect the request/result
            # queues from being accessed by multiple executors.
            while True:
                async with requests_lock:
                    request = await requests.get()

                try:
                    # if isinstance(request, StreamingCodeExecutionRequest):
                    #     async for streaming_response in self.handle_streaming_request(
                    #         request
                    #     ):
                    #         async with results_lock:
                    #             await results.put(streaming_response)
                    # else:
                    # Note that we don't want to hold the lock here
                    # because we want other executors to be able to
                    # grab requests while we're handling a request.
                    logger.info(f"Handling request {request}")
                    response = await self.handle_request(request)
                    async with results_lock:
                        logger.info(f"Putting response {response}")
                        await results.put(response)
                except Exception as e:
                    logger.info(f"Error handling request {request}:\n\n{e}")
                    try:
                        await send_exception_log(e, session=self.current_session)
                    except Exception:
                        pass
                    async with results_lock:
                        await results.put(
                            CliRpcResponse(
                                request_id=request.request_id,
                                response=ErrorResponse(
                                    error_message=str(e),
                                ),
                            )
                        )

        beat_task = asyncio.create_task(beat())
        # Three parallel executors to handle requests

        executor_tasks = [
            asyncio.create_task(executor()),
            asyncio.create_task(executor()),
            asyncio.create_task(executor()),
        ]

        return [beat_task, *executor_tasks]

    async def _process_websocket_messages(
        self,
        websocket: ClientConnection,
        beats: asyncio.Queue[HeartbeatInfo],
        requests: asyncio.Queue[CliRpcRequest],
        results: asyncio.Queue[CliRpcResponse],
    ) -> REMOTE_EXECUTION_CLIENT_EXIT_INFO:
        """Process messages from the websocket connection."""
        try:
            recv = asyncio.create_task(websocket.recv())
            get_beat = asyncio.create_task(beats.get())
            get_result = asyncio.create_task(results.get())
            pending = {recv, get_beat, get_result}

            while True:
                done, pending = await asyncio.wait(
                    pending, return_when=asyncio.FIRST_COMPLETED
                )

                if recv in done:
                    msg = str(recv.result())
                    exit_info = await self._handle_websocket_message(
                        msg, websocket, requests
                    )
                    if exit_info is not None:
                        return exit_info

                    recv = asyncio.create_task(websocket.recv())
                    pending.add(recv)

                if get_beat in done:
                    info = get_beat.result()
                    data = json.loads(info.model_dump_json())
                    msg = json.dumps({"type": "heartbeat", "data": data})
                    await websocket.send(msg)

                    get_beat = asyncio.create_task(beats.get())
                    pending.add(get_beat)

                if get_result in done:
                    response = get_result.result()
                    data = msgspec.to_builtins(response)
                    msg = json.dumps({"type": "result", "data": data})
                    await websocket.send(msg)

                    get_result = asyncio.create_task(results.get())
                    pending.add(get_result)
        finally:
            for task in pending:
                task.cancel()

            await asyncio.gather(*pending, return_exceptions=True)

    async def _handle_websocket_connection(
        self,
        websocket: ClientConnection,
        connection_tracker: ConnectionTracker | None,
    ) -> REMOTE_EXECUTION_CLIENT_EXIT_INFO | None:
        """Handle a single websocket connection.
        Returns None to continue with reconnection attempts, or an exit info to terminate."""
        if connection_tracker is not None:
            await connection_tracker.set_connected(True)

        self._websocket = websocket

        beats: asyncio.Queue[HeartbeatInfo] = asyncio.Queue()
        requests: asyncio.Queue[CliRpcRequest] = asyncio.Queue()
        results: asyncio.Queue[CliRpcResponse] = asyncio.Queue()

        tasks = await self._setup_tasks(beats, requests, results)

        try:
            return await self._process_websocket_messages(
                websocket, beats, requests, results
            )
        except websockets.exceptions.ConnectionClosed as e:
            if e.rcvd is not None:
                if e.rcvd.code == 1000:
                    # Normal closure, exit completely
                    return WSDisconnected()
                elif e.rcvd.code == 1008:
                    error_message = (
                        "Error connecting to websocket"
                        if e.rcvd.reason is None
                        else e.rcvd.reason
                    )
                    return WSDisconnected(error_message=error_message)
            # Otherwise, allow reconnection attempt
            return None
        except TimeoutError:
            # Timeout, allow reconnection attempt
            # TODO: investgate if this is needed, possibly scope it down
            return None
        finally:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            if connection_tracker is not None:
                await connection_tracker.set_connected(False)

    async def run_connection(
        self,
        chat_uuid: str,
        connection_tracker: ConnectionTracker | None = None,
        timeout_seconds: int | None = None,
    ) -> REMOTE_EXECUTION_CLIENT_EXIT_INFO:
        """Run the websocket connection loop with optional inactivity timeout."""
        self.current_session.set_chat_uuid(chat_uuid)

        # Initialize last request time for timeout monitoring
        self._last_request_time = time.time()

        async for websocket in self.ws_connect(f"/api/ws/chat/{chat_uuid}"):
            # Always run connection and timeout monitor concurrently
            # If timeout_seconds is None, timeout monitor will loop indefinitely
            done, pending = await asyncio.wait(
                [
                    asyncio.create_task(
                        self._handle_websocket_connection(websocket, connection_tracker)
                    ),
                    asyncio.create_task(self._timeout_monitor(timeout_seconds)),
                ],
                return_when=asyncio.FIRST_COMPLETED,
            )

            # Cancel pending tasks
            for task in pending:
                task.cancel()

            # Return result from completed task
            for task in done:
                result = await task
                # If we get None, we'll try to reconnect
                if result is not None:
                    return result

        # If we exit the websocket connection loop without returning,
        # it means we couldn't establish a connection
        return WSDisconnected(error_message="Could not establish websocket connection")

    async def create_chat(self, chat_source: ChatSource) -> CreateChatResponse:
        response = await self.api_client.post(
            "/api/remote_execution/create_chat",
            params={"chat_source": chat_source.value},
        )
        return await deserialize_api_response(response, CreateChatResponse)

    # deprecated
    async def run_workflow(self, chat_uuid: str, workflow_id: str) -> dict[str, Any]:
        response = await self.api_client.post(
            "/api/remote_execution/run_workflow",
            json=RunWorkflowRequest(
                chat_uuid=chat_uuid,
                workflow_id=workflow_id,
            ).model_dump(),
            timeout=60,
        )
        if response.status_code != http_status.OK:
            raise Exception(
                f"Failed to run workflow with status code {response.status_code} and response {response.text}"
            )
        return cast(dict[str, Any], response.json())

    async def trigger_workflow(
        self, workflow_name: str, workflow_input: WorkflowInput
    ) -> WorkflowTriggerResponse:
        response = await self.api_client.post(
            "/api/remote_execution/trigger_workflow",
            json=WorkflowTriggerRequest(
                workflow_name=workflow_name,
                workflow_input=workflow_input,
            ).model_dump(),
        )
        return await deserialize_api_response(response, WorkflowTriggerResponse)

    async def get_heartbeat_info(self) -> HeartbeatInfo:
        return HeartbeatInfo(
            system_info=await system_context.get_system_info(self.working_directory),
            exponent_version=get_installed_version(),
            editable_installation=is_editable_install(),
            cli_uuid=str(cli_uuid),
        )

    async def send_heartbeat(self, chat_uuid: str) -> CLIConnectedState:
        logger.info(f"Sending heartbeat for chat_uuid {chat_uuid}")
        heartbeat_info = await self.get_heartbeat_info()
        response = await self.api_client.post(
            f"/api/remote_execution/{chat_uuid}/heartbeat",
            content=heartbeat_info.model_dump_json(),
            timeout=60,
        )
        if response.status_code != http_status.OK:
            raise Exception(
                f"Heartbeat failed with status code {response.status_code} and response {response.text}"
            )
        connected_state = await deserialize_api_response(response, CLIConnectedState)
        logger.info(f"Heartbeat response: {connected_state}")
        return connected_state

    async def request_upload_url(
        self, s3_key: str, content_type: str
    ) -> GenerateUploadUrlResponse:
        if self._websocket is None:
            raise RuntimeError("No active websocket connection")

        request_id = str(uuid.uuid4())
        request = CliRpcRequest(
            request_id=request_id,
            request=GenerateUploadUrlRequest(s3_key=s3_key, content_type=content_type),
        )

        future: asyncio.Future[GenerateUploadUrlResponse] = asyncio.Future()
        async with self._upload_request_lock:
            self._pending_upload_requests[request_id] = future

        try:
            await self._websocket.send(
                json.dumps({"type": "request", "data": msgspec.to_builtins(request)})
            )

            response = await asyncio.wait_for(future, timeout=30)
            return response
        except TimeoutError:
            async with self._upload_request_lock:
                self._pending_upload_requests.pop(request_id, None)
            raise RuntimeError("Timeout waiting for upload URL response")
        except Exception as e:
            async with self._upload_request_lock:
                self._pending_upload_requests.pop(request_id, None)
            raise e

    async def handle_request(self, request: CliRpcRequest) -> CliRpcResponse:
        # Update last request time for timeout functionality
        self._last_request_time = time.time()

        try:
            if isinstance(request.request, ToolExecutionRequest):
                if isinstance(request.request.tool_input, BashToolInput):
                    raw_result = await execute_bash_tool(
                        request.request.tool_input,
                        self.working_directory,
                        should_halt=self.get_halt_check(request.request_id),
                    )
                else:
                    raw_result = await execute_tool(  # type: ignore[assignment]
                        request.request.tool_input, self.working_directory, self
                    )
                tool_result = truncate_result(raw_result)
                return CliRpcResponse(
                    request_id=request.request_id,
                    response=ToolExecutionResponse(
                        tool_result=tool_result,
                    ),
                )
            elif isinstance(request.request, GetAllFilesRequest):
                files = await file_walk(self.working_directory)
                return CliRpcResponse(
                    request_id=request.request_id,
                    response=GetAllFilesResponse(files=files),
                )
            elif isinstance(request.request, BatchToolExecutionRequest):
                coros: list[Coroutine[Any, Any, ToolResultType]] = []
                for tool_input in request.request.tool_inputs:
                    if isinstance(tool_input, BashToolInput):
                        coros.append(
                            execute_bash_tool(
                                tool_input,
                                self.working_directory,
                                should_halt=self.get_halt_check(request.request_id),
                            )
                        )
                    else:
                        coros.append(
                            execute_tool(tool_input, self.working_directory, self)
                        )

                results: list[ToolResultType | BaseException] = await asyncio.gather(
                    *coros, return_exceptions=True
                )

                processed_results: list[ToolResultType] = []
                for result in results:
                    if not isinstance(result, BaseException):
                        processed_results.append(truncate_result(result))
                    else:
                        processed_results.append(
                            ErrorToolResult(error_message=str(result))
                        )

                return CliRpcResponse(
                    request_id=request.request_id,
                    response=BatchToolExecutionResponse(
                        tool_results=processed_results,
                    ),
                )
            elif isinstance(request.request, HttpRequest):
                http_response = await fetch_http_content(request.request)
                return CliRpcResponse(
                    request_id=request.request_id,
                    response=http_response,
                )
            elif isinstance(request.request, TerminateRequest):
                raise ValueError(
                    "TerminateRequest should not be handled by handle_request"
                )

            elif isinstance(request.request, SwitchCLIChatRequest):
                raise ValueError(
                    "SwitchCLIChatRequest should not be handled by handle_request"
                )
            elif isinstance(request.request, KeepAliveCliChatRequest):
                raise ValueError(
                    "KeepAliveCliChatRequest should not be handled by handle_request"
                )

            raise ValueError(f"Unhandled request type: {type(request)}")

        except Exception as e:
            logger.error(f"Error handling request {request}:\n\n{e}")
            raise e
        finally:
            # Clean up halt state after request is complete
            if isinstance(request.request, ToolExecutionRequest) and isinstance(
                request.request.tool_input, BashToolInput
            ):
                await self.clear_halt_state(request.request_id)
            elif isinstance(request.request, BatchToolExecutionRequest):
                # Clear halt state if any of the batch tools were bash commands
                if any(
                    isinstance(tool_input, BashToolInput)
                    for tool_input in request.request.tool_inputs
                ):
                    await self.clear_halt_state(request.request_id)

    async def handle_streaming_request(
        self, request: StreamingCodeExecutionRequest
    ) -> AsyncGenerator[RemoteExecutionResponseType, None]:
        if not isinstance(request, StreamingCodeExecutionRequest):
            assert False, f"{type(request)} should be sent to handle_streaming_request"
        async for output in execute_code_streaming(
            request,
            self.current_session,
            working_directory=self.working_directory,
            should_halt=self.get_halt_check(request.correlation_id),
        ):
            yield output

    def ws_connect(self, path: str) -> connect:
        base_url = (
            str(self.ws_client.base_url)
            .replace("http://", "ws://")
            .replace("https://", "wss://")
        )

        url = f"{base_url}{path}"
        headers = {"api-key": self.api_client.headers["api-key"]}

        def custom_backoff() -> Generator[float, None, None]:
            yield 0.1  # short initial delay

            delay = 0.5
            while True:
                if delay < 2.0:
                    yield delay
                    delay *= 1.5
                else:
                    yield 2.0

        # Can remove if this is added to public API
        # https://github.com/python-websockets/websockets/issues/1395#issuecomment-3225670409
        asyncio_websockets_client.backoff = custom_backoff  # type: ignore[attr-defined, assignment]

        conn = connect(
            url, additional_headers=headers, open_timeout=10, ping_timeout=10
        )

        return conn

    @staticmethod
    @asynccontextmanager
    async def session(
        api_key: str,
        base_url: str,
        base_ws_url: str,
        working_directory: str,
        file_cache: files.FileCache | None = None,
    ) -> AsyncGenerator[RemoteExecutionClient, None]:
        async with get_session(
            working_directory, base_url, base_ws_url, api_key
        ) as session:
            yield RemoteExecutionClient(session, file_cache)
