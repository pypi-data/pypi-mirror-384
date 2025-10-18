import time
import random
from prefect import runtime
    
def generate_number():
    return 42


def mock_dict_data():
    return {
        "key1": "value1",
        "key2": "value2",
        "key3": {
            "k1": 1, "k2": 2, "k3": [1, 3, "ali"]
        }
    }

def print_input(params):
    print(params)

def print_number(number, dummy_param, env_var_name):
    print(f"The generated number is: {number} and the dummy_value is: {dummy_param}")
    return number, dummy_param, env_var_name


def print_flow_parameters():
    assert runtime.flow_run.parameters.get("WORK_DIR") is not None
    assert runtime.flow_run.parameters.get("MODULE_PATH") is not None
    print(runtime.flow_run.parameters.get("WORK_DIR"))
    print(runtime.flow_run.parameters.get("MODULE_PATH"))

def print_from_flow_parameters(work_dir):
    """
    work_dir is provided via flow parameters
    """
    assert work_dir != ''
    print(work_dir)


def delay(seconds):
    time.sleep(seconds)


def random_boolean():
    return random.choice([True, False])

def merge_bools(inp_dict):
    list_bools = [v for k,v in inp_dict.items()]
    return any(list_bools)

def print_result(task_name, result):
    print(f'=========== {task_name} RESULT =================')
    print(result)
