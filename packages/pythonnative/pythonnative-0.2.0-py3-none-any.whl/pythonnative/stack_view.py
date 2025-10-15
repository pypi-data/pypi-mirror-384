from abc import ABC, abstractmethod
from typing import Any, List

from .utils import IS_ANDROID, get_android_context
from .view import ViewBase

# ========================================
# Base class
# ========================================


class StackViewBase(ABC):
    @abstractmethod
    def __init__(self) -> None:
        super().__init__()
        self.views: List[Any] = []

    @abstractmethod
    def add_view(self, view) -> None:
        pass


if IS_ANDROID:
    # ========================================
    # Android class
    # https://developer.android.com/reference/android/widget/LinearLayout
    # ========================================

    from java import jclass

    class StackView(StackViewBase, ViewBase):
        def __init__(self) -> None:
            super().__init__()
            self.native_class = jclass("android.widget.LinearLayout")
            context = get_android_context()
            self.native_instance = self.native_class(context)
            self.native_instance.setOrientation(self.native_class.VERTICAL)

        def add_view(self, view):
            self.views.append(view)
            self.native_instance.addView(view.native_instance)

else:
    # ========================================
    # iOS class
    # https://developer.apple.com/documentation/uikit/uistackview
    # ========================================

    from rubicon.objc import ObjCClass

    class StackView(StackViewBase, ViewBase):
        def __init__(self) -> None:
            super().__init__()
            self.native_class = ObjCClass("UIStackView")
            self.native_instance = self.native_class.alloc().initWithFrame_(((0, 0), (0, 0)))
            self.native_instance.setAxis_(0)  # Set axis to vertical

        def add_view(self, view):
            self.views.append(view)
            self.native_instance.addArrangedSubview_(view.native_instance)
