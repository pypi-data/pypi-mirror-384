"""
.. versionadded:: 3.8.0

This module contains various `trait types <https://docs.enthought.com/traits/traits_user_manual/intro.html>`__, which
can be used in the context of :ref:`custom modifiers <writing_custom_modifiers>`, :ref:`custom viewport overlays <writing_custom_viewport_overlays>`, and
other Python-based extensions for OVITO. Traits encapsulate :ref:`object parameters <writing_custom_modifiers.advanced_interface.user_params>`,
which are displayed in the OVITO graphical user interface and can be adjusted by the user.

The specific trait types defined in this module supplement the `generic trait types <https://docs.enthought.com/traits/traits_user_manual/defining.html#predefined-traits>`__
provided by the `Traits <https://docs.enthought.com/traits/index.html>`__ Python package, which can be used to define parameters with simple data types such as numeric values and
strings. The OVITO-specific trait types in this module are tailored to the needs of OVITO's Python scripting interface and provide additional functionality
for interacting with the OVITO data pipeline, the undo system, and the graphical user interface.

The following OVITO-specific trait types are available:

- :py:class:`OvitoObject`: A trait type that stores an instance of a class from the :py:mod:`ovito` package, e.g. a visual element, modifier, or data object.
- :py:class:`Color`: A trait type that stores a tuple of three floats representing the RGB components of a color parameter.
- :py:class:`Vector2`: A trait type that stores a tuple of two floats representing a vector or point in 2d space.
- :py:class:`Vector3`: A trait type that stores a tuple of three floats representing a vector or point in 3d space.
- :py:class:`Matrix3`: A trait type that stores a 3-by-3 floating-point matrix.
- :py:class:`FilePath`: A trait type that stores a filesystem path. In the GUI, a file selection dialog is displayed for the user to pick the trait value.
- :py:class:`DataObjectReference`: A trait type that holds a reference to a certain :py:class:`~ovito.data.DataObject` in a :py:class:`~ovito.data.DataCollection` object hierarchy.
- :py:class:`PropertyReference`: A trait type that holds a reference to a :py:class:`~ovito.data.Property`.
"""

from collections.abc import Iterable
import ovito.nonpublic
import ovito.data
from typing import Optional, Union, Callable
import collections.abc
from enum import Enum
from functools import wraps
import warnings
import numbers
import traits.api
import traits.observation.exception_handling

__all__ = [
    "action_handler",
    "Color",
    "ColorTrait",
    "DataObjectReference",
    "FilePath",
    "Matrix3",
    "OvitoObject",
    "OvitoObjectTrait",
    "PropertyReference",
    "Vector2",
    "Vector3",
]

def action_handler(button_trait_name: str) -> Callable:
    """
    A decorator for handler methods that handle button events in the GUI. See :ref:`writing_custom_modifiers.advanced_interface.user_params`
    for more information on GUI traits.

    Use this decorator to mark a method of your class as an event handler for a :py:class:`traits.trait_types.Button` trait.
    The handler method will be called when the user clicks the button in the OVITO graphical user interface.

    :param button_trait_name: The name of the button trait that the handler method should respond to.

    **Usage example**:

    .. literalinclude:: ../example_snippets/action_handler_decorator.py
        :lines: 5-14

    .. note::

        The OVITO GUI does not support the *label* argument of the :py:class:`~traits.trait_types.Button` trait constructor.
        Please use the *ovito_label* metadata key instead to specify the button's label in the GUI: ``Button(ovito_label="Click me")``.

    If your handler is performing a long-running operation, it should be written as a Python generator function that yields
    status strings or progress values to the GUI. The GUI will display these messages in a progress dialog window
    while the handler is running. The ``yield`` statement also gives the GUI a chance to handle user input events
    and keep the application responsive. It allows the user to cancel the long-running task.

    .. literalinclude:: ../example_snippets/action_handler_decorator.py
        :lines: 22-28

    Any exceptions raised by the handler method will be caught by the GUI and displayed to the user in a message box.

    .. versionadded:: 3.12.0

    """
    # All this decorator does is to attach the button trait name to the method as a hidden attribute.
    # The hidden attribute will be looked up by the C++ GUI code that runs the matching handler method
    # when the trait's button is clicked by the user.
    def decorator(method):
        @wraps(method)
        def wrapper(self, *args, **kwargs):
            return method(self, *args, **kwargs)
        if not hasattr(wrapper, "_action_button_trait"):
            # Store name of button trait as an attribute.
            wrapper._action_button_trait = button_trait_name  # type: ignore
        return wrapper
    return decorator

