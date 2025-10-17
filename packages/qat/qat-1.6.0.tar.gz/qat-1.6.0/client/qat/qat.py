# -*- coding: utf-8 -*-
# (c) Copyright 2023, Qat’s Authors

"""
Public Qat API
"""

# Some imports are only to make types accessible with qat.Type without using 'internal' namespace
# pylint: disable=unused-import

# Mouse events require many arguments
# pylint: disable = too-many-arguments

from pathlib import Path
from typing import Optional, Union
import atexit
import time

from qat.internal import app_launcher
from qat.internal.application_context import ApplicationContext
from qat.internal.qt_custom_object import QtCustomObject
from qat.internal.qt_object import QtObject
import qat.internal.communication_operations as comm
import qat.internal.debug_operations as debug
import qat.internal.find_object as find
import qat.internal.mouse_operations as mouse
import qat.internal.gesture_operations as gesture
import qat.internal.keyboard_operations as keyboard
import qat.internal.screenshot_operations as screenshot
import qat.internal.synchronization as sync
import qat.internal.touch_operations as touch

from qat.internal.mouse_operations import Button, Modifier
from qat.internal.xml_report import XmlReport
from qat.internal.binding import Binding
from qat.internal.global_constants import QApp, Platform, QStyleHints
from qat.internal.global_state import GlobalState

from qat.test_settings import Settings

# Global state manages application lifecycle
global_state = GlobalState()

def get_state() -> GlobalState:
    """ Return the global state for the current script """
    return global_state


@atexit.register
def close_all_apps():
    """
    Make sure all current applications are closed when a script terminates
    """
    get_state().close_apps()


###################################################################################
# Application management and configuration
###################################################################################


def register_application(name: str, path: str, args='', shared: Optional[bool] = False) -> None:
    """
    Add the given application to the configuration file.

    Args:
      name: Must be a unique name for this application. It will be used when calling :func:`start_application` for example.
      path: The absolute path to the application executable.
      args (optional): The default arguments used when launching the application (e.g. when using Qat-Spy). 
        They can be overridden when calling :func:`start_application`.
      shared (optional): True to use the shared (global) file, False to use the local one. 
        If None (default), the local file will be used if it exists otherwise the shared one will be used.
    """
    config_file = get_config_file(shared)
    app_launcher.register_application(config_file, name, path, args)


def unregister_application(name: str, shared: Optional[bool] = False) -> None:
    """
    Remove the given application from the configuration file.

    Args:
      name: The unique name of the application, must be the same as the one given to :func:`register_application`.
      shared: True to use the shared (global) file, False to use the local one.
        If None, the local file will be used if it exists otherwise the shared one will be used.
    """
    config_file = get_config_file(shared)
    app_launcher.unregister_application(config_file, name)


def list_applications() -> dict:
    """
    List all registered applications (shared and local).
    
    The contents of both local and shared configurations is merged.
    Values from the local configuration take precedence: if an application is 
    registered in both configurations with different paths or arguments, 
    the values from the local configuration will be returned.
    """
    return app_launcher.list_applications()


def get_config_file(shared: Optional[bool] = None) -> Path:
    """
    Return the absolute path to the current configuration file (applications.json).

    Args:
      shared: True to use the shared (global) file, False to use the local one.
    
    Returns:
      The absolute path to the current configuration file.

      If shared is None and if a configuration file exists in the current working directory, 
      it will be returned. Otherwise, the global one from the user directory (e.g. ~/.qat) 
      will be returned if it exists. 
      Finally, if no file exists, the path to a default file in the current working directory will be returned.
    """
    return app_launcher.get_config_file(shared)


def get_application_path(name: str) -> str:
    """
    Return the path of the given application from the configuration file.

    Args:
      name: The unique name of the application, must be the same as the one given to :func:`register_application`.
    """
    applications = list_applications()
    return applications[name]['path']


###################################################################################
# Application life cycle
###################################################################################

