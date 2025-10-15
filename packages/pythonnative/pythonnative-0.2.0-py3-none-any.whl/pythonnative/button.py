from abc import ABC, abstractmethod
from typing import Callable, Optional

from .utils import IS_ANDROID, get_android_context
from .view import ViewBase

# ========================================
# Base class
# ========================================


class ButtonBase(ABC):
    @abstractmethod
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def set_title(self, title: str) -> None:
        pass

    @abstractmethod
    def get_title(self) -> str:
        pass

    @abstractmethod
    def set_on_click(self, callback: Callable[[], None]) -> None:
        pass


if IS_ANDROID:
    # ========================================
    # Android class
    # https://developer.android.com/reference/android/widget/Button
    # ========================================

    from java import dynamic_proxy, jclass

    class Button(ButtonBase, ViewBase):
        def __init__(self, title: str = "") -> None:
            super().__init__()
            self.native_class = jclass("android.widget.Button")
            context = get_android_context()
            self.native_instance = self.native_class(context)
            self.set_title(title)

        def set_title(self, title: str) -> None:
            self.native_instance.setText(title)

        def get_title(self) -> str:
            return self.native_instance.getText().toString()

        def set_on_click(self, callback: Callable[[], None]) -> None:
            class OnClickListener(dynamic_proxy(jclass("android.view.View").OnClickListener)):
                def __init__(self, callback):
                    super().__init__()
                    self.callback = callback

                def onClick(self, view):
                    self.callback()

            listener = OnClickListener(callback)
            self.native_instance.setOnClickListener(listener)

else:
    # ========================================
    # iOS class
    # https://developer.apple.com/documentation/uikit/uibutton
    # ========================================

    from rubicon.objc import SEL, ObjCClass, objc_method

    NSObject = ObjCClass("NSObject")

    # Mypy cannot understand Rubicon's dynamic subclassing; ignore the base type here.
    class _PNButtonHandler(NSObject):  # type: ignore[valid-type]
        # Set by the Button when wiring up the target/action callback.
        _callback: Optional[Callable[[], None]] = None

        @objc_method
        def onTap_(self, sender) -> None:
            try:
                callback = self._callback
                if callback is not None:
                    callback()
            except Exception:
                # Swallow exceptions to avoid crashing the app; logging is handled at higher levels
                pass

    class Button(ButtonBase, ViewBase):
        def __init__(self, title: str = "") -> None:
            super().__init__()
            self.native_class = ObjCClass("UIButton")
            self.native_instance = self.native_class.alloc().init()
            self.set_title(title)

        def set_title(self, title: str) -> None:
            self.native_instance.setTitle_forState_(title, 0)

        def get_title(self) -> str:
            return self.native_instance.titleForState_(0)

        def set_on_click(self, callback: Callable[[], None]) -> None:
            # Create a handler object with an Objective-C method `onTap:` and attach the Python callback
            handler = _PNButtonHandler.new()
            # Keep strong references to the handler and callback
            self._click_handler = handler
            handler._callback = callback
            # UIControlEventTouchUpInside = 1 << 6
            self.native_instance.addTarget_action_forControlEvents_(handler, SEL("onTap:"), 1 << 6)
