from abc import ABC
from typing import Any

# ========================================
# Base class
# ========================================


class ViewBase(ABC):
    def __init__(self) -> None:
        # Native bridge handles return types dynamically; these attributes are set at runtime.
        self.native_instance: Any = None
        self.native_class: Any = None

    # @abstractmethod
    # def add_view(self, view):
    #     pass
    #
    # @abstractmethod
    # def set_layout(self, layout):
    #     pass
    #
    # @abstractmethod
    # def show(self):
    #     pass
