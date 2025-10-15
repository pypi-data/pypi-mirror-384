from abc import ABC, abstractmethod

from .utils import IS_ANDROID, get_android_context
from .view import ViewBase

# ========================================
# Base class
# ========================================


class ProgressViewBase(ABC):
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
    # https://developer.android.com/reference/android/widget/ProgressBar
    # ========================================

    from java import jclass

    class ProgressView(ProgressViewBase, ViewBase):
        def __init__(self) -> None:
            super().__init__()
            self.native_class = jclass("android.widget.ProgressBar")
            # self.native_instance = self.native_class(context, None, android.R.attr.progressBarStyleHorizontal)
            context = get_android_context()
            self.native_instance = self.native_class(context, None, jclass("android.R$attr").progressBarStyleHorizontal)
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

    class ProgressView(ProgressViewBase, ViewBase):
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
