import pytest
from contextlib import redirect_stdout
from importlib.metadata import version
import io
import json
from queue import Empty
import re
from unittest import mock
from uuid import uuid4

import requests_mock

from vellum.workflows.emitters.base import WorkflowEvent
from vellum.workflows.emitters.vellum_emitter import VellumEmitter
from workflow_server.code_exec_runner import run_code_exec_stream
from workflow_server.server import create_app
from workflow_server.utils.system_utils import get_active_process_count


def flask_stream(request_body: dict) -> tuple[int, list]:
    flask_app = create_app()
    with flask_app.test_client() as test_client:
        response = test_client.post("/workflow/stream", json=request_body)
        status_code = response.status_code

        return status_code, [
            json.loads(line)
            for line in response.data.decode().split("\n")
            if line
            and line
            not in [
                "WAITING",
                "END",
            ]
        ]


@mock.patch("workflow_server.api.workflow_view.ENABLE_PROCESS_WRAPPER", False)
def flask_stream_disable_process_wrapper(request_body: dict) -> tuple[int, list]:
    flask_app = create_app()
    with flask_app.test_client() as test_client:
        response = test_client.post("/workflow/stream", json=request_body)
        status_code = response.status_code

        return status_code, [
            json.loads(line)
            for line in response.data.decode().split("\n")
            if line
            and line
            not in [
                "WAITING",
                "END",
            ]
        ]


def code_exec_stream(request_body: dict) -> tuple[int, list]:
    output = io.StringIO()

    with mock.patch("os.read") as mocked_os_read, redirect_stdout(output):
        mocked_os_read.return_value = (json.dumps(request_body) + "\n--vellum-input-stop--\n").encode("utf-8")
        run_code_exec_stream()

    lines = output.getvalue().split("\n")
    events = []
    for line in lines:
        if "--event--" in line:
            events.append(json.loads(line.replace("--event--", "")))

    return 200, events


@pytest.fixture(params=[flask_stream, code_exec_stream, flask_stream_disable_process_wrapper])
def both_stream_types(request):
    return request.param


def test_stream_workflow_flask_route__verify_headers():
    # GIVEN a valid request body
    span_id = uuid4()
    request_body = {
        "execution_id": str(span_id),
        "inputs": [],
        "environment_api_key": "test",
        "module": "workflow",
        "timeout": 360,
        "files": {
            "__init__.py": "",
            "workflow.py": """\
from vellum.workflows import BaseWorkflow

class Workflow(BaseWorkflow):
    pass
""",
        },
    }

    # WHEN we call the stream route
    flask_app = create_app()
    with flask_app.test_client() as test_client:
        response = test_client.post("/workflow/stream", json=request_body)
        status_code = response.status_code

    # THEN we get a 200 response
    assert status_code == 200, response.text

    # AND the version headers are present
    assert "X-Vellum-SDK-Version" in response.headers
    assert "X-Vellum-Server-Version" in response.headers
    assert "X-Vellum-Workflow-Span-Id" in response.headers


def test_stream_workflow_route__happy_path(both_stream_types):
    # GIVEN a valid request body
    span_id = uuid4()
    request_body = {
        "execution_id": str(span_id),
        "inputs": [],
        "environment_api_key": "test",
        "module": "test",
        "timeout": 360,
        "files": {
            "__init__.py": "",
            "workflow.py": """\
from vellum.workflows import BaseWorkflow

class Workflow(BaseWorkflow):
    class Outputs(BaseWorkflow.Outputs):
        foo = "hello"
""",
        },
    }

    # WHEN we call the stream route
    status_code, events = both_stream_types(request_body)

    # THEN we get a 200 response
    assert status_code == 200, events

    # THEN we get the expected events
    assert events[0] == {
        "id": mock.ANY,
        "trace_id": mock.ANY,
        "span_id": str(span_id),
        "timestamp": mock.ANY,
        "api_version": "2024-10-25",
        "parent": None,
        "links": None,
        "name": "vembda.execution.initiated",
        "body": {
            "sdk_version": version("vellum-ai"),
            "server_version": "local",
        },
    }

    assert events[1]["name"] == "workflow.execution.initiated", events[1]
    assert events[1]["body"]["workflow_definition"]["module"] == ["test", "workflow"]
    assert "display_context" in events[1]["body"], events[1]["body"]
    display_context = events[1]["body"]["display_context"]
    assert "node_displays" in display_context
    assert "workflow_inputs" in display_context
    assert "workflow_outputs" in display_context
    assert isinstance(display_context["node_displays"], dict)
    assert isinstance(display_context["workflow_inputs"], dict)
    assert isinstance(display_context["workflow_outputs"], dict)
    assert "foo" in display_context["workflow_outputs"]
    assert events[2]["name"] == "workflow.execution.fulfilled", events[2]
    assert events[2]["body"]["workflow_definition"]["module"] == ["test", "workflow"]

    assert events[3] == {
        "id": mock.ANY,
        "trace_id": events[0]["trace_id"],
        "span_id": str(span_id),
        "timestamp": mock.ANY,
        "api_version": "2024-10-25",
        "parent": None,
        "links": None,
        "name": "vembda.execution.fulfilled",
        "body": mock.ANY,
    }
    assert events[3]["body"] == {
        "exit_code": 0,
        "log": "",
        "stderr": "",
        "timed_out": False,
        "container_overhead_latency": mock.ANY,
    }

    assert len(events) == 4


