from abc import ABC, abstractmethod

from .utils import IS_ANDROID
from .view import ViewBase

# ========================================
# Base class
# ========================================


class MaterialDatePickerBase(ABC):
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
    # https://developer.android.com/reference/com/google/android/material/datepicker/MaterialDatePicker
    # ========================================

    from java import jclass

    class MaterialDatePicker(MaterialDatePickerBase, ViewBase):
        def __init__(self, year: int = 0, month: int = 0, day: int = 0) -> None:
            super().__init__()
            self.native_class = jclass("com.google.android.material.datepicker.MaterialDatePicker")
            self.builder = self.native_class.Builder.datePicker()
            self.set_date(year, month, day)
            self.native_instance = self.builder.build()

        def set_date(self, year: int, month: int, day: int) -> None:
            # MaterialDatePicker uses milliseconds since epoch to set date
            from java.util import Calendar

            cal = Calendar.getInstance()
            cal.set(year, month, day)
            milliseconds = cal.getTimeInMillis()
            self.builder.setSelection(milliseconds)

        def get_date(self) -> tuple:
            # Convert selection (milliseconds since epoch) back to a date
            from java.util import Calendar

            cal = Calendar.getInstance()
            cal.setTimeInMillis(self.native_instance.getSelection())
            return (
                cal.get(Calendar.YEAR),
                cal.get(Calendar.MONTH),
                cal.get(Calendar.DAY_OF_MONTH),
            )

else:
    # ========================================
    # iOS class
    # https://developer.apple.com/documentation/uikit/uidatepicker
    # ========================================

    from datetime import datetime

    from rubicon.objc import ObjCClass

    class MaterialDatePicker(MaterialDatePickerBase, ViewBase):
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
