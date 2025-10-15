from importlib import import_module
from typing import Any, Dict

__version__ = "0.2.0"

__all__ = [
    "ActivityIndicatorView",
    "Button",
    "DatePicker",
    "ImageView",
    "Label",
    "ListView",
    "MaterialActivityIndicatorView",
    "MaterialButton",
    "MaterialDatePicker",
    "MaterialProgressView",
    "MaterialSearchBar",
    "MaterialSwitch",
    "MaterialTimePicker",
    "MaterialBottomNavigationView",
    "MaterialToolbar",
    "Page",
    "PickerView",
    "ProgressView",
    "ScrollView",
    "SearchBar",
    "StackView",
    "Switch",
    "TextField",
    "TextView",
    "TimePicker",
    "WebView",
]

_NAME_TO_MODULE: Dict[str, str] = {
    "ActivityIndicatorView": ".activity_indicator_view",
    "Button": ".button",
    "DatePicker": ".date_picker",
    "ImageView": ".image_view",
    "Label": ".label",
    "ListView": ".list_view",
    "MaterialActivityIndicatorView": ".material_activity_indicator_view",
    "MaterialButton": ".material_button",
    "MaterialDatePicker": ".material_date_picker",
    "MaterialProgressView": ".material_progress_view",
    "MaterialSearchBar": ".material_search_bar",
    "MaterialSwitch": ".material_switch",
    "MaterialTimePicker": ".material_time_picker",
    "MaterialBottomNavigationView": ".material_bottom_navigation_view",
    "MaterialToolbar": ".material_toolbar",
    "Page": ".page",
    "PickerView": ".picker_view",
    "ProgressView": ".progress_view",
    "ScrollView": ".scroll_view",
    "SearchBar": ".search_bar",
    "StackView": ".stack_view",
    "Switch": ".switch",
    "TextField": ".text_field",
    "TextView": ".text_view",
    "TimePicker": ".time_picker",
    "WebView": ".web_view",
}


def __getattr__(name: str) -> Any:
    module_path = _NAME_TO_MODULE.get(name)
    if not module_path:
        raise AttributeError(f"module 'pythonnative' has no attribute {name!r}")
    module = import_module(module_path, package=__name__)
    return getattr(module, name)


def __dir__() -> Any:
    return sorted(list(globals().keys()) + __all__)