def test_stream_workflow_route__happy_path_with_inputs(both_stream_types):
    # GIVEN a valid request body
    span_id = uuid4()
    request_body = {
        "timeout": 360,
        "execution_id": str(span_id),
        "inputs": [
            {"name": "foo", "type": "STRING", "value": "hello"},
        ],
        "environment_api_key": "test",
        "module": "workflow",
        "files": {
            "__init__.py": "",
            "workflow.py": """\
from vellum.workflows import BaseWorkflow
from vellum.workflows.state import BaseState
from .inputs import Inputs

class Workflow(BaseWorkflow[Inputs, BaseState]):
    class Outputs(BaseWorkflow.Outputs):
        foo = "hello"
""",
            "inputs.py": """\
from vellum.workflows.inputs import BaseInputs

class Inputs(BaseInputs):
    foo: str
""",
        },
    }

    # WHEN we call the stream route
    status_code, events = both_stream_types(request_body)

    # THEN we get a 200 response
    assert status_code == 200, events

    # THEN we get the expected events
    assert events[0] == {
        "id": mock.ANY,
        "trace_id": mock.ANY,
        "span_id": str(span_id),
        "timestamp": mock.ANY,
        "api_version": "2024-10-25",
        "parent": None,
        "links": None,
        "name": "vembda.execution.initiated",
        "body": {
            "sdk_version": version("vellum-ai"),
            "server_version": "local",
        },
    }

    assert events[1]["name"] == "workflow.execution.initiated", events[1]
    assert "display_context" in events[1]["body"], events[1]["body"]
    display_context = events[1]["body"]["display_context"]
    assert "node_displays" in display_context
    assert "workflow_inputs" in display_context
    assert "workflow_outputs" in display_context
    assert isinstance(display_context["node_displays"], dict)
    assert isinstance(display_context["workflow_inputs"], dict)
    assert isinstance(display_context["workflow_outputs"], dict)
    assert "foo" in display_context["workflow_inputs"]
    assert "foo" in display_context["workflow_outputs"]
    assert events[2]["name"] == "workflow.execution.fulfilled", events[2]

    assert events[3] == {
        "id": mock.ANY,
        "trace_id": events[0]["trace_id"],
        "span_id": str(span_id),
        "timestamp": mock.ANY,
        "api_version": "2024-10-25",
        "parent": None,
        "links": None,
        "name": "vembda.execution.fulfilled",
        "body": mock.ANY,
    }
    assert events[3]["body"] == {
        "exit_code": 0,
        "log": "",
        "stderr": "",
        "timed_out": False,
        "container_overhead_latency": mock.ANY,
    }

    assert len(events) == 4


