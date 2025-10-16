from enum import Enum


class EnvironmentVariable(Enum):
    ENVIRONMENT = "ENVIRONMENT"


class EnvironmentSecret(Enum):
    APPLICATION_NAME = "APPLICATION_NAME"
    DISCORD_BOT_TOKEN = "DISCORD_BOT_TOKEN"
    WISE_API_KEY = "WISE_API_KEY"