def start_application(app_name: str, args: str = None, detached: bool = False) -> ApplicationContext:
    """
    Start a registered application.

    Start the given application, inject the server library (except if detached is True)
    and return the corresponding application context.

    Args:
      app_name: The unique name of the application, must be the same as the one given to :func:`register_application`.
      args: A string containing arguments to be passed to the application. 
        If None (default), arguments will be read from the current configuration file.
      detached: If True, the application will start without initializing Qat. 
        This is useful when testing cases where the application returns early (e.g. in case of errors such as invalid arguments).
    
    Returns:
      An ApplicationContext that uniquely identifies the started application instance.
      Even when 'detached' argument is True, this ApplicationContext can still be used to retrieve 
      the corresponding exit code and process ID.
    """
    get_state().current_app_context = None
    get_state().current_app_context = app_launcher.start_application(app_name, args, detached)
    get_state().app_context_list.append(get_state().current_app_context)
    return get_state().current_app_context


def attach_to_application(name_or_pid) -> ApplicationContext:
    """
    Attach to the given application by name, file name or process ID.

    If a name is given, it must correspond to a registered application.
    On linux and MacOS, the application must have been launched by Qat (by calling :func:`start_application`) for this function to work.

    Args:
      name_or_pid: Can be the name of a registered application, the name of a (running) executable file or a process ID.

    Returns:
      An ApplicationContext that uniquely identifies the attached application instance.
    
    Raises:
      ProcessLookupError: The application process could not be found or failed to connect.
    """
    get_state().current_app_context = app_launcher.attach_to(name_or_pid)
    get_state().app_context_list.append(get_state().current_app_context)
    return get_state().current_app_context


def detach(contexts : Union[ApplicationContext, list] = None):
    """
    Detach the given application contexts.
    Applications will not be available to the API anymore and will not
    be closed when the calling script terminates.

    To access an application again, use the attach_to_application() function.

    Args:
      contexts: An ApplicationContext or a list of ApplicationContext to detach.
        If None (default), all current contexts will be detached.
    """
    if isinstance(contexts, ApplicationContext):
        contexts = [contexts]
    elif contexts is None:
        contexts = get_state().app_context_list.copy()

    for context in contexts:
        if not isinstance(context, ApplicationContext):
            continue
        if get_state().current_app_context == context:
            get_state().current_app_context = None
        context.detach()
        get_state().app_context_list.remove(context)


def current_application_context() -> ApplicationContext:
    """Return the current application context."""
    return get_state().current_app_context


def get_context_list() -> list:
    """Return the list of all current application contexts"""
    return get_state().app_context_list


def set_current_application_context(app_context: ApplicationContext):
    """
    Change the current application context.

    All subsequent API calls will use this context until this function is called again
    or another application is started / attached to.
    """
    get_state().current_app_context = app_context


def close_application(app_context = None) -> int:
    """
    Terminate the application associated to the given context and returns its exit code.

    Args:
      app_context: The context of the application to be closed. If None, the current context will be used.

    Returns:
      The exit code returned by the closed application.
      This usually corresponds to SIGKILL since the application is killed when calling this function.

    Raises:
      ProcessLookupError: No process were found for the given application context.
    """
    if app_context is None:
        app_context = current_application_context()
    if app_context:
        app_context.take_ownership()
        app_context.kill()
        exit_code = app_context.get_exit_code()
        get_state().current_app_context = None
        get_state().app_context_list.remove(app_context)
        return exit_code
    raise ProcessLookupError("Cannot close application: process does not exist")


###################################################################################
# Application windows
###################################################################################

def lock_application():
    """Lock application by filtering external/user events."""
    debug.lock_application(current_application_context())


def unlock_application():
    """Unlock application by allowing external/user events."""
    debug.unlock_application(current_application_context())


def list_top_windows() -> list:
    """Return all the top windows of the application."""
    return find.list_top_windows(get_state().current_app_context)


###################################################################################
# Accessing objects and widgets
###################################################################################

def find_all_objects(definition: dict) -> list:
    """
    Return all objects matching the given definition.

    Args:
      definition: A dictionary of property names and values.
    
    Returns:
      A (potentially empty) list of QtObjects corresponding to the given properties.
    """
    return find.find_all_objects(get_state().current_app_context, definition)


def wait_for_object_exists(definition: dict, timeout=None) -> QtObject:
    """
    Wait for the given object to exist in the tested application.

    Args:
      definition: A dictionary of property names and values identifying a unique object.
    
    Raises:
      LookupError: No object was found or multiple objects match the given definition.
    """
    if timeout is None:
        timeout = Settings.wait_for_object_timeout
    return find.wait_for_object_exists(get_state().current_app_context, definition, timeout)


