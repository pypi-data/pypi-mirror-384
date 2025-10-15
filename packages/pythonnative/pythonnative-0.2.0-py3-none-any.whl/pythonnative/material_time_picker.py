from abc import ABC, abstractmethod

from .utils import IS_ANDROID
from .view import ViewBase

# ========================================
# Base class
# ========================================


class MaterialTimePickerBase(ABC):
    @abstractmethod
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def set_time(self, hour: int, minute: int) -> None:
        pass

    @abstractmethod
    def get_time(self) -> tuple:
        pass


if IS_ANDROID:
    # ========================================
    # Android class
    # https://developer.android.com/reference/com/google/android/material/timepicker/MaterialTimePicker
    # ========================================

    from java import jclass

    class MaterialTimePicker(MaterialTimePickerBase, ViewBase):
        def __init__(self, context, hour: int = 0, minute: int = 0) -> None:
            super().__init__()
            self.native_class = jclass("com.google.android.material.timepicker.MaterialTimePicker")
            self.native_instance = self.native_class(context)
            self.set_time(hour, minute)

        def set_time(self, hour: int, minute: int) -> None:
            self.native_instance.setTime(hour, minute)

        def get_time(self) -> tuple:
            hour = self.native_instance.getHour()
            minute = self.native_instance.getMinute()
            return hour, minute

else:
    # ========================================
    # iOS class
    # https://developer.apple.com/documentation/uikit/uidatepicker
    # ========================================

    from datetime import time

    from rubicon.objc import ObjCClass

    class MaterialTimePicker(MaterialTimePickerBase, ViewBase):
        def __init__(self, hour: int = 0, minute: int = 0) -> None:
            super().__init__()
            self.native_class = ObjCClass("UIDatePicker")
            self.native_instance = self.native_class.alloc().init()
            self.native_instance.setDatePickerMode_(1)  # Setting mode to Time
            self.set_time(hour, minute)

        def set_time(self, hour: int, minute: int) -> None:
            t = time(hour, minute)
            self.native_instance.setTime_(t)

        def get_time(self) -> tuple:
            t = self.native_instance.time()
            return t.hour, t.minute