def test_stream_workflow_route__happy_path_with_state(both_stream_types):
    # GIVEN a valid request body
    span_id = uuid4()
    request_body = {
        "timeout": 360,
        "execution_id": str(span_id),
        "state": {"foo": "bar"},
        "environment_api_key": "test",
        "module": "workflow",
        "files": {
            "__init__.py": "",
            "workflow.py": """\
from vellum.workflows import BaseWorkflow
from vellum.workflows.inputs import BaseInputs
from .state import State

class Workflow(BaseWorkflow[BaseInputs, State]):
    class Outputs(BaseWorkflow.Outputs):
        foo = State.foo
""",
            "state.py": """\
from vellum.workflows.state import BaseState

class State(BaseState):
    foo: str
""",
        },
    }

    # WHEN we call the stream route
    status_code, events = both_stream_types(request_body)

    # THEN we get a 200 response
    assert status_code == 200, events

    # THEN we get the expected events
    assert events[0] == {
        "id": mock.ANY,
        "trace_id": mock.ANY,
        "span_id": str(span_id),
        "timestamp": mock.ANY,
        "api_version": "2024-10-25",
        "parent": None,
        "links": None,
        "name": "vembda.execution.initiated",
        "body": {
            "sdk_version": version("vellum-ai"),
            "server_version": "local",
        },
    }

    assert events[1]["name"] == "workflow.execution.initiated", events[1]
    assert "display_context" in events[1]["body"], events[1]["body"]
    display_context = events[1]["body"]["display_context"]
    assert "node_displays" in display_context
    assert "workflow_inputs" in display_context
    assert "workflow_outputs" in display_context
    assert isinstance(display_context["node_displays"], dict)
    assert isinstance(display_context["workflow_inputs"], dict)
    assert isinstance(display_context["workflow_outputs"], dict)
    assert "foo" in display_context["workflow_outputs"]
    assert events[2]["name"] == "workflow.execution.fulfilled", events[2]
    assert events[2]["body"]["outputs"] == {"foo": "bar"}

    assert events[3] == {
        "id": mock.ANY,
        "trace_id": events[0]["trace_id"],
        "span_id": str(span_id),
        "timestamp": mock.ANY,
        "api_version": "2024-10-25",
        "parent": None,
        "links": None,
        "name": "vembda.execution.fulfilled",
        "body": mock.ANY,
    }
    assert events[3]["body"] == {
        "exit_code": 0,
        "log": "",
        "stderr": "",
        "timed_out": False,
        "container_overhead_latency": mock.ANY,
    }

    assert len(events) == 4


def test_stream_workflow_route__bad_indent_in_inputs_file(both_stream_types):
    # GIVEN a valid request body
    span_id = uuid4()
    request_body = {
        "timeout": 360,
        "execution_id": str(span_id),
        "inputs": [
            {"name": "foo", "type": "STRING", "value": "hello"},
        ],
        "environment_api_key": "test",
        "module": "workflow",
        "files": {
            "__init__.py": "",
            "workflow.py": """\
from vellum.workflows import BaseWorkflow
from vellum.workflows.state import BaseState
from .inputs import Inputs

class Workflow(BaseWorkflow[Inputs, BaseState]):
    class Outputs(BaseWorkflow.Outputs):
        foo = "hello"
""",
            "inputs.py": """\
from vellum.workflows.inputs import BaseInputs

  class Inputs(BaseInputs):
     foo: str
""",
        },
    }

    # WHEN we call the stream route
    status_code, events = both_stream_types(request_body)

    # THEN we get a 200 response
    assert status_code == 200, events

    # THEN we get the expected events: vembda initiated, workflow initiated, workflow rejected, vembda fulfilled
    assert len(events) == 4

    assert events[0] == {
        "id": mock.ANY,
        "trace_id": mock.ANY,
        "span_id": str(span_id),
        "timestamp": mock.ANY,
        "api_version": "2024-10-25",
        "parent": None,
        "links": None,
        "name": "vembda.execution.initiated",
        "body": {
            "sdk_version": version("vellum-ai"),
            "server_version": "local",
        },
    }

    assert events[1]["name"] == "workflow.execution.initiated"

    assert events[2]["name"] == "workflow.execution.rejected"
    assert events[2]["span_id"] == events[1]["span_id"]
    assert (
        "Syntax Error raised while loading Workflow: "
        "unexpected indent (inputs.py, line 3)" in events[2]["body"]["error"]["message"]
    )

    assert events[3] == {
        "id": mock.ANY,
        "trace_id": events[0]["trace_id"],
        "span_id": str(span_id),
        "timestamp": mock.ANY,
        "api_version": "2024-10-25",
        "parent": None,
        "links": None,
        "name": "vembda.execution.fulfilled",
        "body": mock.ANY,
    }
    assert events[3]["body"] == {
        "exit_code": 0,
        "log": "",
        "stderr": "",
        "timed_out": False,
        "container_overhead_latency": mock.ANY,
    }


