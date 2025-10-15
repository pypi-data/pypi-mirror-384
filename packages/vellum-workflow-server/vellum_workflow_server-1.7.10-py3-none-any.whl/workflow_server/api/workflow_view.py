from datetime import datetime
import importlib
import inspect
import json
import logging
from multiprocessing import Event as MultiprocessingEvent, Process, Queue, set_start_method
import os
import pkgutil
from queue import Empty
import sys
import time
import traceback
from uuid import uuid4
from typing import Any, Dict, Generator, Iterator, Optional, Union, cast

from flask import Blueprint, Response, current_app as app, request, stream_with_context
from pydantic import ValidationError
from vellum_ee.workflows.display.nodes.get_node_display_class import get_node_display_class
from vellum_ee.workflows.display.types import WorkflowDisplayContext
from vellum_ee.workflows.display.workflows import BaseWorkflowDisplay
from vellum_ee.workflows.server.virtual_file_loader import VirtualFileFinder

from vellum.workflows.exceptions import WorkflowInitializationException
from vellum.workflows.nodes import BaseNode
from vellum.workflows.vellum_client import create_vellum_client
from workflow_server.config import ENABLE_PROCESS_WRAPPER, MEMORY_LIMIT_MB
from workflow_server.core.events import (
    SPAN_ID_EVENT,
    STREAM_FINISHED_EVENT,
    VEMBDA_EXECUTION_FULFILLED_EVENT_NAME,
    VembdaExecutionFulfilledBody,
    VembdaExecutionFulfilledEvent,
    VembdaExecutionInitiatedBody,
    VembdaExecutionInitiatedEvent,
)
from workflow_server.core.executor import (
    get_random_namespace,
    stream_node_process_timeout,
    stream_workflow,
    stream_workflow_process_timeout,
)
from workflow_server.core.utils import (
    create_vembda_rejected_event,
    is_events_emitting_enabled,
    serialize_vembda_rejected_event,
)
from workflow_server.core.workflow_executor_context import (
    DEFAULT_TIMEOUT_SECONDS,
    NodeExecutorContext,
    WorkflowExecutorContext,
)
from workflow_server.utils.oom_killer import get_is_oom_killed
from workflow_server.utils.system_utils import (
    add_active_span_id,
    get_active_process_count,
    increment_process_count,
    remove_active_span_id,
    wait_for_available_process,
)
from workflow_server.utils.utils import get_version

bp = Blueprint("exec", __name__)
logger = logging.getLogger(__name__)

set_start_method("fork", force=True)

CUSTOM_NODES_DIRECTORY = "vellum_custom_nodes"
WORKFLOW_INITIATION_TIMEOUT_SECONDS = 60


