from prefect import flow,  get_run_logger, runtime
import asyncio
from typing import List
import secrets
import os
import kube_watch.watch.helpers as helpers
from kube_watch.models.workflow import WorkflowOutput
from kube_watch.enums.workflow import TaskRunners, TaskInputsType


# @TODO: CONCURRENCY DOES NOT WORK PROPERLY AT FLOW LEVEL
def create_flow_based_on_config(yaml_file, run_async=True):
    workflow_config = helpers.load_workflow_config(yaml_file)
    flow_name       = workflow_config.name
    runner          = helpers.resolve_runner(workflow_config.runner)
    random_suffix   = secrets.token_hex(6)
    flow_run_name   = f"{flow_name} - {random_suffix}"

    @flow(name=flow_name, flow_run_name=flow_run_name, task_runner=runner)
    async def dynamic_workflow():
        logger = get_run_logger()
        tasks = {}

        for param in workflow_config.parameters:      
            runtime.flow_run.parameters[param.name] = param.value

        logger.info(f"Starting flow: {flow_name}")
        for task_data in workflow_config.tasks:
            task_name   = task_data.name
            func        = helpers.get_task_function(task_data.module, task_data.task, task_data.plugin_path)
            task_inputs = helpers.prepare_task_inputs(task_data.inputs.parameters) if task_data.inputs else {}

            condition_result = True
            if task_data.conditional:
                condition_result = helpers.resolve_conditional(task_data, tasks)

            if condition_result:
                # Resolve dependencies only if the task is going to be executed
                if task_data.dependency:
                    task_inputs = helpers.prepare_task_inputs_from_dep(task_data, task_inputs, tasks)
                
                task_future = helpers.submit_task(task_name, task_data, task_inputs, func)
                tasks[task_data.name] = task_future
            

        return tasks
    return dynamic_workflow


# SINGLE
def single_run_workflow(yaml_file, return_state=True) -> WorkflowOutput:
    dynamic_flow  = create_flow_based_on_config(yaml_file, run_async=False)
    flow_run = dynamic_flow(return_state=return_state)
    return WorkflowOutput(**{'flow_run': flow_run, 'config': dynamic_flow})


async def single_run_workflow_async(yaml_file, return_state=True) -> WorkflowOutput:
    dynamic_flow  = create_flow_based_on_config(yaml_file, run_async=True)
    flow_run = await dynamic_flow(return_state=return_state)
    return WorkflowOutput(**{'flow_run': flow_run, 'config': dynamic_flow}) 


# BATCH

@flow(name="Batch Workflow Runner - Sequential")
async def batch_run_sequential(batch_config, batch_dir) -> List[WorkflowOutput]:
    # batch_config = helpers.load_batch_config(batch_yaml_file)
    # batch_dir = os.path.dirname(batch_yaml_file)
    flows = []
    for item in batch_config.items:
        yaml_file_path = os.path.join(batch_dir, item.path)
        output = await single_run_workflow_async(yaml_file_path, return_state = True)
        flows.append(output)

    return flows

