from abc import ABC, abstractmethod

from .utils import IS_ANDROID, get_android_context
from .view import ViewBase

# ========================================
# Base class
# ========================================


class SwitchBase(ABC):
    @abstractmethod
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def set_on(self, value: bool) -> None:
        pass

    @abstractmethod
    def is_on(self) -> bool:
        pass


if IS_ANDROID:
    # ========================================
    # Android class
    # https://developer.android.com/reference/android/widget/Switch
    # ========================================

    from java import jclass

    class Switch(SwitchBase, ViewBase):
        def __init__(self, value: bool = False) -> None:
            super().__init__()
            self.native_class = jclass("android.widget.Switch")
            context = get_android_context()
            self.native_instance = self.native_class(context)
            self.set_on(value)

        def set_on(self, value: bool) -> None:
            self.native_instance.setChecked(value)

        def is_on(self) -> bool:
            return self.native_instance.isChecked()

else:
    # ========================================
    # iOS class
    # https://developer.apple.com/documentation/uikit/uiswitch
    # ========================================

    from rubicon.objc import ObjCClass

    class Switch(SwitchBase, ViewBase):
        def __init__(self, value: bool = False) -> None:
            super().__init__()
            self.native_class = ObjCClass("UISwitch")
            self.native_instance = self.native_class.alloc().init()
            self.set_on(value)

        def set_on(self, value: bool) -> None:
            self.native_instance.setOn_animated_(value, False)

        def is_on(self) -> bool:
            return self.native_instance.isOn()
