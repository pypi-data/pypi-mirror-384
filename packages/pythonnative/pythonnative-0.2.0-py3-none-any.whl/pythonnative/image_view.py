from abc import ABC, abstractmethod

from .utils import IS_ANDROID, get_android_context
from .view import ViewBase

# ========================================
# Base class
# ========================================


class ImageViewBase(ABC):
    @abstractmethod
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def set_image(self, image: str) -> None:
        pass

    @abstractmethod
    def get_image(self) -> str:
        pass


if IS_ANDROID:
    # ========================================
    # Android class
    # https://developer.android.com/reference/android/widget/ImageView
    # ========================================

    from android.graphics import BitmapFactory
    from java import jclass

    class ImageView(ImageViewBase, ViewBase):
        def __init__(self, image: str = "") -> None:
            super().__init__()
            self.native_class = jclass("android.widget.ImageView")
            context = get_android_context()
            self.native_instance = self.native_class(context)
            if image:
                self.set_image(image)

        def set_image(self, image: str) -> None:
            bitmap = BitmapFactory.decodeFile(image)
            self.native_instance.setImageBitmap(bitmap)

        def get_image(self) -> str:
            # Please note that this is a simplistic representation, getting image from ImageView
            # in Android would require converting Drawable to Bitmap and then to File
            return "Image file path in Android"

else:
    # ========================================
    # iOS class
    # https://developer.apple.com/documentation/uikit/uiimageview
    # ========================================

    from rubicon.objc import ObjCClass
    from rubicon.objc.api import NSString, UIImage

    class ImageView(ImageViewBase, ViewBase):
        def __init__(self, image: str = "") -> None:
            super().__init__()
            self.native_class = ObjCClass("UIImageView")
            self.native_instance = self.native_class.alloc().init()
            if image:
                self.set_image(image)

        def set_image(self, image: str) -> None:
            ns_str = NSString.alloc().initWithUTF8String_(image)
            ui_image = UIImage.imageNamed_(ns_str)
            self.native_instance.setImage_(ui_image)

        def get_image(self) -> str:
            # Similar to Android, getting the image from UIImageView isn't straightforward.
            return "Image file name in iOS"
