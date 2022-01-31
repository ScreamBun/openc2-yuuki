from pydantic import BaseSettings


class OpenDxlConfig(BaseSettings):
    """OpenDXL Configuration to pass to OpenDXL Transport init."""
    event_request_topic: str = "oc2/cmd"
    event_response_topic: str = "oc2/rsp"
    service_topic: str = "oc2"
    config_file: str
