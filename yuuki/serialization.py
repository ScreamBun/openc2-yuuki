from typing import Callable

from pydantic import BaseModel


class Serialization(BaseModel):
    name: str
    deserialize: Callable
    serialize: Callable
