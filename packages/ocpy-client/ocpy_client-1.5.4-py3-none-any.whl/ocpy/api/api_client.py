from ocpy import get_connection_config


class OpenCastBaseApiClient:
    def __init__(self, user: str = None, password: str = None, server_url: str = None):
        if user is None or password is None or server_url is None:
            connection_config = get_connection_config()
            if connection_config is None:
                raise ValueError(
                    "user, password and server_url must be specified; directly or by calling "
                    "ocpy.api.setup_connection_config(user, password,server_url)!"
                )
            user = connection_config.get("user", user) if user is None else user
            password = connection_config.get("password", password) if password is None else password
            server_url = connection_config.get("server_url", server_url) if server_url is None else server_url
            if user is None or password is None or server_url is None:
                raise ValueError(
                    "invalid values in connection_config, please call "
                    "ocpy.api.setup_connection_config(user, password,server_url) again"
                )
        self.user = user
        self.password = password
        self.server_url = server_url


class OpenCastDigestBaseApiClient:
    def __init__(
            self,
            digest_user: str = None,
            digest_password: str = None,
            server_url: str = None,
            optional: bool = False
    ):
        if digest_user is None or digest_password is None or server_url is None:
            connection_config = get_connection_config()
            if connection_config is None and not optional:
                raise ValueError(
                    "digest_user, digest_password and server_url must be specified; directly or by calling "
                    "ocpy.api.setup_connection_config(digest_user, digest_password, server_url)!"
                )
            digest_user = connection_config.get("digest_user", digest_user) if digest_user is None else digest_user
            digest_password = connection_config.get("digest_password", digest_password) if digest_password is None else digest_password
            server_url = connection_config.get("server_url", server_url) if server_url is None else server_url
            if (digest_user is None or digest_password is None or server_url is None) and not optional:
                raise ValueError(
                    "invalid values in connection_config, please call "
                    "ocpy.api.setup_connection_config(digest_user, digest_password, server_url, etc.) again"
                )
        self.server_url = server_url
        self.digest_user = digest_user
        self.digest_password = digest_password


class OpenCastApiService:
    def __init__(self, service_url):
        from ocpy.api.service import Service
        if isinstance(service_url, Service):
            service_url = service_url.get_url()
        self.base_url = service_url
        self.server_url = service_url

    def __str__(self):
        return self.base_url

    def __repr__(self):
        return self.__str__()
