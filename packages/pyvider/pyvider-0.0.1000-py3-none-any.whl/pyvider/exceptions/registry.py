# pyvider/exceptions/registry.py
from provide.foundation.errors import ConfigurationError as FoundationConfigurationError


class ComponentRegistryError(FoundationConfigurationError):
    """Raised for errors during component registration or retrieval."""

    def _default_code(self) -> str:
        return "COMPONENT_REGISTRY_ERROR"


class ValidatorRegistrationError(FoundationConfigurationError):
    """Raised when a non-callable is registered as a validator, or other validator issues."""

    def _default_code(self) -> str:
        return "VALIDATOR_REGISTRATION_ERROR"