def wait_for_object(definition: dict, timeout=None) -> QtObject:
    """
    Wait for the given object to be accessible in the application.

    This function is similar to t:func:`wait_for_object_exists` but also 
    waits for the object to be accessible (i.e. visible and enabled).

    Args:
      definition: A dictionary of property names and values identifying a unique object.
      timeout: Maximum time in milliseconds that this function will wait before raising a LookupError.
        If None (default) the timeout value will be read from the testSettings.json file.
    
    Raises:
      LookupError: No object was found before the given timeout or multiple objects match the given definition.
    """
    if timeout is None:
        timeout = Settings.wait_for_object_timeout
    return find.wait_for_object(get_state().current_app_context, definition, timeout)


def wait_for_object_missing(definition: dict, timeout=None):
    """
    Wait for the given object to be deleted from the application.

    Args:
      definition: A dictionary of property names and values identifying a unique object.
      timeout: Maximum time in milliseconds that this function will wait before raising a LookupError.
        If None (default) the timeout value will be read from the testSettings.json file.

    Raises:
      TimeoutError: The given object still exists after the given timeout (in milliseconds) has been reached.
    """
    if timeout is None:
        timeout = Settings.wait_for_object_timeout
    find.wait_for_object_missing(get_state().current_app_context, definition, timeout)


###################################################################################
# Accessing properties
###################################################################################

def wait_for_property_value(
    definition: dict,
    property_name: str,
    new_value,
    comparator = None,
    check = False,
    timeout = None) -> bool:
    """
    Wait for the given object's property to reach the given value.

    Args:
      definition: A QtObject or an object definition.
      property_name: The name of the property.
      new_value: The value to reach.
      comparator: Callable used to compare property values. == is used by default.
      check: If True, raises an exception in case of failure. False by default.
      timeout: If the new_value is not reached after this timeout (in milliseconds), returns False.

    Returns:
      True if the value was reached, False otherwise.
    """
    if timeout is None:
        timeout = Settings.wait_for_object_timeout

    def default_compare(value, reference):
        return value == reference

    return sync.wait_for_property(
        get_state().current_app_context,
        definition,
        property_name,
        new_value,
        comparator or default_compare,
        timeout,
        check)


def wait_for_property_change(
    definition: dict,
    property_name: str,
    old_value,
    comparator = None,
    check = False,
    timeout = None) -> bool:
    """
    Wait for the given object's property to change its value.

    Args:
      definition: A QtObject or an object definition.
      property_name: The name of the property.
      old_value: The original value.
      comparator: Callable used to compare property values. == is used by default.
      check: If True, raises an exception in case of failure. False by default.
      timeout: If the new_value has not changed after this timeout (in milliseconds), returns False.

    Returns:
      True if the value was changed, False otherwise.
    """
    if timeout is None:
        timeout = Settings.wait_for_object_timeout

    def default_compare(value, reference):
        return value != reference

    def reverse_comparator(value, reference):
        return not comparator(value, reference)

    return sync.wait_for_property(
        get_state().current_app_context,
        definition,
        property_name,
        old_value,
        reverse_comparator if comparator else default_compare,
        timeout,
        check)


def wait_for(condition, timeout=None) -> bool:
    """
    Wait for the given condition to be reached.

    Args:
      condition: Any expression, function or lambda returning a boolean.
      timeout: If the condition is not reached after this timeout (in milliseconds), returns False.

    Returns:
      True if the condition was reached before timeout, False otherwise
    """
    if timeout is None:
        timeout = Settings.wait_for_object_timeout
    start_time = round(1000 * time.time())
    reached = False
    while not reached and (round(1000 * time.time()) - start_time) < timeout:
        reached = condition()
        if reached:
            break
        time.sleep(0.2)

    return reached


###################################################################################
# Mouse interactions
###################################################################################

def mouse_press(
        definition: dict,
        x=None,
        y=None,
        modifier=Modifier.NONE,
        button=Button.LEFT,
        check=False):
    """
    Press a mouse button on the given widget using the given parameters.

    Args:
      definition: An object definition or an Object returned by :func:`wait_for_object*`.
      x, y: The coordinates of the event, relative to the object. If not given, event will occur at the center of the object.
      modifier: Optional keyboard modifier. Must be one of the constants in qat.Modifier. Default is NONE.
      button: Optional mouse button. Must be one of the constants in qat.Button. Default is LEFT.
      check: Optional check. When True, this function will raise an exception if no widget accepted the event. Default is False.
    """
    mouse.click(get_state().current_app_context, definition,
                "press", x, y, modifier, button, check)