@bp.route("/stream", methods=["POST"])
def stream_workflow_route() -> Response:
    data = request.get_json()

    try:
        context = WorkflowExecutorContext.model_validate(data)
    except ValidationError as e:
        error_message = e.errors()[0]["msg"]
        error_location = e.errors()[0]["loc"]

        return Response(
            json.dumps({"detail": f"Invalid context: {error_message} at {error_location}"}),
            status=400,
            content_type="application/json",
        )

    logger.info(
        f"Starting Workflow Server Request, trace ID: {context.trace_id}, "
        f"process count: {get_active_process_count()}, process wrapper: {ENABLE_PROCESS_WRAPPER}"
    )

    # Create this event up here so timestamps are fully from the start to account for any unknown overhead
    vembda_initiated_event = VembdaExecutionInitiatedEvent(
        id=uuid4(),
        timestamp=datetime.now(),
        trace_id=context.trace_id,
        span_id=context.execution_id,
        body=VembdaExecutionInitiatedBody.model_validate(get_version()),
        parent=None,
    )

    process_output_queue: Queue[Union[str, dict]] = Queue()

    headers = {
        "X-Vellum-SDK-Version": vembda_initiated_event.body.sdk_version,
        "X-Vellum-Server-Version": vembda_initiated_event.body.server_version,
        "X-Vellum-Events-Emitted": str(is_events_emitting_enabled(context)),
    }

    # We can exceed the concurrency count currently with long running workflows due to a knative issue. So here
    # if we detect a memory problem just exit us early
    if not wait_for_available_process():
        return Response(
            json.dumps(
                {
                    "detail": f"Workflow server concurrent request rate exceeded. "
                    f"Process count: {get_active_process_count()}"
                }
            ),
            status=429,
            content_type="application/json",
            headers=headers,
        )

    cancel_signal = MultiprocessingEvent()
    timeout_signal = MultiprocessingEvent()

    process: Optional[Process] = None
    if ENABLE_PROCESS_WRAPPER:
        try:
            process = stream_workflow_process_timeout(
                executor_context=context,
                queue=process_output_queue,
                cancel_signal=cancel_signal,
                timeout_signal=timeout_signal,
            )
            increment_process_count(1)
        except Exception as e:
            logger.exception(e)

            process_output_queue.put(create_vembda_rejected_event(context, traceback.format_exc()))

        try:
            first_item = process_output_queue.get(timeout=WORKFLOW_INITIATION_TIMEOUT_SECONDS)
        except Empty:
            logger.error("Request timed out trying to initiate the Workflow")

            if process and process.is_alive():
                process.kill()
            increment_process_count(-1)

            return Response(
                json.dumps({"detail": "Request timed out trying to initiate the Workflow"}),
                status=408,
                content_type="application/json",
                headers=headers,
            )
    else:

        def workflow_stream_processor() -> Iterator[Union[dict, str]]:
            span_id_emitted = False
            try:
                workflow_iterator, span_id = stream_workflow(
                    context,
                    disable_redirect=True,
                    cancel_signal=cancel_signal,
                    timeout_signal=timeout_signal,
                )
                yield f"{SPAN_ID_EVENT}:{span_id}"
                span_id_emitted = True
                for event in workflow_iterator:
                    yield event
            except Exception as e:
                if not span_id_emitted:
                    yield f"{SPAN_ID_EVENT}:{uuid4()}"

                logger.exception(e)
                yield serialize_vembda_rejected_event(context, "Internal Server Error")

        stream_iterator = workflow_stream_processor()
        first_item = next(stream_iterator)
        increment_process_count(1)

    if not isinstance(first_item, str) or not first_item.startswith(SPAN_ID_EVENT):
        logger.error("Workflow stream did not start with span id event")
        return Response(
            json.dumps({"detail": "Internal Server Error"}),
            status=500,
            content_type="application/json",
            headers=headers,
        )

    span_id = first_item.split(":")[1]
    headers["X-Vellum-Workflow-Span-Id"] = span_id
    add_active_span_id(span_id)

    logger.info(f"Starting Workflow Stream, execution ID: {span_id}, ")

    def process_events(queue: Queue) -> Iterator[Union[str, dict]]:
        event: Union[str, dict]
        loops = 0
        timed_out_time: Optional[float] = None

        while True:
            loops += 1
            # Check if we timed out and kill the process if so. Set the timeout a little under what
            # the default is (30m) since the connection limit is 30m and otherwise we may not receive
            # the timeout event. After cancelling the workflow wait 5 seconds for the workflow to emit
            # any cancel events before ending the stream.
            if (
                min(context.timeout, DEFAULT_TIMEOUT_SECONDS - 90)
                < ((time.time_ns() - context.request_start_time) / 1_000_000_000)
                and not timed_out_time
            ):
                logger.error("Workflow timed out, waiting 5 seconds before ending request...")
                cancel_signal.set()
                # We pass this separate signal in so we can get the vembda time_out flag set to true in the vembda
                # fulfilled event inside of exec. In the future we might have a separate timeout event in wsdk
                timeout_signal.set()
                timed_out_time = time.time()

            if timed_out_time is not None and timed_out_time + 5 < time.time():
                logger.warning("Killing request after workflow timeout")

                if ENABLE_PROCESS_WRAPPER and process and process.is_alive():
                    process.kill()

                if not ENABLE_PROCESS_WRAPPER or process:
                    increment_process_count(-1)
                    remove_active_span_id(span_id)

                yield VembdaExecutionFulfilledEvent(
                    id=uuid4(),
                    timestamp=datetime.now(),
                    trace_id=context.trace_id,
                    span_id=context.execution_id,
                    body=VembdaExecutionFulfilledBody(
                        exit_code=-1,
                        container_overhead_latency=context.container_overhead_latency,
                        timed_out=True,
                    ),
                    parent=None,
                ).model_dump(mode="json")

                break

            if get_is_oom_killed():
                logger.warning("Workflow stream OOM Kill event")

                yield create_vembda_rejected_event(
                    context, f"Organization Workflow server has exceeded {MEMORY_LIMIT_MB}MB memory limit."
                )

                if process and process.is_alive():
                    process.kill()
                if process:
                    increment_process_count(-1)
                    remove_active_span_id(span_id)

                break

            try:
                if ENABLE_PROCESS_WRAPPER:
                    event = queue.get(timeout=0.1)
                else:
                    event = next(stream_iterator)
            except Empty:
                # Emit waiting event if were just sitting around to attempt to keep the line
                # open to trick knative
                if loops % 20 == 0:
                    yield "WAITING"

                    if ENABLE_PROCESS_WRAPPER and process and not process.is_alive():
                        logger.error("Workflow process exited abnormally")

                        yield create_vembda_rejected_event(
                            context, "Internal Server Error, Workflow process exited abnormally"
                        )

                        break

                continue
            except StopIteration:
                break
            except Exception as e:
                logger.exception(e)
                break

            if event == STREAM_FINISHED_EVENT:
                break
            yield event

    workflow_events = process_events(process_output_queue)

    def generator() -> Generator[str, None, None]:
        try:
            yield "\n"
            yield vembda_initiated_event.model_dump_json()
            yield "\n"
            for row in workflow_events:
                yield "\n"
                if isinstance(row, dict):
                    dump = json.dumps(row)
                    yield dump
                else:
                    yield row
                yield "\n"
            # Sometimes the connections get hung after they finish with the vembda fulfilled event
            # if it happens during a knative scale down event. So we emit an END string so that
            # we don't have to do string compares on all the events for performance.
            yield "\n"
            yield "END"
            yield "\n"

            logger.info(
                f"Workflow stream completed, execution ID: {span_id}, process count: {get_active_process_count()}"
            )
        except GeneratorExit:
            # These can happen either from Vembda disconnects (possibily from predict disconnects) or
            # from knative activator gateway timeouts which are caused by idleTimeout or responseStartSeconds
            # being exceeded.
            app.logger.error(
                "Client disconnected in the middle of the Workflow Stream",
                extra={
                    "sentry_tags": {
                        "server_version": vembda_initiated_event.body.server_version,
                        "sdk_version": vembda_initiated_event.body.sdk_version,
                    }
                },
            )
            return
        except Exception as e:
            logger.exception("Error during workflow response stream generator", extra={"error": e})
            yield "\n"
            yield "END"
            yield "\n"
            return
        finally:
            if ENABLE_PROCESS_WRAPPER:
                try:
                    if process and process.is_alive():
                        process.kill()
                    if process:
                        increment_process_count(-1)
                        remove_active_span_id(span_id)
                except Exception as e:
                    logger.error("Failed to kill process", e)
            else:
                increment_process_count(-1)
                remove_active_span_id(span_id)

    resp = Response(
        stream_with_context(generator()),
        status=200,
        content_type="application/x-ndjson",
        headers=headers,
    )
    return resp


