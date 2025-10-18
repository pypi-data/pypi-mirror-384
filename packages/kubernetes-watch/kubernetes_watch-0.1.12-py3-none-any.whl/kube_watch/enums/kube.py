from enum import Enum


class Hosts(str, Enum):
    LOCAL = 'local'
    REMOTE = 'remote'