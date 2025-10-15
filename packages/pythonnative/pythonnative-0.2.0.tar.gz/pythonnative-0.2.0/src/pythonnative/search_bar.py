from abc import ABC, abstractmethod

from .utils import IS_ANDROID
from .view import ViewBase

# ========================================
# Base class
# ========================================


class SearchBarBase(ABC):
    @abstractmethod
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def set_query(self, query: str) -> None:
        pass

    @abstractmethod
    def get_query(self) -> str:
        pass


if IS_ANDROID:
    # ========================================
    # Android class
    # https://developer.android.com/reference/android/widget/SearchView
    # ========================================

    from java import jclass

    class SearchBar(SearchBarBase, ViewBase):
        def __init__(self, context, query: str = "") -> None:
            super().__init__()
            self.native_class = jclass("android.widget.SearchView")
            self.native_instance = self.native_class(context)
            self.set_query(query)

        def set_query(self, query: str) -> None:
            self.native_instance.setQuery(query, False)

        def get_query(self) -> str:
            return self.native_instance.getQuery().toString()

else:
    # ========================================
    # iOS class
    # https://developer.apple.com/documentation/uikit/uisearchbar
    # ========================================

    from rubicon.objc import ObjCClass

    class SearchBar(SearchBarBase, ViewBase):
        def __init__(self, query: str = "") -> None:
            super().__init__()
            self.native_class = ObjCClass("UISearchBar")
            self.native_instance = self.native_class.alloc().init()
            self.set_query(query)

        def set_query(self, query: str) -> None:
            self.native_instance.set_text_(query)

        def get_query(self) -> str:
            return self.native_instance.text()