def mouse_release(
        definition: dict,
        x=None,
        y=None,
        modifier=Modifier.NONE,
        button=Button.LEFT,
        check=False):
    """
    Release a mouse button on the given widget using the given parameters.
    
    Args:
      definition: An object definition or an Object returned by :func:`wait_for_object*`.
      x, y: The coordinates of the event, relative to the object. If not given, event will occur at the center of the object.
      modifier: Optional keyboard modifier. Must be one of the constants in qat.Modifier. Default is NONE.
      button: Optional mouse button. Must be one of the constants in qat.Button. Default is LEFT.
      check: Optional check. When True, this function will raise an exception if no widget accepted the event. Default is False.
    """
    mouse.click(get_state().current_app_context, definition,
                "release", x, y, modifier, button, check)


def mouse_click(
        definition: dict,
        x=None,
        y=None,
        modifier=Modifier.NONE,
        button=Button.LEFT,
        check=False):
    """
    Click on the given widget using the given parameters.
        
    Args:
      definition: An object definition or an Object returned by :func:`wait_for_object*`.
      x, y: The coordinates of the event, relative to the object. If not given, event will occur at the center of the object.
      modifier: Optional keyboard modifier. Must be one of the constants in qat.Modifier. Default is NONE.
      button: Optional mouse button. Must be one of the constants in qat.Button. Default is LEFT.
      check: Optional check. When True, this function will raise an exception if no widget accepted the event. Default is False.
        """
    mouse.click(get_state().current_app_context, definition,
                "click", x, y, modifier, button, check)


def double_click(
        definition: dict,
        x=None,
        y=None,
        modifier=Modifier.NONE,
        button=Button.LEFT,
        check=False):
    """
    Double-click on the given widget using the given parameters.
        
    Args:
      definition: An object definition or an Object returned by :func:`wait_for_object*`.
      x, y: The coordinates of the event, relative to the object. If not given, event will occur at the center of the object.
      modifier: Optional keyboard modifier. Must be one of the constants in qat.Modifier. Default is NONE.
      button: Optional mouse button. Must be one of the constants in qat.Button. Default is LEFT.
      check: Optional check. When True, this function will raise an exception if no widget accepted the event. Default is False.
    """
    mouse.click(get_state().current_app_context, definition,
                "double-click", x, y, modifier, button, check)


def mouse_move(
        definition: dict,
        x=None,
        y=None,
        modifier=Modifier.NONE,
        button=Button.LEFT):
    """
    Move the mouse using the given parameters.

    If :func:`mousePress` was called before, this will act as drag operation.

    Args:
      definition: An object definition or an Object returned by :func:`wait_for_object*`.
      x, y: the coordinates of the event, relative to the object. If not given, event will occur at the center of the object.
      modifier: Optional keyboard modifier. Must be one of the constants in qat.Modifier. Default is NONE.
      button: Optional mouse button. Must be one of the constants in qat.Button. Default is LEFT.
    """
    mouse.click(get_state().current_app_context, definition,
                "move", x, y, modifier, button)


def mouse_drag(
        definition: dict,
        x=None,
        y=None,
        dx=None,
        dy=None,
        modifier=Modifier.NONE,
        button=Button.LEFT,
        check=False):
    """
    Drag the mouse using the given parameters.

    Args:
      definition: An object definition or an Object returned by :func:`wait_for_object*`.
      x, y: The coordinates of the event, relative to the object. If not given, event will occur at the center of the object.
      dx, dy: the number of pixels to move the mouse by, in each direction.
      modifier: Optional keyboard modifier. Must be one of the constants in qat.Modifier. Default is NONE.
      button: Optional mouse button. Must be one of the constants in qat.Button. Default is LEFT.
      check: Optional check. When True this function will raise an exception if no widget accepted the event. Default is False.
    """
    mouse.drag(get_state().current_app_context, definition, 'drag', x,
               y, dx, dy, modifier, button, check=check)


