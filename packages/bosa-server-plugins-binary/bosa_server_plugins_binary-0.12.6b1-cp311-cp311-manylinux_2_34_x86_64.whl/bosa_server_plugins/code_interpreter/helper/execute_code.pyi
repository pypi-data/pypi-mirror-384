from bosa_server_plugins.code_interpreter.constant import DATA_FILE_NAME as DATA_FILE_NAME, DEFAULT_LANGUAGE as DEFAULT_LANGUAGE
from bosa_server_plugins.code_interpreter.helper.sandbox.models import ExecutionResult as ExecutionResult
from bosa_server_plugins.code_interpreter.helper.sandbox.sandbox import E2BRemoteSandbox as E2BRemoteSandbox
from bosa_server_plugins.code_interpreter.service.sandbox_creator import SandboxCreatorService as SandboxCreatorService
from typing import Any

async def execute_code(create_sandbox_service: SandboxCreatorService, *, code: str, data_source: str | list[dict[str, Any]] | None = None, timeout: int | None = None, language: str | None = None, additional_packages: list[str] | None = None, output_dirs: list[str] | None = None):
    '''Execute code in the Cloud sandbox.

    Args:
        create_sandbox_service (SandboxCreatorService): The sandbox creator service.
        code (str): The code to execute.
        data_source (str | list[dict[str, Any]] | None, optional): The data source used during code execution.
            Defaults to None.
        timeout (int, optional): The maximum execution time in seconds. Defaults to 30.
        language (str, optional): The programming language for the sandbox. Defaults to "python".
        additional_packages (list[str] | None, optional): Additional Python packages to install before execution.
            Defaults to None.
        output_dirs (list[str] | None, optional): List of output directories to monitor for file creation.
            Defaults to None.

    Returns:
        dict | str: The execution result as a dictionary or a string.
    '''
