from enum import Enum

class Operations(str, Enum):
    OR  = 'or'
    AND = 'and'
    SUM = 'sum'
    AVG = 'avg'
    MAX = 'max'
    MIN = 'min'