def test_stream_workflow_route__invalid_inputs_initialization_events(both_stream_types):
    """
    Tests that invalid inputs initialization gets us back a workflow initiated and workflow rejected event.
    """
    # GIVEN a valid request body with valid inputs file but omitting required input to cause
    # WorkflowInitializationException
    span_id = uuid4()
    request_body = {
        "timeout": 360,
        "execution_id": str(span_id),
        "inputs": [
            # Omit the required input to trigger WorkflowInitializationException
        ],
        "environment_api_key": "test",
        "module": "workflow",
        "files": {
            "__init__.py": "",
            "workflow.py": """\
from vellum.workflows import BaseWorkflow
from vellum.workflows.state import BaseState
from .inputs import Inputs

class Workflow(BaseWorkflow[Inputs, BaseState]):
    class Outputs(BaseWorkflow.Outputs):
        foo = "hello"
""",
            "inputs.py": """\
from vellum.workflows.inputs import BaseInputs

class Inputs(BaseInputs):
    foo: str
""",
        },
    }

    # WHEN we call the stream route
    status_code, events = both_stream_types(request_body)

    # THEN we get a 200 response
    assert status_code == 200, events

    # THEN we get the expected events: vembda initiated, workflow initiated, workflow rejected, vembda fulfilled
    assert len(events) == 4

    # AND the first event should be vembda execution initiated
    assert events[0]["name"] == "vembda.execution.initiated"
    assert events[0]["span_id"] == str(span_id)

    # AND the second event should be workflow execution initiated
    assert events[1]["name"] == "workflow.execution.initiated"

    # AND the third event should be workflow execution rejected
    assert events[2]["name"] == "workflow.execution.rejected"
    assert events[1]["span_id"] == events[2]["span_id"]
    assert "Required input variables foo should have defined value" in events[2]["body"]["error"]["message"]

    # AND the fourth event should be vembda execution fulfilled
    assert events[3]["name"] == "vembda.execution.fulfilled"
    assert events[3]["span_id"] == str(span_id)
    assert events[3]["body"]["exit_code"] == 0


@pytest.mark.parametrize(
    ["execute_workflow_stream", "assert_last_request"],
    [
        (flask_stream, False),  # Unfortunately, can't make assertions on requests made in a subprocess.
        (code_exec_stream, True),
        (flask_stream_disable_process_wrapper, True),
    ],
    ids=["flask_stream", "code_exec_stream", "flask_stream_disable_process_wrapper"],
)
def test_stream_workflow_route__cancel(execute_workflow_stream, assert_last_request):
    # GIVEN a valid request body
    span_id = uuid4()
    request_body = {
        "timeout": 360,
        "execution_id": str(span_id),
        "inputs": [],
        "environment_api_key": "test",
        "module": "workflow",
        "vembda_public_url": "http://test.biz",
        "files": {
            "__init__.py": "",
            "workflow.py": """\
import time

from vellum.workflows.nodes.bases.base import BaseNode
from vellum.workflows.workflows.base import BaseWorkflow


class StartNode(BaseNode):
    class Outputs(BaseNode.Outputs):
        value: str

    def run(self) -> Outputs:
        time.sleep(2)
        return self.Outputs(value="hello world")


class BasicCancellableWorkflow(BaseWorkflow):
    graph = StartNode
    class Outputs(BaseWorkflow.Outputs):
        final_value = StartNode.Outputs.value

""",
        },
    }

    # WHEN we call the stream route with a mock cancelled return true
    with requests_mock.Mocker() as mocker:
        response_mock = mocker.get(
            re.compile("http://test.biz/vembda-public/cancel-workflow-execution-status"), json={"cancelled": True}
        )
        status_code, events = execute_workflow_stream(request_body)

    # THEN we get a 200 response
    assert status_code == 200, events

    # THEN we get the expected cancelled events
    assert events[0] == {
        "id": mock.ANY,
        "trace_id": mock.ANY,
        "span_id": str(span_id),
        "timestamp": mock.ANY,
        "api_version": "2024-10-25",
        "parent": None,
        "links": None,
        "name": "vembda.execution.initiated",
        "body": {
            "sdk_version": version("vellum-ai"),
            "server_version": "local",
        },
    }

    assert events[1]["name"] == "workflow.execution.initiated", events[1]
    assert "display_context" in events[1]["body"], events[1]["body"]

    cancelled_event = events[-2]
    assert cancelled_event["name"] == "workflow.execution.rejected"
    assert cancelled_event["body"]["error"]["message"] == "Workflow run cancelled"

    # AND we called the cancel endpoint with the correct execution id
    workflow_span_id = events[1]["span_id"]
    if assert_last_request:
        assert response_mock.last_request
        assert (
            response_mock.last_request.url
            == f"http://test.biz/vembda-public/cancel-workflow-execution-status/{workflow_span_id}"
        )


