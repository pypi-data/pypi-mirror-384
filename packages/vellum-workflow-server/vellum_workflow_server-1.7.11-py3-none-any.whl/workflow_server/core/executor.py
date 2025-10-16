from datetime import datetime
import importlib
from io import StringIO
import json
import logging
from multiprocessing import Process, Queue
import os
import random
import string
import sys
from threading import Event as ThreadingEvent
import time
from traceback import format_exc
from uuid import UUID, uuid4
from typing import Any, Callable, Generator, Iterator, Optional, Tuple, Type

from vellum_ee.workflows.display.utils.events import event_enricher
from vellum_ee.workflows.server.virtual_file_loader import VirtualFileFinder

from vellum.workflows import BaseWorkflow
from vellum.workflows.emitters.base import BaseWorkflowEmitter
from vellum.workflows.emitters.vellum_emitter import VellumEmitter
from vellum.workflows.events.exception_handling import stream_initialization_exception
from vellum.workflows.events.types import BaseEvent
from vellum.workflows.exceptions import WorkflowInitializationException
from vellum.workflows.inputs import BaseInputs
from vellum.workflows.nodes import BaseNode
from vellum.workflows.nodes.mocks import MockNodeExecution
from vellum.workflows.resolvers.base import BaseWorkflowResolver
from vellum.workflows.resolvers.resolver import VellumResolver
from vellum.workflows.state.context import WorkflowContext
from vellum.workflows.state.store import EmptyStore
from vellum.workflows.types import CancelSignal
from vellum.workflows.workflows.event_filters import all_workflow_event_filter
from workflow_server.config import LOCAL_DEPLOYMENT, LOCAL_WORKFLOW_MODULE
from workflow_server.core.cancel_workflow import CancelWorkflowWatcherThread
from workflow_server.core.events import (
    SPAN_ID_EVENT,
    STREAM_FINISHED_EVENT,
    VembdaExecutionFulfilledBody,
    VembdaExecutionFulfilledEvent,
)
from workflow_server.core.utils import (
    create_vembda_rejected_event,
    is_events_emitting_enabled,
    serialize_vembda_rejected_event,
)
from workflow_server.core.workflow_executor_context import (
    BaseExecutorContext,
    NodeExecutorContext,
    WorkflowExecutorContext,
)
from workflow_server.utils.log_proxy import redirect_log

logger = logging.getLogger(__name__)


def stream_node_process_timeout(
    executor_context: NodeExecutorContext,
    queue: Queue,
) -> Process:
    node_process = Process(
        target=_stream_node_wrapper,
        args=(executor_context, queue),
    )
    node_process.start()

    if node_process.exitcode is not None:
        queue.put(create_vembda_rejected_event(executor_context, "Internal Server Error", timed_out=True))

    return node_process


def _stream_node_wrapper(executor_context: NodeExecutorContext, queue: Queue) -> None:
    try:
        for event in stream_node(executor_context=executor_context):
            queue.put(event)
    except WorkflowInitializationException as e:
        queue.put(create_vembda_rejected_event(executor_context, e.message))
    except Exception as e:
        logger.exception(e)
        queue.put(create_vembda_rejected_event(executor_context, "Internal Server Error"))


def _stream_workflow_wrapper(
    executor_context: WorkflowExecutorContext,
    queue: Queue,
    cancel_signal: CancelSignal,
    timeout_signal: CancelSignal,
) -> None:
    span_id_emitted = False
    try:
        stream_iterator, span_id = stream_workflow(
            executor_context=executor_context,
            cancel_signal=cancel_signal,
            timeout_signal=timeout_signal,
        )

        queue.put(f"{SPAN_ID_EVENT}:{span_id}")
        span_id_emitted = True

        for event in stream_iterator:
            queue.put(json.dumps(event))

    except Exception as e:
        if not span_id_emitted:
            queue.put(f"{SPAN_ID_EVENT}:{uuid4()}")

        logger.exception(e)
        queue.put(serialize_vembda_rejected_event(executor_context, "Internal Server Error"))

    queue.put(STREAM_FINISHED_EVENT)

    exit(0)


def stream_workflow_process_timeout(
    executor_context: WorkflowExecutorContext,
    queue: Queue,
    cancel_signal: CancelSignal,
    timeout_signal: CancelSignal,
) -> Process:
    workflow_process = Process(
        target=_stream_workflow_wrapper,
        args=(
            executor_context,
            queue,
            cancel_signal,
            timeout_signal,
        ),
    )
    workflow_process.start()

    if workflow_process.exitcode is not None:
        queue.put(create_vembda_rejected_event(executor_context, "Internal Server Error", timed_out=True))

    return workflow_process


