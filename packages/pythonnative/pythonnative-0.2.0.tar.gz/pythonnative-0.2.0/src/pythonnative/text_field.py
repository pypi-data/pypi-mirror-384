from abc import ABC, abstractmethod

from .utils import IS_ANDROID, get_android_context
from .view import ViewBase

# ========================================
# Base class
# ========================================


class TextFieldBase(ABC):
    @abstractmethod
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def set_text(self, text: str) -> None:
        pass

    @abstractmethod
    def get_text(self) -> str:
        pass


if IS_ANDROID:
    # ========================================
    # Android class
    # https://developer.android.com/reference/android/widget/EditText
    # ========================================

    from java import jclass

    class TextField(TextFieldBase, ViewBase):
        def __init__(self, text: str = "") -> None:
            super().__init__()
            self.native_class = jclass("android.widget.EditText")
            context = get_android_context()
            self.native_instance = self.native_class(context)
            self.native_instance.setSingleLine(True)
            self.set_text(text)

        def set_text(self, text: str) -> None:
            self.native_instance.setText(text)

        def get_text(self) -> str:
            return self.native_instance.getText().toString()

else:
    # ========================================
    # iOS class
    # https://developer.apple.com/documentation/uikit/uitextfield
    # ========================================

    from rubicon.objc import ObjCClass

    class TextField(TextFieldBase, ViewBase):
        def __init__(self, text: str = "") -> None:
            super().__init__()
            self.native_class = ObjCClass("UITextField")
            self.native_instance = self.native_class.alloc().init()
            self.set_text(text)

        def set_text(self, text: str) -> None:
            self.native_instance.setText_(text)

        def get_text(self) -> str:
            return self.native_instance.text()
