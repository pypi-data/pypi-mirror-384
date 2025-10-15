from bosa_server_plugins.code_interpreter.constant import DATA_FILE_PATH as DATA_FILE_PATH, DEFAULT_LANGUAGE as DEFAULT_LANGUAGE
from bosa_server_plugins.code_interpreter.helper.sandbox.file_watcher import E2BFileWatcher as E2BFileWatcher
from bosa_server_plugins.code_interpreter.helper.sandbox.models import ExecutionResult as ExecutionResult, ExecutionStatus as ExecutionStatus
from bosa_server_plugins.code_interpreter.helper.sandbox.utils import calculate_duration_ms as calculate_duration_ms
from e2b.sandbox_sync.commands.command import Commands as Commands
from e2b_code_interpreter import Sandbox as E2BSandbox
from gllm_inference.schema import Attachment as Attachment

class E2BRemoteSandbox:
    """E2B Remote Sandbox wrapper.

    Attributes:
        language (str): Programming language for dependency installation.
        additional_packages (list[str]): Additional packages to install during initialization.
        sandbox (E2BSandbox): E2B sandbox instance.
        file_watcher (E2BFileWatcher): File watcher for monitoring file creation.
        commands (Any): Command interface for the sandbox.
    """
    language: str
    additional_packages: list[str]
    sandbox: E2BSandbox
    file_watcher: E2BFileWatcher
    commands: Commands
    def __init__(self, *, api_key: str, domain: str | None = None, language: str = ..., additional_packages: list[str] | None = None) -> None:
        '''Initialize E2B Remote Sandbox instance.

        Args:
            api_key (str): E2B API key.
            domain (str, optional): E2B domain . Defaults to None.
            language (str, optional): Programming language for dependency installation. Defaults to "python".
            additional_packages (list[str], optional): Additional packages to install during initialization.
                Defaults to None.

        Raises:
            RuntimeError: If E2B Cloud sandbox initialization fails.
        '''
    async def execute_code(self, code: str, timeout: int = 30, files: list[Attachment] | None = None, output_dirs: list[str] | None = None) -> ExecutionResult:
        """Execute code in the E2B Cloud sandbox.

        Args:
            code (str): The code to execute.
            timeout (int, optional): Maximum execution time in seconds. Defaults to 30.
            files (list[Attachment] | None, optional): List of Attachment objects with file details. Defaults to None.
            output_dirs (list[str] | None, optional): List of output directories to monitor for file creation.
                Defaults to None.

        Returns:
            ExecutionResult: Structured result of the execution.

        Raises:
            RuntimeError: If sandbox is not initialized.
        """
    def terminate(self) -> None:
        """Terminate the sandbox environment and clean up resources."""
    def get_created_files(self) -> list[str]:
        """Get the list of files created during the last monitored execution.

        Returns:
            list[str]: List of file paths that were created.
        """
    def download_file(self, file_path: str) -> bytes | None:
        """Download file content from the sandbox.

        Uses download_url method to get a direct URL and downloads via HTTP,
        which avoids the binary corruption issue with files.read().

        Args:
            file_path (str): Path to the file in the sandbox.

        Returns:
            bytes | None: File content as bytes, or None if download fails.

        Raises:
            RuntimeError: If sandbox is not initialized.
        """