def test_stream_workflow_route__timeout_emits_rejection_events():
    """
    Tests that when a workflow times out, we emit node and workflow rejection events.
    """

    span_id = uuid4()
    request_body = {
        "timeout": 1,
        "execution_id": str(span_id),
        "inputs": [],
        "environment_api_key": "test",
        "module": "workflow",
        "files": {
            "__init__.py": "",
            "workflow.py": """\
import time

from vellum.workflows.nodes.bases.base import BaseNode
from vellum.workflows.workflows.base import BaseWorkflow


class LongRunningNode(BaseNode):
    class Outputs(BaseNode.Outputs):
        value: str

    def run(self) -> Outputs:
        time.sleep(30)
        return self.Outputs(value="hello world")


class TimeoutWorkflow(BaseWorkflow):
    graph = LongRunningNode
    class Outputs(BaseWorkflow.Outputs):
        final_value = LongRunningNode.Outputs.value

""",
        },
    }

    status_code, events = flask_stream(request_body)

    assert status_code == 200

    event_names = [e["name"] for e in events]

    assert "vembda.execution.initiated" in event_names
    assert "workflow.execution.initiated" in event_names
    assert "node.execution.initiated" in event_names

    assert "node.execution.rejected" in event_names, "Should emit node.execution.rejected on timeout"
    node_execution_rejected = next(e for e in events if e["name"] == "node.execution.rejected")
    assert "vellum/workflows/runner/runner.py" in node_execution_rejected["body"]["stacktrace"]

    assert "workflow.execution.rejected" in event_names, "Should emit workflow.execution.rejected on timeout"
    workflow_execution_rejected = next(e for e in events if e["name"] == "workflow.execution.rejected")
    assert "vellum/workflows/runner/runner.py" in workflow_execution_rejected["body"]["stacktrace"]

    assert "vembda.execution.fulfilled" in event_names
    vembda_fulfilled = next(e for e in events if e["name"] == "vembda.execution.fulfilled")
    assert vembda_fulfilled["body"]["timed_out"] is True


def test_stream_workflow_route__very_large_events(both_stream_types):
    # GIVEN a valid request body
    span_id = uuid4()
    request_body = {
        "execution_id": str(span_id),
        "inputs": [
            {"name": "foo", "type": "STRING", "value": "hello" * 10_000_000},
        ],
        "environment_api_key": "test",
        "module": "workflow",
        "files": {
            "__init__.py": "",
            "workflow.py": """\
from vellum.workflows import BaseWorkflow
from vellum.workflows.state import BaseState
from .inputs import Inputs

class Workflow(BaseWorkflow[Inputs, BaseState]):
    class Outputs(BaseWorkflow.Outputs):
        foo = "hello"
""",
            "inputs.py": """\
from vellum.workflows.inputs import BaseInputs

class Inputs(BaseInputs):
    foo: str
""",
        },
    }

    # WHEN we call the stream route
    status_code, events = both_stream_types(request_body)

    # THEN we get a 200 response
    assert status_code == 200, events

    # THEN we get the expected events
    assert events[0] == {
        "id": mock.ANY,
        "trace_id": mock.ANY,
        "span_id": str(span_id),
        "timestamp": mock.ANY,
        "api_version": "2024-10-25",
        "parent": None,
        "links": None,
        "name": "vembda.execution.initiated",
        "body": {
            "sdk_version": version("vellum-ai"),
            "server_version": "local",
        },
    }

    assert events[1]["name"] == "workflow.execution.initiated", events[1]
    assert "display_context" in events[1]["body"], events[1]["body"]
    assert events[2]["name"] == "workflow.execution.fulfilled", events[2]

    assert events[3] == {
        "id": mock.ANY,
        "trace_id": events[0]["trace_id"],
        "span_id": str(span_id),
        "timestamp": mock.ANY,
        "api_version": "2024-10-25",
        "parent": None,
        "links": None,
        "name": "vembda.execution.fulfilled",
        "body": mock.ANY,
    }
    assert events[3]["body"] == {
        "exit_code": 0,
        "log": "",
        "stderr": "",
        "timed_out": False,
        "container_overhead_latency": mock.ANY,
    }

    assert len(events) == 4


