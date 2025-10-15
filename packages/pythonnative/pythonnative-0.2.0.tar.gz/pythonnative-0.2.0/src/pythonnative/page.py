"""
Your current approach, which involves creating an Android Activity in Kotlin
and then passing it to Python, is necessary due to the restrictions inherent
in Android's lifecycle. You are correctly following the Android way of managing
Activities. In Android, the system is in control of when and how Activities are
created and destroyed. It is not possible to directly create an instance of an
Activity from Python because that would bypass Android's lifecycle management,
leading to unpredictable results.

Your Button example works because Button is a View, not an Activity. View
instances in Android can be created and managed directly by your code. This is
why you are able to create an instance of Button from Python.

Remember that Activities in Android are not just containers for your UI like a
ViewGroup, they are also the main entry points into your app and are closely
tied to the app's lifecycle. Therefore, Android needs to maintain tight control
over them. Activities aren't something you instantiate whenever you need them;
they are created in response to a specific intent and their lifecycle is
managed by Android.

So, to answer your question: Yes, you need to follow this approach for
Activities in Android. You cannot instantiate an Activity from Python like you
do for Views.

On the other hand, for iOS, you can instantiate a UIViewController directly
from Python. The example code you provided for this is correct.

Just ensure that your PythonNative UI framework is aware of these platform
differences and handles them appropriately.
"""

from abc import ABC, abstractmethod

from .utils import IS_ANDROID, set_android_context
from .view import ViewBase

# ========================================
# Base class
# ========================================


class PageBase(ABC):
    @abstractmethod
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def set_root_view(self, view) -> None:
        pass

    @abstractmethod
    def on_create(self) -> None:
        pass

    @abstractmethod
    def on_start(self) -> None:
        pass

    @abstractmethod
    def on_resume(self) -> None:
        pass

    @abstractmethod
    def on_pause(self) -> None:
        pass

    @abstractmethod
    def on_stop(self) -> None:
        pass

    @abstractmethod
    def on_destroy(self) -> None:
        pass

    @abstractmethod
    def on_restart(self) -> None:
        pass

    @abstractmethod
    def on_save_instance_state(self) -> None:
        pass

    @abstractmethod
    def on_restore_instance_state(self) -> None:
        pass

    @abstractmethod
    def navigate_to(self, page) -> None:
        pass


if IS_ANDROID:
    # ========================================
    # Android class
    # https://developer.android.com/reference/android/app/Activity
    # ========================================

    from java import jclass

    class Page(PageBase, ViewBase):
        def __init__(self, native_instance) -> None:
            super().__init__()
            self.native_class = jclass("android.app.Activity")
            self.native_instance = native_instance
            # self.native_instance = self.native_class()
            # Stash the Activity so child views can implicitly acquire a Context
            set_android_context(native_instance)

        def set_root_view(self, view) -> None:
            self.native_instance.setContentView(view.native_instance)

        def on_create(self) -> None:
            print("Android on_create() called")

        def on_start(self) -> None:
            print("Android on_start() called")

        def on_resume(self) -> None:
            print("Android on_resume() called")

        def on_pause(self) -> None:
            print("Android on_pause() called")

        def on_stop(self) -> None:
            print("Android on_stop() called")

        def on_destroy(self) -> None:
            print("Android on_destroy() called")

        def on_restart(self) -> None:
            print("Android on_restart() called")

        def on_save_instance_state(self) -> None:
            print("Android on_save_instance_state() called")

        def on_restore_instance_state(self) -> None:
            print("Android on_restore_instance_state() called")

        def navigate_to(self, page) -> None:
            # intent = jclass("android.content.Intent")(self.native_instance, page.native_class)
            intent = jclass("android.content.Intent")(
                self.native_instance,
                jclass("com.pythonnative.pythonnative.SecondActivity"),
            )
            self.native_instance.startActivity(intent)

else:
    # ========================================
    # iOS class
    # https://developer.apple.com/documentation/uikit/uiviewcontroller
    # ========================================

    from rubicon.objc import ObjCClass, ObjCInstance

    class Page(PageBase, ViewBase):
        def __init__(self, native_instance) -> None:
            super().__init__()
            self.native_class = ObjCClass("UIViewController")
            # If Swift passed us an integer pointer, wrap it as an ObjCInstance.
            if isinstance(native_instance, int):
                try:
                    native_instance = ObjCInstance(native_instance)
                except Exception:
                    native_instance = None
            self.native_instance = native_instance
            # self.native_instance = self.native_class.alloc().init()

        def set_root_view(self, view) -> None:
            # UIViewController.view is a property; access without calling.
            root_view = self.native_instance.view
            # Size the root child to fill the controller's view and enable autoresizing
            try:
                bounds = root_view.bounds
                view.native_instance.setFrame_(bounds)
                # UIViewAutoresizingFlexibleWidth (2) | UIViewAutoresizingFlexibleHeight (16)
                view.native_instance.setAutoresizingMask_(2 | 16)
            except Exception:
                pass
            root_view.addSubview_(view.native_instance)

        def on_create(self) -> None:
            print("iOS on_create() called")

        def on_start(self) -> None:
            print("iOS on_start() called")

        def on_resume(self) -> None:
            print("iOS on_resume() called")

        def on_pause(self) -> None:
            print("iOS on_pause() called")

        def on_stop(self) -> None:
            print("iOS on_stop() called")

        def on_destroy(self) -> None:
            print("iOS on_destroy() called")

        def on_restart(self) -> None:
            print("iOS on_restart() called")

        def on_save_instance_state(self) -> None:
            print("iOS on_save_instance_state() called")

        def on_restore_instance_state(self) -> None:
            print("iOS on_restore_instance_state() called")

        def navigate_to(self, page) -> None:
            self.native_instance.navigationController().pushViewControllerAnimated_(page.native_instance, True)
