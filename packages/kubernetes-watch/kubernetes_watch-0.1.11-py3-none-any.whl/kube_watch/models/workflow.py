from typing import List, Optional, Dict, Any
from kube_watch.enums.workflow import ParameterType, TaskRunners, TaskInputsType
from kube_watch.enums.logic import Operations

from .common import CamelModel

class Parameter(CamelModel):
    name: str
    value: Any
    type: Optional[ParameterType] = ParameterType.STATIC

class Artifact(CamelModel):
    path: str

class Inputs(CamelModel):
    parameters: Optional[List[Parameter]] = []
    artifacts: Optional[List[Artifact]] = []

class Dependency(CamelModel):
    taskName: str
    inputParamName: Optional[str] = None

class Condition(CamelModel):
    tasks: List[str]
    operation: Optional[Operations] = Operations.AND

class Task(CamelModel):
    """
    :param plugin_path: define if referring to an external module outside the library.
    """
    module: str
    task: str
    name: str
    plugin_path: Optional[str] = ""
    inputsArgType: Optional[TaskInputsType] = TaskInputsType.ARG  # @TODO refactor inputsArgType to inputs_arg_type
    inputs: Optional[Inputs] = None
    dependency: Optional[List[Dependency]]  = None
    conditional: Optional[Condition]  = None
    outputs: Optional[List[str]]  = None

class WorkflowConfig(CamelModel):
    name: str
    runner: TaskRunners = TaskRunners.CONCURRENT
    parameters: Optional[List[Parameter]] = []
    tasks: List[Task]

class WorkflowOutput(CamelModel):
    flow_run: Any
    config: Any

class BatchFlowItem(CamelModel):
    path: str

class BatchFlowConfig(CamelModel):
    # Only possible runners are concurrent and sequential
    runner: TaskRunners = TaskRunners.CONCURRENT
    items: List[BatchFlowItem]