class OvitoObject(traits.api.Instance):
    """
    A `trait type <https://docs.enthought.com/traits/traits_user_manual/intro.html>`__ that stores an instance of a class from the :py:mod:`ovito` package,
    e.g. a visual element, modifier, or data object. The object instance is treated as an sub-object of the class defining the trait,
    and the sub-object's parameters are displayed in the OVITO graphical user interface such that the user can adjust its settings.
    See :ref:`writing_custom_modifiers.advanced_interface.user_params` for more information.

    :param klass: The object class type to instantiate.
    :param params: All other keyword parameters are forwarded to the constructor of the object class.

    **Usage example**:

    .. literalinclude:: ../example_snippets/ovito_object_trait.py
      :lines: 5-22

    """

    def __init__(self, klass, factory=None, ovito_hide_object=False, **params):
        params["_load_user_defaults_in_gui"] = (
            True  # Initialize object parameters to user default values when running in the GUI environment.
        )
        for key in params.keys():
            if key.startswith("ovito_"):
                warnings.warn(
                    f"OvitoObject trait does not accept 'ovito_*' metadata keys.",
                    stacklevel=2,
                )
        super().__init__(klass, factory=factory, kw=params, ovito_hide_object=ovito_hide_object)


class Color(traits.api.BaseTuple):
    """
    A `trait type <https://docs.enthought.com/traits/traits_user_manual/intro.html>`__ that stores a tuple of three floats representing the RGB components of a color parameter.
    The three components must be in the range 0.0 - 1.0.

    See :ref:`writing_custom_modifiers.advanced_interface.user_params` for more information.

    :param default: The initial RGB values to be assigned to the parameter trait.
    :param metadata: Additional keyword arguments are forwarded to the base trait constructor.
    """

    def __init__(self, default=(1.0, 1.0, 1.0), **metadata):
        default = tuple(map(float, default))
        if len(default) != 3:
            raise ValueError("Expected tuple of length 3.")
        super().__init__(default, **metadata)

    # Override the validate() method to also accept NumPy arrays.
    # Some OVITO functions return RGB colors as NumPy arrays, not tuples.
    def validate(self, object, name, value):
        if not isinstance(value, tuple) and isinstance(value, Iterable):
            value = tuple(map(float, value))
        return super().validate(object, name, value)


class FilePath(traits.api.BaseFile):
    """
    A `trait type <https://docs.enthought.com/traits/traits_user_manual/intro.html>`__ that stores a filesystem path.
    In the GUI, a file selection dialog is displayed for the user to pick the trait value.

    See :ref:`writing_custom_modifiers.advanced_interface.user_params` for more information.

    :param default: Initial parameter trait value.
    :param metadata: Additional keyword arguments are forwarded to the base trait constructor.

    .. versionadded:: 3.10.0
    """

    def __init__(self, default: str = "", **metadata) -> None:
        super().__init__(default, **metadata)


