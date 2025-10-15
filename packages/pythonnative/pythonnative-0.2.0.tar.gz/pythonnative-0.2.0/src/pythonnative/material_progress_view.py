from abc import ABC, abstractmethod

from .utils import IS_ANDROID
from .view import ViewBase

# ========================================
# Base class
# ========================================


class MaterialProgressViewBase(ABC):
    @abstractmethod
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def set_progress(self, progress: float) -> None:
        pass

    @abstractmethod
    def get_progress(self) -> float:
        pass


if IS_ANDROID:
    # ========================================
    # Android class
    # https://developer.android.com/reference/com/google/android/material/progressindicator/LinearProgressIndicator
    # ========================================

    from java import jclass

    class MaterialProgressView(MaterialProgressViewBase, ViewBase):
        def __init__(self, context) -> None:
            super().__init__()
            self.native_class = jclass("com.google.android.material.progressindicator.LinearProgressIndicator")
            self.native_instance = self.native_class(context)
            self.native_instance.setIndeterminate(False)

        def set_progress(self, progress: float) -> None:
            self.native_instance.setProgress(int(progress * 100))

        def get_progress(self) -> float:
            return self.native_instance.getProgress() / 100.0

else:
    # ========================================
    # iOS class
    # https://developer.apple.com/documentation/uikit/uiprogressview
    # ========================================

    from rubicon.objc import ObjCClass

    class MaterialProgressView(MaterialProgressViewBase, ViewBase):
        def __init__(self) -> None:
            super().__init__()
            self.native_class = ObjCClass("UIProgressView")
            self.native_instance = self.native_class.alloc().initWithProgressViewStyle_(
                0
            )  # 0: UIProgressViewStyleDefault

        def set_progress(self, progress: float) -> None:
            self.native_instance.setProgress_animated_(progress, False)

        def get_progress(self) -> float:
            return self.native_instance.progress()
