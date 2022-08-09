from pydantic import BaseSettings


class HttpConfig(BaseSettings):
    """
    Http Configuration to pass to Http Transport init
    """
    host: str = '127.0.0.1'
    port: int = 9001