def mouse_wheel(
        definition: dict,
        x=None,
        y=None,
        x_degrees=0,
        y_degrees=0,
        modifier=Modifier.NONE,
        check=False):
    """
    Scroll the mouse by x_degrees, y_degrees at x,y position.

    Default degree increment should be 15 to represent one physical rotation increment.

    Args:
      definition: An object definition or an Object returned by :func:`wait_for_object*`.
      x, y: the coordinates of the event, relative to the object. If not given, event will occur at the center of the object.
      modifier: Optional keyboard modifier. Must be one of the constants in qat.Modifier. Default is NONE.
      button: Optional mouse button. Must be one of the constants in qat.Button. Default is LEFT.
      check: Optional check. When True this function will raise an exception if no widget accepted the event. Default is False.
    """
    mouse.drag(get_state().current_app_context, definition, 'scroll', x, y, 8 * x_degrees,
               8 * y_degrees, modifier=modifier, button=Button.MIDDLE, check=check)


###################################################################################
# Touch screen/pad interactions
###################################################################################

def touch_press(
        definition: dict,
        x=None,
        y=None,
        modifier=Modifier.NONE):
    """
    Press fingers on the given widget using the given parameters.

    Press one or more fingers on the definition object at local coordinates x, y while holding the modifier key.

    Args:
      definition: An object definition or an Object returned by :func:`wait_for_object*`.
      x, y: the coordinates of each finger, relative to the object. If not given, event will occur at the center of the object. 
        Each argument can be a single value (for single touch point) or an array (for multiple touch points). 
        When using arrays, x and y must be of the same size.
      modifier: Optional keyboard modifier. Must be one of the constants in qat.Modifier. Default is NONE.
    """
    touch.tap(get_state().current_app_context, definition,
                "press", x, y, modifier)


def touch_release(
        definition: dict,
        x=None,
        y=None,
        modifier=Modifier.NONE):
    """
    Release fingers on the given widget using the given parameters.

    Release one or more fingers on the definition object at local coordinates x, y while holding the modifier key.

    Args:
      definition: An object definition or an Object returned by :func:`wait_for_object*`.
      x, y: the coordinates of each finger, relative to the object. If not given, event will occur at the center of the object. 
        Each argument can be a single value (for single touch point) or an array (for multiple touch points). 
        When using arrays, x and y must be of the same size.
      modifier: Optional keyboard modifier. Must be one of the constants in qat.Modifier. Default is NONE.
    """
    touch.tap(get_state().current_app_context, definition,
                "release", x, y, modifier)


def touch_tap(
        definition: dict,
        x=None,
        y=None,
        modifier=Modifier.NONE):
    """
    Tap on the given widget using the given parameters.

    Tap one or more fingers on the definition object at local coordinates x, y while holding the modifier
    Note that sending two touch_tap events quickly will not generate a double-tap event. Use "func:`double_click` instead.

    Args:
      definition: An object definition or an Object returned by :func:`wait_for_object*`.
      x, y: the coordinates of each finger, relative to the object. If not given, event will occur at the center of the object. 
        Each argument can be a single value (for single touch point) or an array (for multiple touch points). 
        When using arrays, x and y must be of the same size.
      modifier: Optional keyboard modifier. Must be one of the constants in qat.Modifier. Default is NONE.
    """
    touch.tap(get_state().current_app_context, definition,
                "tap", x, y, modifier)


def touch_move(
        definition: dict,
        x=None,
        y=None,
        modifier=Modifier.NONE):
    """
    Move fingers on the given widget using the given parameters.

    Move one or more fingers on the definition object at local coordinates x, y while holding the modifier key.

    Args:
      definition: An object definition or an Object returned by :func:`wait_for_object*`.
      x, y: the coordinates of each finger, relative to the object. If not given, event will occur at the center of the object. 
        Each argument can be a single value (for single touch point) or an array (for multiple touch points). 
        When using arrays, x and y must be of the same size.
      modifier: Optional keyboard modifier. Must be one of the constants in qat.Modifier. Default is NONE.
    """
    touch.tap(get_state().current_app_context, definition,
                "move", x, y, modifier)


