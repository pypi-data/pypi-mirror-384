from prefect import task
import sys
from prefect.task_runners import ConcurrentTaskRunner, ThreadPoolTaskRunner
from prefect import runtime
# from prefect_dask.task_runners import DaskTaskRunner
from typing import Dict, List
import yaml
import importlib
import os
from kube_watch.models.workflow import WorkflowConfig, BatchFlowConfig, Task
from kube_watch.enums.workflow import ParameterType, TaskRunners, TaskInputsType
from kube_watch.modules.logic.merge import merge_logical_list

def load_workflow_config(yaml_file) -> WorkflowConfig:
    with open(yaml_file, 'r') as file:
        data = yaml.safe_load(file)
    return WorkflowConfig(**data['workflow'])


def load_batch_config(yaml_file) -> BatchFlowConfig:
    with open(yaml_file, 'r') as file:
        data = yaml.safe_load(file)
    return BatchFlowConfig(**data['batchFlows'])



# def execute_task(func, *args, name="default_task_name", **kwargs):
#     @task(name=name)
#     def func_task():
#         return func(*args, **kwargs)
#     return func_task


def func_task(name="default_task_name", task_input_type: TaskInputsType = TaskInputsType.ARG):
    if task_input_type == TaskInputsType.ARG:
        @task(name=name)
        def execute_task(func, *args, **kwargs):
            return func(*args, **kwargs)
        return execute_task
    if task_input_type == TaskInputsType.DICT:
        @task(name=name)
        def execute_task_dict(func, dict_inp):
            return func(dict_inp)
        return execute_task_dict
    raise ValueError(f'Unknow Task Input Type. It should either be {TaskInputsType.ARG} or {TaskInputsType.DICT} but {task_input_type} is provided.')


# @task
# def execute_task(func, *args, **kwargs):
#     return func(*args, **kwargs)



def get_task_function(module_name, task_name, plugin_path=None):
    """
    Fetch a function directly from a specified module.
    
    Args:
        module_name (str): The name of the module to import the function from. e.g. providers.aws
        task_name (str): The name of the function to fetch from the module.
        plugin_path (ster): define for external modules
        
    Returns:
        function: The function object fetched from the module.
    """
    try:
        if plugin_path:
            # Temporarily prepend the plugin path to sys.path to find the module
            module_path = os.path.join(plugin_path, *module_name.split('.')) + '.py'
            module_spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(module_spec)
            module_spec.loader.exec_module(module)
        else:
            # Standard import from the internal library path
            module = importlib.import_module(f"kube_watch.modules.{module_name}")
        
        return getattr(module, task_name)
    except ImportError as e:
        raise ImportError(f"Unable to import module '{module_name}': {e}")
    except AttributeError as e:
        raise AttributeError(f"The module '{module_name}' does not have a function named '{task_name}': {e}")
    # finally:
    #     if plugin_path:
    #         # Remove the plugin path from sys.path after importing
    #         sys.path.pop(0)  # Using pop(0) is safer in the context of insert(0, plugin_path)



def resolve_parameter_value(param):
    if param.type == ParameterType.FROM_ENV:
        return os.getenv(param.value, '')  # Default to empty string if env var is not set
    if param.type == ParameterType.FROM_FLOW:
        return runtime.flow_run.parameters.get(param.value, '')
    return param.value

def prepare_task_inputs(parameters):
    return {param.name: resolve_parameter_value(param) for param in parameters}


def prepare_task_inputs_from_dep(task_data: Task, task_inputs: Dict, tasks):
    for dep in task_data.dependency:
        par_task   = tasks[dep.taskName]
        par_res    = par_task.result()
        if dep.inputParamName != None:
            task_inputs.update({dep.inputParamName: par_res})

    return task_inputs


def resolve_conditional(task_data: Task, tasks):
    lst_bools = []
    for task_name in task_data.conditional.tasks:
        if task_name not in tasks:
            return False
        
        par_task   = tasks[task_name]
        lst_bools.append(par_task.result())
    return merge_logical_list(lst_bools, task_data.conditional.operation)
    



def submit_task(task_name, task_data, task_inputs, func):
    execute_task = func_task(name=task_name, task_input_type=task_data.inputsArgType)
    if task_data.inputsArgType == TaskInputsType.ARG:
        return execute_task.submit(func, **task_inputs)
    if task_data.inputsArgType == TaskInputsType.DICT:
        return execute_task.submit(func, dict_inp=task_inputs)
    raise ValueError("Unknown Input Arg Type.")



def resolve_runner(runner):
    if runner == TaskRunners.CONCURRENT:
        return ConcurrentTaskRunner
    if runner == TaskRunners.SEQUENTIAL:
        return ThreadPoolTaskRunner(max_workers=1)
    if runner == TaskRunners.DASK:
        raise ValueError("Dask Not Implemented")
        # return DaskTaskRunner
    if runner == TaskRunners.RAY:
        raise ValueError("Ray Not Implemented")
        # return RayTaskRunner
    raise ValueError("Invalid task runner type")


def filter_attributes(obj):
    import uuid
    from collections.abc import Iterable
    import inspect

    def is_simple(value):
        """ Check if the value is a simple data type or a collection of simple data types """
        if isinstance(value, (int, float, str, bool, type(None), uuid.UUID)):
            return True
        if isinstance(value, dict):
            return all(is_simple(k) and is_simple(v) for k, v in value.items())
        if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
            return all(is_simple(item) for item in value)
        return False

    result = {}
    for attr in dir(obj):
        # Avoid magic methods and attributes
        if attr.startswith("__") and attr.endswith("__"):
            continue
        value = getattr(obj, attr)
        # Filter out methods and check if the attribute value is simple
        if not callable(value) and not inspect.isclass(value) and is_simple(value):
            result[attr] = value
    return result