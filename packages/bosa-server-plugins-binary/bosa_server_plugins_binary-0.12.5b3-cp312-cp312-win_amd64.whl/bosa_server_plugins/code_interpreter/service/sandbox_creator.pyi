from _typeshed import Incomplete
from bosa_core import ConfigService as ConfigService
from bosa_server_plugins.auth.scheme import AuthenticationScheme as AuthenticationScheme
from bosa_server_plugins.code_interpreter.constant import DEFAULT_LANGUAGE as DEFAULT_LANGUAGE
from bosa_server_plugins.code_interpreter.helper.sandbox.sandbox import E2BRemoteSandbox as E2BRemoteSandbox

class SandboxCreatorService:
    """Sandbox creator for Code Interpreter Plugin.

    Attributes:
        auth_scheme (AuthenticationScheme): The authentication scheme to use.
        config_service (ConfigService): The config service to use.
        e2b_domain (str | None): The E2B domain to use.
        DEFAULT_ADDITIONAL_PACKAGES (list[str]): Default additional packages to install.
    """
    DEFAULT_ADDITIONAL_PACKAGES: Incomplete
    auth_scheme: AuthenticationScheme
    config_service: ConfigService
    e2b_domain: str | None
    def __init__(self, auth_scheme: AuthenticationScheme, config_service: ConfigService) -> None:
        """Initialize the sandbox creator service.

        Args:
            auth_scheme (AuthenticationScheme): The authentication scheme to use.
            config_service (ConfigService): The config service to use.
        """
    def create_sandbox(self, language: str = ..., additional_packages: list[str] | None = None) -> E2BRemoteSandbox:
        '''Create and initialize the E2B Remote Sandbox.

        Args:
            language (str, optional): Programming language for the sandbox. Defaults to "python".
            additional_packages (list[str] | None, optional): Additional packages to install. Defaults to None.

        Returns:
            E2BRemoteSandbox: Initialized sandbox instance.
        '''