class Vector2(traits.api.BaseTuple):
    """
    A `trait type <https://docs.enthought.com/traits/traits_user_manual/intro.html>`__ that stores a tuple of two floats, which represent a vector or point in 2d space.

    See :ref:`writing_custom_modifiers.advanced_interface.user_params` for more information.

    :param default: The initial vector value to be assigned to the parameter trait.
    :param metadata: Additional keyword arguments are forwarded to the base trait constructor.

    .. versionadded:: 3.10.0
    """

    def __init__(self, default=(0.0, 0.0), **metadata):
        default = tuple(map(float, default))
        if len(default) != 2:
            raise ValueError("Expected tuple of length 2.")
        super().__init__(default, **metadata)

    # Override the validate() method to also accept NumPy arrays.
    # Some OVITO functions return Vector2 values as NumPy arrays, not tuples.
    def validate(self, object, name, value):
        value = tuple(map(float, value))
        return super().validate(object, name, value)


class Vector3(traits.api.BaseTuple):
    """
    A `trait type <https://docs.enthought.com/traits/traits_user_manual/intro.html>`__ that stores a tuple of three floats, which represent a vector or point in 3d space.

    See :ref:`writing_custom_modifiers.advanced_interface.user_params` for more information.

    :param default: The initial vector value to be assigned to the parameter trait.
    :param metadata: Additional keyword arguments are forwarded to the base trait constructor.

    .. versionadded:: 3.10.0
    """

    def __init__(self, default=(0.0, 0.0, 0.0), **metadata):
        default = tuple(map(float, default))
        if len(default) != 3:
            raise ValueError("Expected tuple of length 3.")
        super().__init__(default, **metadata)

    # Override the validate() method to also accept NumPy arrays.
    # Some OVITO functions return Vector3 values as NumPy arrays, not tuples.
    def validate(self, object, name, value):
        value = tuple(map(float, value))
        return super().validate(object, name, value)


class Matrix3(traits.api.TraitType):
    """
    A `trait type <https://docs.enthought.com/traits/traits_user_manual/intro.html>`__ that stores a 3x3 matrix represented as a tuple of tuples of floats.
    Each inner tuple represents a row of the matrix. Thus, the element in the i-th row and the j-th column of the matrix can be accessed as ``matrix[i][j]``.

    See :ref:`writing_custom_modifiers.advanced_interface.user_params` for more information.

    :param default: The initial matrix to be assigned to the parameter trait. Must be convertible to a tuple of tuples of floats.
    :param metadata: Additional keyword arguments are forwarded to the base trait constructor.

    .. versionadded:: 3.11.2
    """

    def __init__(
        self, default=((0.0, 0.0, 0.0), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)), **metadata
    ):
        value = self.validate(None, "default", default)
        super().__init__(value, **metadata)

    def validate(self, obj, name, value):
        if len(value) != 3:
            raise ValueError(f"Expected an outer dimension of size 3, not {len(value)}.")
        for row in value:
            if len(row) != 3:
                raise ValueError(f"Expected an inner dimension of size 3, not {len(row)}.")
            for item in row:
                if not isinstance(item, numbers.Number):
                    raise ValueError(f"{item} is not a valid numeric matrix element.")
        return tuple(tuple(map(float, row)) for row in value)


