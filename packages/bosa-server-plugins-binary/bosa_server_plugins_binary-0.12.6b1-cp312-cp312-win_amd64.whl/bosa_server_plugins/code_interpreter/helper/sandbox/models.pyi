from enum import Enum
from pydantic import BaseModel

class ExecutionStatus(Enum):
    """Status of code execution."""
    SUCCESS = 'success'
    ERROR = 'error'
    TIMEOUT = 'timeout'

class ExecutionResult(BaseModel):
    """Structured result of code execution."""
    status: ExecutionStatus
    code: str
    stdout: str
    stderr: str
    text: str
    error: str
    exit_code: int
    duration_ms: int | None
    @classmethod
    def create(cls, status: ExecutionStatus, code: str, stdout: str = '', stderr: str = '', error: str = '', duration_ms: int | None = None) -> ExecutionResult:
        '''Create ExecutionResult with common parameters.

        Args:
            status (ExecutionStatus): Execution status.
            code (str): Original code that was executed.
            stdout (str): Standard output from execution. Defaults to "".
            stderr (str): Standard error from execution. Defaults to "".
            error (str): Error message if execution failed. Defaults to "".
            duration_ms (int | None): Execution duration in milliseconds. Defaults to None.

        Returns:
            ExecutionResult: Configured execution result.
        '''