def test_stream_workflow_route__happy_path_run_from_node(both_stream_types):
    # GIVEN a valid request body representing a run from a node
    node_id = uuid4()
    span_id = uuid4()
    request_body = {
        "timeout": 360,
        "execution_id": str(span_id),
        "node_id": str(node_id),
        "environment_api_key": "test",
        "module": "workflow",
        "files": {
            "__init__.py": "from .display import *",
            "workflow.py": """\
from vellum.workflows import BaseWorkflow
from .nodes.start import StartNode
from .nodes.end import EndNode

class Workflow(BaseWorkflow):
    graph = StartNode >> EndNode

    class Outputs(BaseWorkflow.Outputs):
        foo = EndNode.Outputs.value
""",
            "nodes/__init__.py": """
from .start import StartNode
from .end import EndNode

__all__ = ["StartNode", "EndNode"]
""",
            "nodes/start.py": """\
from vellum.workflows.nodes import BaseNode

class StartNode(BaseNode):
    class Outputs(BaseNode.Outputs):
        value = "apple"
""",
            "nodes/end.py": """\
from vellum.workflows.nodes import BaseNode
from .start import StartNode

class EndNode(BaseNode):
    class Outputs(BaseNode.Outputs):
        value = StartNode.Outputs.value.coalesce("banana")
""",
            "display/__init__.py": """
from .nodes import *
from .workflow import *
""",
            "display/workflow.py": """
from uuid import UUID
from vellum_ee.workflows.display.workflows import BaseWorkflowDisplay
from vellum_ee.workflows.display.base import EdgeDisplay
from ..nodes.start import StartNode
from ..nodes.end import EndNode

class WorkflowDisplay(BaseWorkflowDisplay):
    edge_displays = {
        (StartNode.Ports.default, EndNode): EdgeDisplay(
            id=UUID("63606ff1-1c70-4516-92c6-cbaba9336424")
        ),
    }
""",
            "display/nodes/__init__.py": """
from .start import StartNodeDisplay
from .end import EndNodeDisplay

__all__ = ["StartNodeDisplay", "EndNodeDisplay"]
""",
            "display/nodes/start.py": """\
from vellum_ee.workflows.display.nodes import BaseNodeDisplay
from ...nodes.start import StartNode

class StartNodeDisplay(BaseNodeDisplay[StartNode]):
    pass
""",
            "display/nodes/end.py": f"""\
from uuid import UUID

from vellum_ee.workflows.display.nodes import BaseNodeDisplay
from ...nodes.end import EndNode

class EndNodeDisplay(BaseNodeDisplay[EndNode]):
    node_id = UUID("{node_id}")
""",
        },
    }

    # WHEN we call the stream route
    status_code, events = both_stream_types(request_body)

    # THEN we get a 200 response
    assert status_code == 200, events

    # THEN we get the expected workflow and node fulfilled events
    assert events[-4]["name"] == "node.execution.fulfilled", json.dumps(events[-1])
    assert events[-4]["body"]["node_definition"]["id"] == str(node_id)
    assert events[-2]["name"] == "workflow.execution.fulfilled", json.dumps(events[-1])
    assert events[-2]["body"]["outputs"] == {"foo": "banana"}
    assert [event["name"] for event in events] == [
        "vembda.execution.initiated",
        "workflow.execution.initiated",
        "node.execution.initiated",
        "workflow.execution.snapshotted",
        "node.execution.fulfilled",
        "workflow.execution.streaming",
        "workflow.execution.fulfilled",
        "vembda.execution.fulfilled",
    ]


def test_stream_workflow_route__happy_path_run_from_node_with_state(both_stream_types):
    # GIVEN a valid request body representing a run from a node with state
    node_id = uuid4()
    span_id = uuid4()
    request_body = {
        "timeout": 360,
        "execution_id": str(span_id),
        "node_id": str(node_id),
        "environment_api_key": "test",
        "module": "workflow",
        "state": {"meta": {"node_outputs": {"StartNode.Outputs.value": "cherry"}}},
        "files": {
            "__init__.py": "from .display import *",
            "workflow.py": """\
from vellum.workflows import BaseWorkflow
from .nodes.start import StartNode
from .nodes.end import EndNode

class Workflow(BaseWorkflow):
    graph = StartNode >> EndNode

    class Outputs(BaseWorkflow.Outputs):
        foo = EndNode.Outputs.value
""",
            "nodes/__init__.py": """
from .start import StartNode
from .end import EndNode

__all__ = ["StartNode", "EndNode"]
""",
            "nodes/start.py": """\
import random
from vellum.workflows.nodes import BaseNode

class StartNode(BaseNode):
    class Outputs(BaseNode.Outputs):
        value = str
    def run(self) -> Outputs:
        return self.Outputs(value=random.choice(["apple", "banana", "cherry"]))
""",
            "nodes/end.py": """\
from vellum.workflows.nodes import BaseNode
from .start import StartNode

class EndNode(BaseNode):
    fruit = StartNode.Outputs.value.coalesce("date")

    class Outputs(BaseNode.Outputs):
        value: str

    def run(self) -> Outputs:
        return self.Outputs(value=self.fruit)
""",
            "display/__init__.py": """
from .nodes import *
from .workflow import *
""",
            "display/workflow.py": """
from uuid import UUID
from vellum_ee.workflows.display.workflows import BaseWorkflowDisplay
from vellum_ee.workflows.display.base import EdgeDisplay
from ..nodes.start import StartNode
from ..nodes.end import EndNode

class WorkflowDisplay(BaseWorkflowDisplay):
    edge_displays = {
        (StartNode.Ports.default, EndNode): EdgeDisplay(
            id=UUID("63606ff1-1c70-4516-92c6-cbaba9336424")
        ),
    }
""",
            "display/nodes/__init__.py": """
from .start import StartNodeDisplay
from .end import EndNodeDisplay

__all__ = ["StartNodeDisplay", "EndNodeDisplay"]
""",
            "display/nodes/start.py": """\
from vellum_ee.workflows.display.nodes import BaseNodeDisplay
from ...nodes.start import StartNode

class StartNodeDisplay(BaseNodeDisplay[StartNode]):
    pass
""",
            "display/nodes/end.py": f"""\
from uuid import UUID

from vellum_ee.workflows.display.nodes import BaseNodeDisplay
from ...nodes.end import EndNode

class EndNodeDisplay(BaseNodeDisplay[EndNode]):
    node_id = UUID("{node_id}")
""",
        },
    }

    # WHEN we call the stream route
    status_code, events = both_stream_types(request_body)

    # THEN we get a 200 response
    assert status_code == 200, events

    # THEN we get the expected workflow and node initiated events
    assert len(events) > 3, json.dumps(events[-1])
    assert events[2]["name"] == "node.execution.initiated", json.dumps(events[-1])
    assert events[2]["body"]["inputs"] == {"fruit": "cherry"}