class DataObjectReference(traits.api.Instance):
    """
    This `trait type <https://docs.enthought.com/traits/traits_user_manual/intro.html>`__ holds a :py:class:`DataObject.Ref <ovito.data.DataObject.Ref>` reference
    to a data object in a :py:class:`~ovito.data.DataCollection`.
    The stored reference tells where to find the selected object in the pipeline output but it does not hold the actual object.
    The user can select the data object from a list of available objects in the OVITO graphical user interface.
    To retrieve the actual object from a data collection, use the :py:meth:`DataCollection.get <ovito.data.DataCollection.get>` method.

    :param object_type: A :py:class:`~ovito.data.DataObject`-derived class type.
    :param filter: Optional callback function that can be used to additionally filter the list of data objects shown to the user in the GUI.
    :param default_value: Optional :py:class:`DataObject.Ref <ovito.data.DataObject.Ref>` instance to be used as the initial value of the trait.
    :param metadata: Additional keyword arguments are forwarded to the base trait constructor.

    Usage example: a :ref:`custom modifier <writing_custom_modifiers>` that lets the user select a :py:class:`~ovito.data.DataTable` object from the pipeline:

    .. literalinclude:: ../example_snippets/data_object_reference_trait.py
      :lines: 6-18

    This is how you would insert the custom modifier into the pipeline and configure it to print a specific data table:

    .. literalinclude:: ../example_snippets/data_object_reference_trait.py
      :lines: 26-26

    .. versionadded:: 3.11.0
    """

    def __init__(
        self,
        object_type: type[ovito.data.DataObject],
        filter: Optional[
            collections.abc.Callable[[ovito.data.DataObject], bool]
        ] = None,
        default_value: Optional[ovito.data.DataObject.Ref] = None,
        **metadata,
    ):
        if not issubclass(object_type, ovito.data.DataObject):
            raise ValueError("Expected a subclass of ovito.data.DataObject")
        if default_value:
            if not isinstance(default_value, ovito.data.DataObject.Ref):
                raise ValueError("Expected a DataObject.Ref instance as default value")
            metadata["factory"] = lambda: default_value
        super().__init__(
            klass=ovito.data.DataObject.Ref,
            args=(),
            allow_none=False,
            ovito_data_class=object_type,
            ovito_data_filter=filter,
            **metadata,
        )


class PropertyReference(traits.api.Str):
    """
    A `trait type <https://docs.enthought.com/traits/traits_user_manual/intro.html>`__ that manages a reference
    to a :py:class:`~ovito.data.Property`. The reference is encoded as a string containing the name of the property -
    optionally followed by a dot and the name of a vector component of the property.

    See :ref:`writing_custom_modifiers.advanced_interface.user_params` for more information.

    :param container:   1. :py:class:`~ovito.data.DataObject.Ref` specifying a :py:class:`~ovito.data.PropertyContainer` object
                           from which the user can select a property or
                        2. name of a :py:class:`DataObjectReference` trait defined in the same class,
                           which allows the user to select a property container.
    :param default_value: Initial property name to be assigned to the parameter trait.
    :param mode: Controls whether the trait should list entire properties, individual components of properties, or both.
    :param filter: Optional callback function that can be used to filter the list of properties shown to the user.
    :param metadata: Additional keyword arguments are forwarded to the base trait constructor.

    **Usage example**:

    .. literalinclude:: ../example_snippets/property_reference_trait.py
      :lines: 6-37

    .. versionadded:: 3.11.0
    """

    class Mode(Enum):
        """
        Enumeration of possible component listing modes for vector properties.
        """

        #: List entire properties (not their vector components).
        Properties = "properties"
        #: List individual components of vector properties.
        Components = "components"
        #: List entire properties AND their vector components.
        PropertiesAndComponents = "properties_and_components"

    def __init__(
        self,
        *,
        container: Union[str, ovito.data.DataObject.Ref] = ovito.data.DataObject.Ref(
            ovito.data.Particles
        ),
        default_value: str = "",
        mode: Mode = Mode.Components,
        filter: Optional[
            collections.abc.Callable[
                [ovito.data.PropertyContainer, ovito.data.Property], bool
            ]
        ] = None,
        **metadata,
    ):
        if isinstance(container, ovito.data.DataObject.Ref):
            metadata["ovito_property_container_ref"] = container
        elif isinstance(container, str):
            metadata["ovito_property_container_trait"] = container
        else:
            raise ValueError("Expected a trait name (string) or a DataObject.Ref")
        if not isinstance(mode, PropertyReference.Mode):
            raise ValueError("Expected a PropertyReference.Mode enum value")
        super().__init__(
            default_value=default_value,
            ovito_list_mode=mode,
            ovito_property_filter=filter,
            **metadata,
        )


# For backward compatibility with OVITO 3.9.2:
OvitoObjectTrait = OvitoObject
ColorTrait = Color
