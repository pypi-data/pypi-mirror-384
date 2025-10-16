from enum import Enum

class ConfigPriority(Enum):
    RuntimeSpecificEnv = 1
    GlobalEnv = 2
    RuntimeSpecificFile = 3
    GlobalFile = 4
    User = 5
    DefaultLibrary = 6
