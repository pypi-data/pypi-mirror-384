from abc import ABC, abstractmethod

from .utils import IS_ANDROID
from .view import ViewBase

# ========================================
# Base class
# ========================================


class DatePickerBase(ABC):
    @abstractmethod
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def set_date(self, year: int, month: int, day: int) -> None:
        pass

    @abstractmethod
    def get_date(self) -> tuple:
        pass


if IS_ANDROID:
    # ========================================
    # Android class
    # https://developer.android.com/reference/android/widget/DatePicker
    # ========================================

    from java import jclass

    class DatePicker(DatePickerBase, ViewBase):
        def __init__(self, context, year: int = 0, month: int = 0, day: int = 0) -> None:
            super().__init__()
            self.native_class = jclass("android.widget.DatePicker")
            self.native_instance = self.native_class(context)
            self.set_date(year, month, day)

        def set_date(self, year: int, month: int, day: int) -> None:
            self.native_instance.updateDate(year, month, day)

        def get_date(self) -> tuple:
            year = self.native_instance.getYear()
            month = self.native_instance.getMonth()
            day = self.native_instance.getDayOfMonth()
            return year, month, day

else:
    # ========================================
    # iOS class
    # https://developer.apple.com/documentation/uikit/uidatepicker
    # ========================================

    from datetime import datetime

    from rubicon.objc import ObjCClass

    class DatePicker(DatePickerBase, ViewBase):
        def __init__(self, year: int = 0, month: int = 0, day: int = 0) -> None:
            super().__init__()
            self.native_class = ObjCClass("UIDatePicker")
            self.native_instance = self.native_class.alloc().init()
            self.set_date(year, month, day)

        def set_date(self, year: int, month: int, day: int) -> None:
            date = datetime(year, month, day)
            self.native_instance.setDate_(date)

        def get_date(self) -> tuple:
            date = self.native_instance.date()
            return date.year, date.month, date.day
