from _typeshed import Incomplete
from bosa_core import ConfigService as ConfigService
from bosa_core.authentication.client.service import ClientAwareService as ClientAwareService
from bosa_core.authentication.plugin.service import ThirdPartyIntegrationService as ThirdPartyIntegrationService
from bosa_core.authentication.token.service import VerifyTokenService as VerifyTokenService
from bosa_core.cache import CacheService as CacheService
from bosa_server_plugins.auth.bearer import BearerTokenAuthentication as BearerTokenAuthentication
from bosa_server_plugins.code_interpreter.router import CodeInterpreterApiRoutes as CodeInterpreterApiRoutes
from bosa_server_plugins.common.exception import IntegrationDoesNotExistException as IntegrationDoesNotExistException
from bosa_server_plugins.common.helper.header import HeaderHelper as HeaderHelper
from bosa_server_plugins.common.helper.integration import IntegrationHelper as IntegrationHelper
from bosa_server_plugins.common.plugin import ThirdPartyIntegrationPlugin as ThirdPartyIntegrationPlugin
from bosa_server_plugins.handler import ExposedDefaultHeaders as ExposedDefaultHeaders, Router as Router
from typing import Any

class CodeInterpreterPlugin(ThirdPartyIntegrationPlugin):
    """Code Interpreter Plugin."""
    name: str
    version: str
    description: str
    config: ConfigService
    cache: CacheService
    router: Router
    client_aware_service: ClientAwareService
    third_party_integration_service: ThirdPartyIntegrationService
    token_service: VerifyTokenService
    header_helper: HeaderHelper
    integration_helper: IntegrationHelper
    CODE_INTERPRETER_MASTER_KEY_ENV: str
    api_key: Incomplete
    auth_scheme: Incomplete
    routes: Incomplete
    def __init__(self) -> None:
        """Initializes the plugin."""
    def initialize_authorization(self, callback_url: str, headers: ExposedDefaultHeaders):
        """Initializes the plugin authorization.

        This method is not supported by this plugin. Use initialize_custom_configuration instead.

        Args:
            callback_url (str): The callback URL.
            headers (ExposedDefaultHeaders): The headers.

        Raises:
            NotImplementedError: because this plugin does not support OAuth2 authorization.
        """
    def initialize_custom_configuration(self, configuration: dict[str, Any], headers: ExposedDefaultHeaders):
        """Initializes the plugin with custom configuration.

        Args:
            configuration (dict[str, Any]): The custom configuration dictionary containing the API key.
            headers (ExposedDefaultHeaders): The headers.

        Returns:
            dict: The configuration result URL or status.
        """
    def success_authorize_callback(self, **kwargs) -> None:
        """Success authorize callback.

        Args:
            **kwargs: The keyword arguments.
        """
    def remove_integration(self, user_identifier: str, headers: ExposedDefaultHeaders):
        """Removes the integration.

        Args:
            user_identifier (str): The user identifier to remove.
            headers (ExposedDefaultHeaders): The headers.

        Raises:
            IntegrationDoesNotExistException: If the integration does not exist.
        """
    def user_has_integration(self, headers: ExposedDefaultHeaders):
        """Checks if the user has an integration.

        Args:
            headers (ExposedDefaultHeaders): The headers.

        Returns:
            bool: True if the user has an integration, False otherwise.
        """
    def select_integration(self, user_identifier: str, headers: ExposedDefaultHeaders):
        """Selects the integration.

        Args:
            user_identifier (str): The user identifier to select.
            headers (ExposedDefaultHeaders): The headers.

        Raises:
            IntegrationDoesNotExistException: If the integration does not exist.
        """
    def get_integration(self, user_identifier: str, headers: ExposedDefaultHeaders):
        """Gets the integration.

        Args:
            user_identifier (str): The user identifier to get.
            headers (ExposedDefaultHeaders): The headers.

        Raises:
            IntegrationDoesNotExistException: If the integration does not exist.
        """
