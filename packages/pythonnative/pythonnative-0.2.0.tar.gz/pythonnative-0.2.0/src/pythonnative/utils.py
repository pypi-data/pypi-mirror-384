import os
from typing import Any, Optional

# Platform detection with multiple fallbacks suitable for Chaquopy/Android
_is_android: Optional[bool] = None


def _detect_android() -> bool:
    # 1) Direct environment hints commonly present on Android
    env = os.environ
    if "ANDROID_BOOTLOGO" in env or "ANDROID_ROOT" in env or "ANDROID_DATA" in env or "ANDROID_ARGUMENT" in env:
        return True

    # 2) Chaquopy-specific: the builtin 'java' package is available
    try:
        # Import inside try so importing this module doesn't explode off-device
        from java import jclass

        _ = jclass  # silence linter unused
        return True
    except Exception:
        pass

    # 3) Last resort: some Android Python dists set os.name/others, but avoid false positives
    return False


def _ensure_platform_detection() -> None:
    global _is_android
    if _is_android is None:
        _is_android = _detect_android()


def _get_is_android() -> bool:
    _ensure_platform_detection()
    assert _is_android is not None
    return _is_android


IS_ANDROID: bool = _get_is_android()

# Global hook to access the current Android Activity/Context from Python code
_android_context: Any = None


def set_android_context(context: Any) -> None:
    """Record the current Android Activity/Context for implicit constructor use.

    On Android, Python UI components require a Context to create native views.
    We capture it when a Page is constructed from the host Activity so component
    constructors can be platform-consistent and avoid explicit context params.
    """

    global _android_context
    _android_context = context


def get_android_context() -> Any:
    """Return the previously set Android Activity/Context or raise if missing."""

    if not IS_ANDROID:
        raise RuntimeError("get_android_context() called on non-Android platform")
    if _android_context is None:
        raise RuntimeError(
            "Android context is not set. Ensure Page is initialized from an Activity " "before constructing views."
        )
    return _android_context