@mock.patch("workflow_server.api.workflow_view.wait_for_available_process")
def test_stream_workflow_route__concurrent_request_rate_exceeded(mock_wait_for_available_process):
    # GIVEN a valid request body
    span_id = uuid4()
    request_body = {
        "execution_id": str(span_id),
        "inputs": [],
        "workspace_api_key": "test",
        "environment_api_key": "test",
        "module": "workflow",
        "timeout": 360,
        "files": {
            "__init__.py": "",
            "workflow.py": """\
from vellum.workflows import BaseWorkflow

class Workflow(BaseWorkflow):
    class Outputs(BaseWorkflow.Outputs):
        foo = "hello"
""",
        },
    }

    # AND wait_for_available_process returns False
    mock_wait_for_available_process.return_value = False

    # WHEN we call the stream route
    status_code, events = flask_stream(request_body)

    # THEN we get a 429 response
    assert status_code == 429, events

    # AND we get a simple JSON error response
    assert len(events) == 1
    assert events[0] == {
        "detail": f"Workflow server concurrent request rate exceeded. Process count: {get_active_process_count()}"
    }


def test_stream_workflow_route__with_environment_variables(both_stream_types):
    # GIVEN a valid request body with environment variables
    span_id = uuid4()
    request_body = {
        "execution_id": str(span_id),
        "inputs": [],
        "environment_api_key": "test",
        "module": "workflow",
        "timeout": 360,
        "environment_variables": {"TEST_ENV_VAR": "test_value", "ANOTHER_VAR": "another_value"},
        "files": {
            "__init__.py": "",
            "workflow.py": """\
from vellum.workflows import BaseWorkflow
from vellum.workflows.references import EnvironmentVariableReference

class Workflow(BaseWorkflow):
    class Outputs(BaseWorkflow.Outputs):
        env_var_value = EnvironmentVariableReference(name="TEST_ENV_VAR", default="not_found")
        another_var_value = EnvironmentVariableReference(name="ANOTHER_VAR", default="not_found")
""",
        },
    }

    # WHEN we call the stream route
    status_code, events = both_stream_types(request_body)

    # THEN we get a 200 response
    assert status_code == 200, events

    # THEN we get the expected events
    assert events[0]["name"] == "vembda.execution.initiated"
    assert events[1]["name"] == "workflow.execution.initiated"
    assert events[2]["name"] == "workflow.execution.fulfilled"

    # AND the environment variables are accessible in the workflow
    outputs = events[2]["body"]["outputs"]
    assert outputs["env_var_value"] == "test_value"
    assert outputs["another_var_value"] == "another_value"


