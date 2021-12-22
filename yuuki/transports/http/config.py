from typing import Optional

from pydantic import BaseSettings, root_validator


class HTTPAuthentication(BaseSettings):
    enable: bool = False
    certfile: Optional[str] = None
    keyfile: Optional[str] = None
    ca_certs: Optional[str] = None

    @root_validator
    def check_certfile_and_keyfile(cls, args):
        if args.get('enable') is True and (args.get('certfile') is None and args.get('keyfile') is None):
            raise ValueError('TLS requires both a certfile and a keyfile')
        return args


class HttpConfig(BaseSettings):
    """Http Configuration to pass to Http Transport init."""
    host: str = '127.0.0.1'
    port: int = 9001
    authentication: HTTPAuthentication = HTTPAuthentication()