@flow(name="Batch Workflow Runner - Concurrent")
async def batch_run_concurrent(batch_config, batch_dir) -> List[WorkflowOutput]:
    """
    Run multiple workflows concurrently within a single flow to avoid database conflicts.
    Instead of creating separate flows, we'll execute the workflow logic directly as tasks.
    """
    from prefect import task
    
    @task
    async def execute_workflow_tasks(yaml_file_path):
        """Execute all tasks from a workflow config as a single unit"""
        workflow_config = helpers.load_workflow_config(yaml_file_path)
        logger = get_run_logger()
        tasks = {}
        
        # Set flow parameters
        for param in workflow_config.parameters:
            runtime.flow_run.parameters[param.name] = param.value
        
        logger.info(f"Processing workflow: {workflow_config.name} from {yaml_file_path}")
        
        # Execute tasks sequentially within this task to avoid conflicts
        for task_data in workflow_config.tasks:
            task_name = task_data.name
            func = helpers.get_task_function(task_data.module, task_data.task, task_data.plugin_path)
            task_inputs = helpers.prepare_task_inputs(task_data.inputs.parameters) if task_data.inputs else {}
            
            condition_result = True
            if task_data.conditional:
                condition_result = helpers.resolve_conditional(task_data, tasks)
            
            if condition_result:
                # Resolve dependencies
                if task_data.dependency:
                    task_inputs = helpers.prepare_task_inputs_from_dep(task_data, task_inputs, tasks)
                
                # Execute the function directly instead of submitting as a separate task
                try:
                    # Handle default inputsArgType if not specified
                    inputs_arg_type = getattr(task_data, 'inputsArgType', TaskInputsType.ARG)
                    if inputs_arg_type == TaskInputsType.ARG:
                        result = func(**task_inputs)
                    else:  # TaskInputsType.DICT
                        result = func(task_inputs)
                    
                    # Store result for dependencies
                    class MockTaskResult:
                        def __init__(self, value):
                            self._value = value
                        def result(self):
                            return self._value
                    
                    tasks[task_data.name] = MockTaskResult(result)
                    logger.info(f"Completed task: {task_name}")
                
                except Exception as e:
                    logger.error(f"Task {task_name} failed: {str(e)}")
                    raise
        
        return {"workflow_name": workflow_config.name, "tasks_completed": len(tasks)}
    
    # Submit all workflow executions as concurrent tasks
    workflow_tasks = []
    for item in batch_config.items:
        yaml_file_path = os.path.join(batch_dir, item.path)
        task_future = execute_workflow_tasks.submit(yaml_file_path)
        workflow_tasks.append((task_future, yaml_file_path))
    
    # Wait for all tasks to complete
    results = []
    for task_future, yaml_path in workflow_tasks:
        try:
            result = task_future.result()  # .result() is synchronous, don't await it
            # Create a mock WorkflowOutput for compatibility
            workflow_output = WorkflowOutput(**{
                'flow_run': result, 
                'config': {'name': result['workflow_name'], 'path': yaml_path}
            })
            results.append(workflow_output)
        except Exception as e:
            logger = get_run_logger()
            logger.error(f"Workflow {yaml_path} failed: {str(e)}")
            raise
    
    return results


@flow(name="Batch Workflow Runner - Concurrent (Original Flow Approach)")
async def batch_run_concurrent_flows(batch_config, batch_dir) -> List[WorkflowOutput]:
    """
    Original approach: Run separate flows with staggered execution to reduce database contention.
    This preserves the full Prefect flow semantics and task tracking.
    Use this with PostgreSQL backend for better concurrent performance.
    
    Advantages:
    - Full Prefect flow semantics and UI tracking
    - Each YAML gets its own flow run with proper task hierarchy
    - Task names can be the same across YAML files without conflicts
    
    Disadvantages:
    - May cause database locking with SQLite
    - More database writes due to separate flow runs
    """
    from prefect import task
    
    @task
    async def run_flow_with_delay(yaml_file_path, delay_seconds=0):
        if delay_seconds > 0:
            await asyncio.sleep(delay_seconds)
        
        flow_function = create_flow_based_on_config(yaml_file_path, run_async=True)
        result = await flow_function(return_state=True)
        return WorkflowOutput(**{'flow_run': result, 'config': flow_function})
    
    # Submit flows with staggered delays to reduce database contention
    workflow_tasks = []
    for i, item in enumerate(batch_config.items):
        yaml_file_path = os.path.join(batch_dir, item.path)
        # Add small delay between flow starts (0, 2, 4, 6 seconds...)
        delay = i * 2  
        task_future = run_flow_with_delay.submit(yaml_file_path, delay)
        workflow_tasks.append(task_future)
    
    # Wait for all flows to complete
    results = []
    for task_future in workflow_tasks:
        result = task_future.result()
        results.append(result)
    
    return results


def batch_run_workflow(batch_yaml_file, use_single_flow=True):
    """
    Run batch workflows with two different approaches:
    
    Args:
        batch_yaml_file: Path to the batch configuration YAML
        use_single_flow: If True (default), uses single flow approach (better for SQLite)
                        If False, uses separate flows with delays (better for PostgreSQL)
    """
    batch_config = helpers.load_batch_config(batch_yaml_file)
    batch_dir = os.path.dirname(batch_yaml_file)

    if batch_config.runner == TaskRunners.SEQUENTIAL:
        return asyncio.run(batch_run_sequential(batch_config, batch_dir))
    
    if batch_config.runner == TaskRunners.CONCURRENT:
        if use_single_flow:
            # Single flow approach - better for SQLite, tasks scoped per YAML
            return asyncio.run(batch_run_concurrent(batch_config, batch_dir))
        else:
            # Separate flows approach - better for PostgreSQL, full Prefect semantics
            return asyncio.run(batch_run_concurrent_flows(batch_config, batch_dir))

    raise ValueError('Invalid flow runner type')
