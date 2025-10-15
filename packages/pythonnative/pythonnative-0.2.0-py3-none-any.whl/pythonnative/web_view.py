from abc import ABC, abstractmethod

from .utils import IS_ANDROID, get_android_context
from .view import ViewBase

# ========================================
# Base class
# ========================================


class WebViewBase(ABC):
    @abstractmethod
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def load_url(self, url: str) -> None:
        pass


if IS_ANDROID:
    # ========================================
    # Android class
    # https://developer.android.com/reference/android/webkit/WebView
    # ========================================

    from java import jclass

    class WebView(WebViewBase, ViewBase):
        def __init__(self, url: str = "") -> None:
            super().__init__()
            self.native_class = jclass("android.webkit.WebView")
            context = get_android_context()
            self.native_instance = self.native_class(context)
            self.load_url(url)

        def load_url(self, url: str) -> None:
            self.native_instance.loadUrl(url)

else:
    # ========================================
    # iOS class
    # https://developer.apple.com/documentation/webkit/wkwebview
    # ========================================

    from rubicon.objc import NSURL, NSURLRequest, ObjCClass

    class WebView(WebViewBase, ViewBase):
        def __init__(self, url: str = "") -> None:
            super().__init__()
            self.native_class = ObjCClass("WKWebView")
            self.native_instance = self.native_class.alloc().init()
            self.load_url(url)

        def load_url(self, url: str) -> None:
            ns_url = NSURL.URLWithString_(url)
            request = NSURLRequest.requestWithURL_(ns_url)
            self.native_instance.loadRequest_(request)