@mock.patch("workflow_server.api.workflow_view.Queue")
def test_stream_workflow_route__queue_get_timeout(mock_queue_class):
    # GIVEN a valid request body
    span_id = uuid4()
    request_body = {
        "execution_id": str(span_id),
        "inputs": [],
        "environment_api_key": "test",
        "module": "workflow",
        "timeout": 360,
        "files": {
            "__init__.py": "",
            "workflow.py": """\
from vellum.workflows import BaseWorkflow

class Workflow(BaseWorkflow):
    class Outputs(BaseWorkflow.Outputs):
        foo = "hello"
""",
        },
    }

    # AND the queue.get method raises Empty exception
    mock_queue_instance = mock_queue_class.return_value
    mock_queue_instance.get.side_effect = Empty()

    # WHEN we call the stream route
    flask_app = create_app()
    with flask_app.test_client() as test_client:
        response = test_client.post("/workflow/stream", json=request_body)
        status_code = response.status_code
        response_data = response.get_json()

    # THEN we get a 408 response
    assert status_code == 408

    # AND we get the expected timeout error message
    assert response_data == {"detail": "Request timed out trying to initiate the Workflow"}


@pytest.mark.parametrize("non_process_stream_types", [code_exec_stream, flask_stream_disable_process_wrapper])
def test_stream_workflow_route__vembda_emitting_calls_monitoring_api(non_process_stream_types):
    """
    Tests that the monitoring API is called when vembda emitting is enabled.
    """

    # GIVEN a valid request body with vembda emitting enabled
    span_id = uuid4()
    request_body = {
        "execution_id": str(span_id),
        "inputs": [],
        "environment_api_key": "test",
        "module": "workflow",
        "timeout": 360,
        "feature_flags": {"vembda-event-emitting-enabled": True},
        "files": {
            "__init__.py": "",
            "workflow.py": """\
from vellum.workflows import BaseWorkflow

class Workflow(BaseWorkflow):
    class Outputs(BaseWorkflow.Outputs):
        foo = "hello"
""",
        },
    }
    emitted_events = []

    def send_events(self, events: list[WorkflowEvent]) -> None:
        for event in events:
            emitted_events.append(event)

    VellumEmitter._send_events = send_events

    # WHEN we call the stream route with mocked monitoring API
    status_code, events = non_process_stream_types(request_body)

    # THEN we get a 200 response
    assert status_code == 200, events

    # AND the expected workflow events were emitted
    event_names = [event.name for event in emitted_events]
    assert len(event_names) == 2, "Should include 2 events"
    assert "workflow.execution.initiated" in event_names, "Should include workflow.execution.initiated event"
    assert "workflow.execution.fulfilled" in event_names, "Should include workflow.execution.fulfilled event"


def test_stream_workflow_route__with_invalid_nested_set_graph(both_stream_types):
    """
    Tests that a workflow with an invalid nested set graph structure raises a clear error in the stream response.
    """
    # GIVEN a Flask application and invalid workflow content with nested set graph
    span_id = uuid4()

    invalid_workflow_content = """
from vellum.workflows import BaseWorkflow
from vellum.workflows.nodes import BaseNode

class TestNode(BaseNode):
    class Outputs(BaseNode.Outputs):
        value = "test"

class InvalidWorkflow(BaseWorkflow):
    graph = {TestNode, {TestNode}}

    class Outputs(BaseWorkflow.Outputs):
        result = TestNode.Outputs.value
"""

    request_body = {
        "timeout": 360,
        "execution_id": str(span_id),
        "inputs": [],
        "environment_api_key": "test",
        "module": "workflow",
        "files": {
            "__init__.py": "",
            "workflow.py": invalid_workflow_content,
        },
    }

    # WHEN we call the stream route
    status_code, events = both_stream_types(request_body)

    # THEN we get a 200 response
    assert status_code == 200, events

    # THEN we get the expected events: vembda initiated, workflow initiated, workflow rejected, vembda fulfilled
    assert len(events) == 4

    # AND the first event should be vembda execution initiated
    assert events[0]["name"] == "vembda.execution.initiated"
    assert events[0]["span_id"] == str(span_id)

    # AND the second event should be workflow execution initiated
    assert events[1]["name"] == "workflow.execution.initiated"

    # AND the third event should be workflow execution rejected
    assert events[2]["name"] == "workflow.execution.rejected"
    assert events[1]["span_id"] == events[2]["span_id"]

    # AND the error message should contain information about the invalid graph structure
    error_message = events[2]["body"]["error"]["message"]
    expected_message = (
        "Invalid graph structure detected. "
        "Nested sets or unsupported graph types are not allowed. "
        "Please contact Vellum support for assistance with Workflow configuration."
    )
    assert error_message == expected_message

    # AND the fourth event should be vembda execution fulfilled
    assert events[3]["name"] == "vembda.execution.fulfilled"
    assert events[3]["span_id"] == str(span_id)
    assert events[3]["body"]["exit_code"] == 0
