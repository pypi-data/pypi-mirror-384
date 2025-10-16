# PyQtPaint
**This is still a work in progress, but basic functionality is present.**
A library of boilerplate code using the PyQt5 library. Used for creating a window to draw in and having an application and update thread. Also comes with some predefined objects to add to the window for drawing.

## Modules
* `PyQtPaint.app`:
Contains the `App` abstract class for running the window and updates to it.

* `PyQtPaint.form`:
Contains the `PainterWindow` class of which objects can be added and removed from it. These objects will be painted on every update call.

* `PyQtPaint.objects`:
Contains the `PainterObject` abstract class which descendants will have paint methods and other styling methods for customizing the object.

## Examples:
Press `esc` to close.
* tree_app.py
* mouse_app.py

## Usage:
The expected way to use this library to to create a class that extends App.
The subclass can override various methods inside of App and there are options for further customization.

### App Options:
These will be keyword arguments that are passed into the super constructor.
* `auto_update`: Defaults to `True`; determines if an asynchronous thread should be made and ran
* `fps`: Defaults to `30`; will be the amount of times the `update` method is called in a second
* `mouse_tracking`: Defaults to `False`; Will not capture mouse movements unless a button is down when `False`
* `title`: Defaults to `Painter Window`; The title to be displayed on the window
* `fullscreen`: Defaults to `False`; If `True` the window will be in fullscreen mode
* `size`: The size of the window as a tuple `(width, height)`
* `width`: Defaults to `600`; If not `size` the width of the window
* `height`: Defaults to `600`; If not `size` the height of the window
* `position`: Defaults to `(0, 0)`; Where the window should be placed on the screen
* `render_hint`: Defaults to `QPainter.Antialiasing`; The render hint the window should use when painting
* `background`: Defaults to `QBrush(Qt.black)`; The `QBrush` the background should use

### Methods to override:
#### Standard:
* `setup_objects`:
	* Automatically called in the constructor
	* Where the initial painter objects should be added to the window
* `update`:
	* When `auto_update` is true will be called asynchronously multiple times a second based on `fps`
	* When `auto_update` is false call `update` manually when you need a repaint
#### Events:
They will all have an event parameter
##### Keys:
* `keyPress`
* `keyRelease`
##### Mouse:
* `mousePress`
* `mouseRelease`
* `mouseDouble`
* `mouseMove`
* `mouseEnter`
* `mouseLeave`
* `mouseWheel`