def touch_drag(
        definition: dict,
        x=None,
        y=None,
        dx=0,
        dy=0,
        modifier=Modifier.NONE):
    """
    Drag fingers on the given widget using the given parameters.

    Press and drag one or more fingers on the definition object starting at local coordinates x, y while holding the modifier key.

    Args:
      definition: An object definition or an Object returned by :func:`wait_for_object*`.
      x, y: the coordinates of each finger, relative to the object. If not given, event will occur at the center of the object. 
        Each argument can be a single value (for single touch point) or an array (for multiple touch points). 
        When using arrays, x and y must be of the same size.
      dx, dy: the number of pixels to move each finger, relative to the object. 
        Each argument can be a single value (to apply the same movement to all touch points) or 
        an array (to have different movements for each touch point). 
        When using arrays, dx and dy must be of the same size.
      modifier: Optional keyboard modifier. Must be one of the constants in qat.Modifier. Default is NONE.
    """
    touch.drag(get_state().current_app_context, definition, 'drag', x,
               y, dx, dy, modifier)


###################################################################################
# Gestures
###################################################################################

def flick(
        definition: dict,
        dx=0,
        dy=0):
    """
    Move the given Flickable by the given horizontal and vertical distances in pixels.

    Args:
      definition: An object definition or an Object returned by :func:`wait_for_object*`.
      dx: the horizontal distance in pixels.
      dy: the vertical distance in pixels.
    """
    gesture.flick(get_state().current_app_context, definition, dx, dy)


def pinch(
        definition: dict,
        rotation = 0.,
        translation = None,
        scale = 1.0):
    """
    Generate a pinch event (zoom, rotation, pan).

    All three optional parameters can be combined to define a complete pinch gesture.
    The distance between the two fingers during the gesture will be automatically determined based on the target widget’s size.

    Args:
      definition: An object definition or an Object returned by :func:`wait_for_object*`.
      rotation (optional): Total angle of rotation to apply. Value is in degrees and in clockwise direction.
      translation (optional): Global translation of the pinch. This corresponds to the translation 
        of the central point between the two fingers.
      scale (optional): Variation of the distance between the two fingers, typically representing a zoom factor. 
        For example, if scale is set to 2.0, the distance between the fingers will double between the beginning and the end of the gesture.
    """
    gesture.pinch(
        get_state().current_app_context,
        definition,
        rotation,
        translation,
        scale
    )


def native_pinch(
        definition: dict,
        angle: int = None,
        scale: float = None,
        check: bool = False):
    """
    Generate a native pinch event (zoom and/or rotation).

    Native gesture events are high-level events generated by the operating system, usually from a sequence of trackpad events.
    This function works with QML/QtQuick widgets only.

    Args:
      definition: An object definition or an Object returned by :func:`wait_for_object*`.
      angle (optional): Total angle of rotation to apply. Value is in degrees and in clockwise direction.
      scale (optional): Variation of the distance between the two fingers, typically representing a zoom factor. 
        For example, if scale is set to 2.0, the distance between the fingers will double between the beginning and the end of the gesture.
      check (optional): If True, raises an exception in case of failure (i.e when the event is not handled by any widget). False by default.
    """
    gesture.native_pinch(
        get_state().current_app_context,
        definition,
        angle,
        scale,
        check)


###################################################################################
# Keyboard interactions
###################################################################################

def type_in(
        definition: dict,
        text: str):
    """
    Type the given text in the given object.

    Args:
      definition: An object definition or an Object returned by :func:`wait_for_object*`.
      text: Any string. Can also use the following special keys: 
        <Backspace>, <Delete>, <Enter>, <Escape>, <Return>, <Tab>, <Control>, <Shift>, <Alt>
    """
    keyboard.type_in(get_state().current_app_context, definition, text)


def shortcut(
        definition: dict,
        key_combination: str):
    """
    Trigger the given shortcut on the given object.

    Shortcut string must follow the Qt syntax, e.g:
    'Ctrl+Z, Alt+O, Alt+Shift+R, ...'

    Args:
      definition: An object definition or an Object returned by :func:`wait_for_object*`.
      key_combination: The key combination to trigger.
    """
    keyboard.shortcut(get_state().current_app_context, definition, key_combination)


def press_key(
        definition: dict,
        key: str):
    """
    Press the given key on the given object.

    Args:
      definition: An object definition or an Object returned by :func:`wait_for_object*`.
      text: Any character. Can also use the following special keys: 
        <Backspace>, <Delete>, <Enter>, <Escape>, <Return>, <Tab>, <Control>, <Shift>, <Alt>
    """
    keyboard.press_key(get_state().current_app_context, definition, key)


