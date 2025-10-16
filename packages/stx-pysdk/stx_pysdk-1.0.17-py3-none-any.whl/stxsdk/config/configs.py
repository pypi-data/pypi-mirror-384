
"""
`Configs` is a class that contains the global configuration variables/parameters
to be used in the services
"""


class Configs:
    BASE_URL:str = "https://{host}"
    GRAPHQL_URL: str = "https://{host}/api/graphql"
    WS_URL: str = "wss://{host}/socket/websocket"
    API_ENV = "staging"
    LOGIN_API: str = "login"
    CONFIRM_2FA: str = "confirm2Fa"
    REFRESH_TOKEN_API: str = "newToken"
    REGISTER_API:str = "register"
    CHANNEL_CONNECTION_URL: str = "{url}?token={token}&vsn=2.0.0"
    GRAPHQL_VERSION:str = "v3.0.52-3"
    SCHEMA_PATH:str= "https://schema.stxapp.io"
    ENV_HOSTS = {
        "production": "api.on.stxapp.ca",
        "staging": "api-staging.on.sportsxapp.com",
        "dev": "api-dev.on.sportsxapp.com",
        "qa": "api-qa.on.sportsxapp.com",
        "demo": "demo.xvexchange.com"
   }