def stream_workflow(
    executor_context: WorkflowExecutorContext,
    timeout_signal: CancelSignal,
    cancel_signal: CancelSignal,
    disable_redirect: bool = True,
) -> tuple[Iterator[dict], UUID]:
    cancel_watcher_kill_switch = ThreadingEvent()
    try:
        workflow, namespace = _create_workflow(executor_context)
        workflow_inputs = _get_workflow_inputs(executor_context, workflow.__class__)

        workflow_state = (
            workflow.deserialize_state(
                executor_context.state,
                workflow_inputs=workflow_inputs or BaseInputs(),
            )
            if executor_context.state
            else None
        )
        node_output_mocks = MockNodeExecution.validate_all(
            executor_context.node_output_mocks,
            workflow.__class__,
        )

        cancel_signal = cancel_signal or ThreadingEvent()

        stream = workflow.stream(
            inputs=workflow_inputs,
            state=workflow_state,
            node_output_mocks=node_output_mocks,
            event_filter=all_workflow_event_filter,
            cancel_signal=cancel_signal,
            entrypoint_nodes=[executor_context.node_id] if executor_context.node_id else None,
            previous_execution_id=executor_context.previous_execution_id,
        )
    except WorkflowInitializationException as e:
        cancel_watcher_kill_switch.set()
        initialization_exception_stream = stream_initialization_exception(e)

        def _stream_generator() -> Generator[dict[str, Any], Any, None]:
            for event in initialization_exception_stream:
                yield _dump_event(
                    event=event,
                    executor_context=executor_context,
                )

        return (
            _call_stream(
                executor_context=executor_context,
                stream_generator=_stream_generator,
                disable_redirect=disable_redirect,
                timeout_signal=timeout_signal,
            ),
            initialization_exception_stream.span_id,
        )
    except Exception:
        cancel_watcher_kill_switch.set()
        logger.exception("Failed to generate Workflow Stream")
        raise

    cancel_watcher = CancelWorkflowWatcherThread(
        kill_switch=cancel_watcher_kill_switch,
        execution_id=stream.span_id,
        timeout_seconds=executor_context.timeout,
        vembda_public_url=executor_context.vembda_public_url,
        cancel_signal=cancel_signal,
    )

    try:
        if executor_context.vembda_public_url:
            cancel_watcher.start()
    except Exception:
        logger.exception("Failed to start cancel watcher")

    def call_workflow() -> Generator[dict[str, Any], Any, None]:
        try:
            first = True
            for event in stream:
                if first:
                    executor_context.stream_start_time = time.time_ns()
                    first = False

                yield _dump_event(
                    event=event,
                    executor_context=executor_context,
                )
        except Exception as e:
            logger.exception("Failed to generate event from Workflow Stream")
            raise e
        finally:
            cancel_watcher_kill_switch.set()

        workflow.join()

    return (
        _call_stream(
            executor_context=executor_context,
            stream_generator=call_workflow,
            disable_redirect=disable_redirect,
            timeout_signal=timeout_signal,
        ),
        stream.span_id,
    )


def stream_node(
    executor_context: NodeExecutorContext,
    disable_redirect: bool = True,
) -> Iterator[dict]:
    workflow, namespace = _create_workflow(executor_context)
    Node: Optional[Type[BaseNode]] = None

    for workflow_node in workflow.get_nodes():
        if executor_context.node_id and workflow_node.__id__ == executor_context.node_id:
            Node = workflow_node
            break
        elif (
            executor_context.node_module
            and executor_context.node_name
            and workflow_node.__name__ == executor_context.node_name
            and workflow_node.__module__ == f"{namespace}.{executor_context.node_module}"
        ):
            Node = workflow_node
            break

    if not Node:
        identifier = executor_context.node_id or f"{executor_context.node_module}.{executor_context.node_name}"
        raise WorkflowInitializationException(
            message=f"Node '{identifier}' not found in workflow",
            workflow_definition=workflow.__class__,
        )

    def call_node() -> Generator[dict[str, Any], Any, None]:
        executor_context.stream_start_time = time.time_ns()

        for event in workflow.run_node(Node, inputs=executor_context.inputs):  # type: ignore[arg-type]
            yield event.model_dump(mode="json")

    return _call_stream(
        executor_context=executor_context,
        stream_generator=call_node,
        disable_redirect=disable_redirect,
        timeout_signal=ThreadingEvent(),
    )


def _call_stream(
    executor_context: BaseExecutorContext,
    stream_generator: Callable[[], Generator[dict[str, Any], Any, None]],
    timeout_signal: CancelSignal,
    disable_redirect: bool = True,
) -> Iterator[dict]:
    log_redirect: Optional[StringIO] = None

    if not disable_redirect:
        log_redirect = redirect_log()

    try:
        yield from stream_generator()

        vembda_fulfilled_event = VembdaExecutionFulfilledEvent(
            id=uuid4(),
            timestamp=datetime.now(),
            trace_id=executor_context.trace_id,
            span_id=executor_context.execution_id,
            body=VembdaExecutionFulfilledBody(
                exit_code=0,
                log=log_redirect.getvalue() if log_redirect else "",
                stderr="",
                container_overhead_latency=executor_context.container_overhead_latency,
                timed_out=timeout_signal.is_set(),
            ),
            parent=None,
        )
        yield vembda_fulfilled_event.model_dump(mode="json")

    except Exception:
        vembda_fulfilled_event = VembdaExecutionFulfilledEvent(
            id=uuid4(),
            timestamp=datetime.now(),
            trace_id=executor_context.trace_id,
            span_id=executor_context.execution_id,
            body=VembdaExecutionFulfilledBody(
                exit_code=-1,
                log=log_redirect.getvalue() if log_redirect else "",
                stderr=format_exc(),
                container_overhead_latency=executor_context.container_overhead_latency,
            ),
            parent=None,
        )
        yield vembda_fulfilled_event.model_dump(mode="json")


