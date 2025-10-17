from .logapi import (
    LogEntryHeader,
    RunStartLog,
    RunEndLog,
    LlmCallLog,
    TestResultLog,
    OtherLog,
    LogResponse
)
from .client import CoagentClient, CoagentClientError

__all__ = [
    "LogEntryHeader",
    "RunStartLog",
    "RunEndLog",
    "LlmCallLog",
    "TestResultLog",
    "OtherLog",
    "LogResponse",
    "CoagentClient",
    "CoagentClientError"
]

def hello() -> str:
    return "Hello from coagent-client!"
