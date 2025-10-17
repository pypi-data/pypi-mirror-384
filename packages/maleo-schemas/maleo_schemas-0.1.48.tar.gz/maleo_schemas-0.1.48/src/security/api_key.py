import re
from enum import StrEnum
from maleo.enums.environment import Environment
from maleo.types.string import ListOfStrs


class APIKeyType(StrEnum):
    SYSTEM = "sak"
    TENANT = "tak"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


KEY_BODY_PATTERN = re.compile(r"^[A-Za-z0-9_-]{32,256}$")


def validate(api_key: str, environment: Environment):
    components = api_key.split("-", maxsplit=3)

    # Validate components count
    if len(components) != 4:
        raise ValueError("API Key must have excatly four components")

    # Ensure 'maleo' exist
    if components[0] != "maleo":
        raise ValueError("API Key must start with 'maleo' as the first component")

    # Ensure valid environment
    api_key_environment = components[1]
    if api_key_environment not in [e.value for e in Environment]:
        raise ValueError(
            f"Unknown enviromnent in API Key second component: {api_key_environment}"
        )

    api_key_environment = Environment(api_key_environment)

    if environment is Environment.LOCAL:
        if api_key_environment not in (Environment.LOCAL, Environment.STAGING):
            raise ValueError(
                "Only local and staging API Key can be used in local environment"
            )
    elif environment is Environment.STAGING:
        if api_key_environment is not Environment.STAGING:
            raise ValueError("Only staging API Key can be used in staging environment")
    elif environment is Environment.PRODUCTION:
        if api_key_environment is not Environment.PRODUCTION:
            raise ValueError(
                "Only production API Key can be used in production environment"
            )

    # Ensure valid type
    api_key_type = components[2]
    if api_key_type not in [t.value for t in APIKeyType]:
        raise ValueError(f"Unknown type in API Key third component: {api_key_type}")

    # Validate key body
    key_body = components[3]
    if not KEY_BODY_PATTERN.match(key_body):
        raise ValueError(f"Invalid API Key body format: {key_body!r}")