@bp.route("/stream-node", methods=["POST"])
def stream_node_route() -> Response:
    data = request.get_json()

    try:
        context = NodeExecutorContext.model_validate(data)
    except ValidationError as e:
        error_message = e.errors()[0]["msg"]
        error_location = e.errors()[0]["loc"]
        return Response(
            json.dumps({"detail": f"Invalid context: {error_message} at {error_location}"}),
            status=400,
            content_type="application/json",
        )

    # Create this event up here so timestamps are fully from the start to account for any unknown overhead
    vembda_initiated_event = VembdaExecutionInitiatedEvent(
        id=uuid4(),
        timestamp=datetime.now(),
        trace_id=context.trace_id,
        span_id=context.execution_id,
        body=VembdaExecutionInitiatedBody.model_validate(get_version()),
        parent=None,
    )

    app.logger.debug(f"Node stream started. Trace ID: {context.trace_id}")

    pebble_queue: Queue[dict] = Queue()
    process = stream_node_process_timeout(
        executor_context=context,
        queue=pebble_queue,
    )

    def node_events() -> Iterator[dict]:
        while True:
            try:
                event = pebble_queue.get(timeout=context.timeout)

            except Empty:
                if not process.is_alive():
                    yield create_vembda_rejected_event(context, "Internal Server Error")
                    break

            yield event
            if event.get("name") == VEMBDA_EXECUTION_FULFILLED_EVENT_NAME:
                break

    def generator() -> Generator[str, None, None]:
        yield json.dumps(vembda_initiated_event.model_dump(mode="json"))

        for row in node_events():
            yield "\n"
            yield json.dumps(row)

    headers = {
        "X-Vellum-SDK-Version": vembda_initiated_event.body.sdk_version,
        "X-Vellum-Server-Version": vembda_initiated_event.body.server_version,
        "X-Vellum-Events-Emitted": str(is_events_emitting_enabled(context)),
    }

    resp = Response(
        stream_with_context(generator()),
        status=200,
        content_type="application/x-ndjson",
        headers=headers,
    )
    return resp


