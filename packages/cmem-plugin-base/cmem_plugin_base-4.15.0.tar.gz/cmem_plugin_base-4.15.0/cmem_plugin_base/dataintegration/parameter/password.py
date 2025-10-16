"""DI Password String Parameter Type."""

from cmem_plugin_base.dataintegration.context import PluginContext, SystemContext
from cmem_plugin_base.dataintegration.types import ParameterType, ParameterTypes


class Password:
    """A password string that will be encrypted and not shown to the user."""

    def __init__(self, encrypted_value: str, system: SystemContext):
        self.encrypted_value = encrypted_value
        self.system = system
        self.decrypt()  # Decrypt the password to check if the key is valid

    def decrypt(self) -> str:
        """Return the decrypted value"""
        return self.system.decrypt(self.encrypted_value)


class PasswordParameterType(ParameterType[Password]):
    """Password parameter type."""

    name = "password"
    """Same type name as 'PasswordParameterType' in DataIntegration code base."""

    preamble = "PASSWORD_PARAMETER:"
    """Prefix to identify already encrypted values."""

    def from_string(self, value: str, context: PluginContext) -> Password:
        """Parse strings into parameter values.

        Decrypts the password if the encryption preamble is present
        """
        if value is None or value == "":
            encrypted_value = ""
        elif value.startswith(self.preamble):
            encrypted_value = value.removeprefix(self.preamble)
        else:
            encrypted_value = context.system.encrypt(value)
        return Password(encrypted_value, context.system)

    def to_string(self, value: Password) -> str:
        """Convert parameter values into their string representation.

        Encrypts the password so that it won't be stored verbatim.
        """
        if value.encrypted_value == "":
            return ""
        return self.preamble + value.encrypted_value


ParameterTypes.register_type(PasswordParameterType())