def _create_workflow(executor_context: BaseExecutorContext) -> Tuple[BaseWorkflow, str]:
    namespace = _get_file_namespace(executor_context)
    if namespace != LOCAL_WORKFLOW_MODULE:
        sys.meta_path.append(VirtualFileFinder(executor_context.files, namespace))

    workflow_context = _create_workflow_context(executor_context)
    Workflow = BaseWorkflow.load_from_module(namespace)
    VembdaExecutionFulfilledEvent.model_rebuild(
        # Not sure why this is needed, but it is required for the VembdaExecutionFulfilledEvent to be
        # properly rebuilt with the recursive types.
        # use flag here to determine which emitter to use
        _types_namespace={
            "BaseWorkflow": BaseWorkflow,
            "BaseNode": BaseNode,
        },
    )

    # Determine whether to enable the Vellum Emitter for event publishing
    use_vellum_emitter = is_events_emitting_enabled(executor_context)
    emitters: list["BaseWorkflowEmitter"] = []
    if use_vellum_emitter:
        emitters = [VellumEmitter()]

    use_vellum_resolver = executor_context.previous_execution_id is not None
    resolvers: list["BaseWorkflowResolver"] = []
    if use_vellum_resolver:
        resolvers = [VellumResolver()]

    # Explicit constructor call to satisfy typing
    workflow = Workflow(
        context=workflow_context,
        store=EmptyStore(),
        emitters=emitters,
        resolvers=resolvers,
    )

    return workflow, namespace


def _create_workflow_context(executor_context: BaseExecutorContext) -> WorkflowContext:
    if executor_context.environment_variables:
        os.environ.update(executor_context.environment_variables)

    namespace = _get_file_namespace(executor_context)

    return WorkflowContext(
        vellum_client=executor_context.vellum_client,
        execution_context=executor_context.execution_context,
        generated_files=executor_context.files,
        namespace=namespace,
    )


def _get_file_namespace(executor_context: BaseExecutorContext) -> str:
    if (
        LOCAL_WORKFLOW_MODULE
        and hasattr(executor_context.execution_context.parent_context, "deployment_name")
        and LOCAL_DEPLOYMENT == executor_context.execution_context.parent_context.deployment_name  # type: ignore
    ):
        return LOCAL_WORKFLOW_MODULE

    if executor_context.execution_id:
        return str(executor_context.execution_id)

    return get_random_namespace()


def get_random_namespace() -> str:
    return "workflow_tmp_" + "".join(random.choice(string.ascii_letters + string.digits) for i in range(14))


def _dump_event(event: BaseEvent, executor_context: BaseExecutorContext) -> dict:
    module_base = executor_context.module.split(".")
    dump = event.model_dump(
        mode="json", context={"event_enricher": lambda event: event_enricher(event, executor_context.vellum_client)}
    )
    if dump["name"] in {
        "workflow.execution.initiated",
        "workflow.execution.fulfilled",
        "workflow.execution.rejected",
        "workflow.execution.streaming",
        "workflow.execution.paused",
        "workflow.execution.resumed",
    }:
        dump["body"]["workflow_definition"]["module"] = module_base + dump["body"]["workflow_definition"]["module"][1:]
    elif dump["name"] in {
        "node.execution.initiated",
        "node.execution.fulfilled",
        "node.execution.rejected",
        "node.execution.streaming",
        "node.execution.paused",
        "node.execution.resumed",
    }:
        dump["body"]["node_definition"]["module"] = module_base + dump["body"]["node_definition"]["module"][1:]

    return dump


def _get_workflow_inputs(
    executor_context: BaseExecutorContext, workflow_class: Type[BaseWorkflow]
) -> Optional[BaseInputs]:
    if not executor_context.inputs:
        return None

    if not executor_context.files.get("inputs.py"):
        return None

    namespace = _get_file_namespace(executor_context)
    inputs_module_path = f"{namespace}.inputs"
    try:
        inputs_module = importlib.import_module(inputs_module_path)
    except Exception as e:
        raise WorkflowInitializationException(
            message=f"Failed to initialize workflow inputs: {e}",
            workflow_definition=workflow_class,
        ) from e

    if not hasattr(inputs_module, "Inputs"):
        raise WorkflowInitializationException(
            message=f"Inputs module {inputs_module_path} does not have a required Inputs class",
            workflow_definition=workflow_class,
        )

    if not issubclass(inputs_module.Inputs, BaseInputs):
        raise WorkflowInitializationException(
            message=f"""The class {inputs_module_path}.Inputs was expected to be a subclass of BaseInputs, \
but found {inputs_module.Inputs.__class__.__name__}""",
            workflow_definition=workflow_class,
        )

    return inputs_module.Inputs(**executor_context.inputs)
