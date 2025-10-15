# PythonNative

**PythonNative** is a cross-platform toolkit that allows you to create native Android and iOS apps using Python. Inspired by frameworks like React Native and NativeScript, PythonNative provides a Pythonic interface for building native UI elements, handling lifecycle events, and accessing platform-specific APIs.

## Features

- **Native UI Components**: Create and manage native buttons, labels, lists, and more, all from Python.
- **Cross-Platform**: Write once, run on both Android and iOS.
- **Lifecycle Management**: Handle app lifecycle events with ease.
- **Native API Access**: Access device features like Camera, Geolocation, and Notifications.
- **Powered by Proven Tools**: PythonNative integrates seamlessly with [Rubicon](https://beeware.org/project/projects/bridges/rubicon/) for iOS and [Chaquopy](https://chaquo.com/chaquopy/) for Android, ensuring robust native performance.

## Quick Start

### Installation

First, install PythonNative via pip:

```bash
pip install pythonnative
```

### Create Your First App

Initialize a new PythonNative app:

```bash
pn init my_app
```

Your app directory will look like this:

```text
my_app/
├── README.md
├── app
│   ├── __init__.py
│   ├── main_page.py
│   └── resources
├── pythonnative.json
├── requirements.txt
└── tests
```

### Writing Views

In PythonNative, everything is a view. Here's a simple example of how to create a main page with a list view:

```python
import pythonnative as pn

class MainPage(pn.Page):
    def __init__(self, native_instance):
        super().__init__(native_instance)

    def on_create(self):
        super().on_create()
        stack_view = pn.StackView(self.native_instance)
        list_data = ["item_{}".format(i) for i in range(100)]
        list_view = pn.ListView(self.native_instance, list_data)
        stack_view.add_view(list_view)
        self.set_root_view(stack_view)
```

### Run the app

```bash
pn run android
pn run ios
```

## Documentation

For detailed guides and API references, visit the [PythonNative documentation](https://docs.pythonnative.com/).
