from abc import ABC, abstractmethod


class _Serializer(ABC):
    """All Serializer/Deserializers should follow this interface."""

    @staticmethod
    @abstractmethod
    def serialize(obj):
        pass

    @staticmethod
    @abstractmethod
    def deserialize(obj):
        pass
