from abc import ABC, abstractmethod

from .utils import IS_ANDROID
from .view import ViewBase

# ========================================
# Base class
# ========================================


class ListViewBase(ABC):
    @abstractmethod
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def set_data(self, data: list) -> None:
        pass

    @abstractmethod
    def get_data(self) -> list:
        pass


if IS_ANDROID:
    # ========================================
    # Android class
    # https://developer.android.com/reference/android/widget/ListView
    # ========================================

    from java import jclass

    class ListView(ListViewBase, ViewBase):
        def __init__(self, context, data: list = []) -> None:
            super().__init__()
            self.context = context
            self.native_class = jclass("android.widget.ListView")
            self.native_instance = self.native_class(context)
            self.set_data(data)

        def set_data(self, data: list) -> None:
            adapter = jclass("android.widget.ArrayAdapter")(
                self.context, jclass("android.R$layout").simple_list_item_1, data
            )
            self.native_instance.setAdapter(adapter)

        def get_data(self) -> list:
            adapter = self.native_instance.getAdapter()
            return [adapter.getItem(i) for i in range(adapter.getCount())]

else:
    # ========================================
    # iOS class
    # https://developer.apple.com/documentation/uikit/uitableview
    # ========================================

    from rubicon.objc import ObjCClass

    class ListView(ListViewBase, ViewBase):
        def __init__(self, data: list = []) -> None:
            super().__init__()
            self.native_class = ObjCClass("UITableView")
            self.native_instance = self.native_class.alloc().init()
            self.set_data(data)

        def set_data(self, data: list) -> None:
            # Note: This is a simplified representation. Normally, you would need to create a UITableViewDataSource.
            self.native_instance.reloadData()

        def get_data(self) -> list:
            # Note: This is a simplified representation.
            # Normally, you would need to get data from the UITableViewDataSource.
            return []