def release_key(
        definition: dict,
        key: str):
    """
    Release the given key on the given object.

    Args:
      definition: An object definition or an Object returned by :func:`wait_for_object*`.
      text: Any character. Can also use the following special keys: 
        <Backspace>, <Delete>, <Enter>, <Escape>, <Return>, <Tab>, <Control>, <Shift>, <Alt>
    """
    keyboard.release_key(get_state().current_app_context, definition, key)



###################################################################################
# Screenshots
###################################################################################

def take_screenshot(path=None):
    """
    Take a screenshot of each current top-level window.
     
    Screenshots will be saved to the given path. If no path is provided, screenshots will be
    saved to the 'screenshots' subfolder of the current directory.
    The file name will be qat-screenshotN.png, where N is the index of the window.

    Args:
      path: Path to save the screenshots. Extension will determine the format of the image file (png, jpg, bmp, ...).
    """
    screenshot.take_screenshot(get_state().current_app_context, path)


def grab_screenshot(definition, delay=0, timeout=None):
    """
    Take a screenshot of the given widget after an optional delay in ms.

    Args:
      definition: An object definition or an Object returned by :func:`wait_for_object*`.
      delay: Wait delay milliseconds before taking the screenshot. Default is 0: no delay.
      timeout: Number of milliseconds to wait for the screenshot to be available once taken. If timeout is reached, an exception is raised.

    Returns:
      An Image object which provides the following functions:
        def getPixel(x: int, y: int) -> int
        def getPixelRGBA(x: int, y: int) -> Color
        def save(file_name: str)

    Raises:
      LookupError: The given object could not be found.
      RuntimeError: The image could not be generated.
    """
    if timeout is None:
        timeout = Settings.wait_for_object_timeout
    return screenshot.grab_screenshot(get_state().current_app_context, definition, delay, timeout)



###################################################################################
# Picking
###################################################################################

def activate_picker():
    """Activate the object picker"""
    debug.activate_picker(get_state().current_app_context)


def deactivate_picker():
    """Deactivate the object picker"""
    debug.deactivate_picker(get_state().current_app_context)



###################################################################################
# Connections and bindings
###################################################################################

def connect(
        object_def: dict,
        property_or_signal: str,
        callback) -> str:
    """
    Connect a signal from the application to the given callback.

    If 'property_or_signal' is a Qt property name, the given callback will be called with
    one argument containing the new value of the property.

    If 'property_or_signal' is a signal signature, the given callback will be called with the arguments
    from the signal. Callback must have at most as many arguments as the signal does, otherwise
    a TypeError exception will be raised. Argument types must also be compatible.

    Args:
      object_def: An object definition or an Object returned by :func:`wait_for_object*`.
      property_or_signal: The name of the property or signal to connect to.
      callback: A Python Callable (e.g. function or lambda).

    Returns:
      A unique identifier for the newly created connection.
    
    Raises:
      - RuntimeError if signal was not found or invalid.
      - TypeError if callback has more arguments than signal.
    """
    return comm.connect(get_state().current_app_context, object_def, property_or_signal, callback)


def disconnect(conn_id: str):
    """
    Disconnect a signal from its callback.

    Args:
      conn_id: A connection identifier, as returned by :fund:`connect`.
    """
    return comm.disconnect(get_state().current_app_context, conn_id)


def bind(
        remote_object: dict,
        remote_property: str,
        local_object,
        local_property: str) -> Binding:
    """
    Automatically establish a connection between the given object's property and the given receiver.

    Note: this is equivalent to create a Binding object with the same arguments.

    Args:
      remote_object: An object definition or an Object returned by :func:`wait_for_object*`.
      remote_property: The name of the property or signal to connect to.
      local_object: Any Python object.
      local_attribute: The name of the Python attribute to be connected. 
        Must be an attribute of local_object and be of a compatible type.
    
    Returns:
      A Binding object that can be used to manage the connection with the following functions:
        def connect(): Connect (or re-connect) this binding to the remote object.
        def disconnect(): Disconnect this binding. Receiver will not be updated anymore.
    """
    return Binding(remote_object, remote_property, local_object, local_property)