@bp.route("/serialize", methods=["POST"])
def serialize_route() -> Response:
    data = request.get_json()

    files = data.get("files", {})
    workspace_api_key = data.get("workspace_api_key")

    if not files:
        return Response(
            json.dumps({"detail": "No files received"}),
            status=400,
            content_type="application/json",
        )

    client = create_vellum_client(api_key=workspace_api_key)

    # Generate a unique namespace for this serialization request
    namespace = get_random_namespace()
    virtual_finder = VirtualFileFinder(files, namespace)
    try:
        sys.meta_path.append(virtual_finder)
        result = BaseWorkflowDisplay.serialize_module(namespace, client=client, dry_run=True)

        return Response(
            json.dumps(result.model_dump()),
            status=200,
            content_type="application/json",
        )

    except WorkflowInitializationException as e:
        error_message = f"Serialization failed: {str(e)}"
        logger.warning(error_message)
        return Response(
            json.dumps({"detail": error_message}),
            status=400,
            content_type="application/json",
        )

    except Exception as e:
        logger.exception(f"Error during serialization: {str(e)}")
        return Response(
            json.dumps({"detail": f"Serialization failed: {str(e)}"}),
            status=500,
            content_type="application/json",
        )

    finally:
        if virtual_finder in sys.meta_path:
            sys.meta_path.remove(virtual_finder)


@bp.route("/version", methods=["GET"])
def get_version_route() -> tuple[dict, int]:
    resp = get_version()

    try:
        # Discover nodes in the container
        nodes = []

        # Look for custom_nodes directory in the container
        custom_nodes_path = os.path.join(os.getcwd(), CUSTOM_NODES_DIRECTORY)
        if os.path.exists(custom_nodes_path):
            # Add the custom_nodes directory to Python path so we can import from it
            sys.path.append(os.path.dirname(custom_nodes_path))

            # Import all Python files in the custom_nodes directory
            for _, name, _ in pkgutil.iter_modules([custom_nodes_path]):
                try:
                    module = importlib.import_module(f"{CUSTOM_NODES_DIRECTORY}.{name}")
                    for _, obj in inspect.getmembers(module):
                        # Look for classes that inherit from BaseNode
                        if inspect.isclass(obj) and obj != BaseNode and issubclass(obj, BaseNode):
                            node_display_class = get_node_display_class(obj)
                            exec_config_raw = node_display_class().serialize(WorkflowDisplayContext())
                            exec_config = cast(Dict[str, Any], exec_config_raw)
                            config_module = exec_config["definition"]["module"]
                            description = (
                                exec_config["display_data"]["comment"]["value"]
                                if "comment" in exec_config["display_data"]
                                else ""
                            )
                            nodes.append(
                                {
                                    "id": str(uuid4()),
                                    "module": config_module,
                                    "name": obj.__name__,
                                    "label": exec_config["label"],
                                    "description": description,
                                    "exec_config": exec_config,
                                }
                            )
                except Exception as e:
                    logger.warning(f"Failed to load node from module {name}: {str(e)}", exc_info=True)

        resp["nodes"] = nodes
    except Exception as e:
        logger.exception(f"Failed to discover nodes: {str(e)}")
        resp["nodes"] = []

    return resp, 200


def startup_error_generator(
    vembda_initiated_event: VembdaExecutionInitiatedEvent, message: str, context: WorkflowExecutorContext
) -> Generator[str, None, None]:
    try:
        yield "\n"
        yield vembda_initiated_event.model_dump_json()
        yield "\n"
        yield serialize_vembda_rejected_event(context, message)
        yield "\n"
        yield "END"
        yield "\n"

        logger.error("Workflow stream could not start from resource constraints")
    except GeneratorExit:
        app.logger.error(
            "Client disconnected in the middle of the Startup Error Stream",
            extra={
                "sentry_tags": {
                    "server_version": vembda_initiated_event.body.server_version,
                    "sdk_version": vembda_initiated_event.body.sdk_version,
                }
            },
        )
        return
