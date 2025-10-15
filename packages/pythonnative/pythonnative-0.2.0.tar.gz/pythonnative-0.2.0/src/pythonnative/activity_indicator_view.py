from abc import ABC, abstractmethod

from .utils import IS_ANDROID, get_android_context
from .view import ViewBase

# ========================================
# Base class
# ========================================


class ActivityIndicatorViewBase(ABC):
    @abstractmethod
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def start_animating(self) -> None:
        pass

    @abstractmethod
    def stop_animating(self) -> None:
        pass


if IS_ANDROID:
    # ========================================
    # Android class
    # https://developer.android.com/reference/android/widget/ProgressBar
    # ========================================

    from java import jclass

    class ActivityIndicatorView(ActivityIndicatorViewBase, ViewBase):
        def __init__(self) -> None:
            super().__init__()
            self.native_class = jclass("android.widget.ProgressBar")
            # self.native_instance = self.native_class(context, None, android.R.attr.progressBarStyleLarge)
            context = get_android_context()
            self.native_instance = self.native_class(context)
            self.native_instance.setIndeterminate(True)

        def start_animating(self) -> None:
            # self.native_instance.setVisibility(android.view.View.VISIBLE)
            return

        def stop_animating(self) -> None:
            # self.native_instance.setVisibility(android.view.View.GONE)
            return

else:
    # ========================================
    # iOS class
    # https://developer.apple.com/documentation/uikit/uiactivityindicatorview
    # ========================================

    from rubicon.objc import ObjCClass

    class ActivityIndicatorView(ActivityIndicatorViewBase, ViewBase):
        def __init__(self) -> None:
            super().__init__()
            self.native_class = ObjCClass("UIActivityIndicatorView")
            self.native_instance = self.native_class.alloc().initWithActivityIndicatorStyle_(
                0
            )  # 0: UIActivityIndicatorViewStyleLarge
            self.native_instance.hidesWhenStopped = True

        def start_animating(self) -> None:
            self.native_instance.startAnimating()

        def stop_animating(self) -> None:
            self.native_instance.stopAnimating()
