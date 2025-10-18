from enum import Enum

class ParameterType(str, Enum):
    STATIC = 'static'
    FROM_ENV = 'env'
    FROM_FLOW = 'flow'


class TaskRunners(str, Enum):
    SEQUENTIAL = 'sequential'
    CONCURRENT = 'concurrent'
    DASK       = 'dask'
    RAY        = 'ray'


class TaskInputsType(str, Enum):
    ARG = 'arg'
    DICT = 'dict'