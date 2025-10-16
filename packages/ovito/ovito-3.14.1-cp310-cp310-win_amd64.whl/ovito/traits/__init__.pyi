"""This module contains various `trait types <https://docs.enthought.com/traits/traits_user_manual/intro.html>`__, which
can be used in the context of custom modifiers, custom viewport overlays, and
other Python-based extensions for OVITO. Traits encapsulate object parameters,
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
- :py:class:`DataObjectReference`: A trait type that holds a reference to a certain :py:class:`DataObject` in a :py:class:`DataCollection` object hierarchy.
- :py:class:`PropertyReference`: A trait type that holds a reference to a :py:class:`Property`."""
__all__ = ['action_handler', 'Color', 'ColorTrait', 'DataObjectReference', 'FilePath', 'Matrix3', 'OvitoObject', 'OvitoObjectTrait', 'PropertyReference', 'Vector2', 'Vector3']
from __future__ import annotations
from typing import Tuple, Type, Any, Union, Optional, Callable
import traits.api
import ovito.pipeline
import ovito.data
import ovito.vis
from enum import Enum

def action_handler(button_trait_name: str) -> Callable:
    """A decorator for handler methods that handle button events in the GUI. See :ref:`writing_custom_modifiers.advanced_interface.user_params`
for more information on GUI traits.

Use this decorator to mark a method of your class as an event handler for a :py:class:`traits.trait_types.Button` trait.
The handler method will be called when the user clicks the button in the OVITO graphical user interface.

:param button_trait_name: The name of the button trait that the handler method should respond to.

Usage example:

```python
  from ovito.gui import UtilityInterface
  from ovito.traits import action_handler
  from traits.api import Button
  
  class MyUtilityApplet(UtilityInterface):
      hello_btn = Button(ovito_label="Click me")
  
      @action_handler("hello_btn")
      def say_hello(self):
          print("Hello world!")
```

The OVITO GUI does not support the *label* argument of the :py:class:`~traits.trait_types.Button` trait constructor.
    Please use the *ovito_label* metadata key instead to specify the button's label in the GUI: ``Button(ovito_label="Click me")``.

If your handler is performing a long-running operation, it should be written as a Python generator function that yields
status strings or progress values to the GUI. The GUI will display these messages in a progress dialog window
while the handler is running. The ``yield`` statement also gives the GUI a chance to handle user input events
and keep the application responsive. It allows the user to cancel the long-running task.

```python
  @action_handler("process_btn")
  def process_trajectory(self):
      num_frames = 1000
      yield f"Processing trajectory of {num_frames} frames..."
      for frame in range(num_frames):
          yield frame / num_frames # Report progress as a fraction
          do_some_work(frame)
```

Any exceptions raised by the handler method will be caught by the GUI and displayed to the user in a message box."""
    ...

class OvitoObject(traits.api.Instance):
    """A `trait type <https://docs.enthought.com/traits/traits_user_manual/intro.html>`__ that stores an instance of a class from the :py:mod:`ovito` package,
e.g. a visual element, modifier, or data object. The object instance is treated as an sub-object of the class defining the trait,
and the sub-object's parameters are displayed in the OVITO graphical user interface such that the user can adjust its settings.
See :ref:`writing_custom_modifiers.advanced_interface.user_params` for more information.

:param klass: The object class type to instantiate.
:param params: All other keyword parameters are forwarded to the constructor of the object class.

Usage example:

```python
  from ovito.data import DataCollection
  from ovito.pipeline import ModifierInterface
  from ovito.traits import OvitoObject
  from ovito.vis import BondsVis
  
  class MyCreateBondsModifier(ModifierInterface):
  
      # This trait field stores a pre-configured BondsVis visual element to be used
      # for the bonds newly created by this custom modifier.
      # The BondsVis visual element is not enabled by default, so the bonds will not
      # be displayed in the viewport unless the user explicitly enables it.
      # The width of the bonds is set to 0.1, but this can be adjusted as needed.
      bonds_vis = OvitoObject(BondsVis, enabled=False, width=0.1)
  
      def modify(self, data: DataCollection, *, frame: int, **kwargs):
          bonds = data.particles_.create_bonds(count=3, vis=self.bonds_vis)
          pairs = [(0, 1), (1, 2), (2, 0)] # Pairs of particle indices to connect by bonds
          bonds.create_property('Topology', data=pairs)
```"""

    def __init__(self, klass: Type[Union[ovito.vis.DataVis, ovito.pipeline.Modifier, ovito.pipeline.FileSource, ovito.pipeline.StaticSource, ovito.data.DataObject]], **params: Any) -> None:
        """TraitType initializer

This is the only method normally called directly by client code.
It defines the trait. The default implementation accepts an optional,
unvalidated default value, and caller-supplied trait metadata.

Override this method whenever a different method signature or a
validated default value is needed."""
        ...

class Color(traits.api.BaseTuple):
    """A `trait type <https://docs.enthought.com/traits/traits_user_manual/intro.html>`__ that stores a tuple of three floats representing the RGB components of a color parameter.
The three components must be in the range 0.0 - 1.0.

See :ref:`writing_custom_modifiers.advanced_interface.user_params` for more information.

:param default: The initial RGB values to be assigned to the parameter trait.
:param metadata: Additional keyword arguments are forwarded to the base trait constructor."""

    def __init__(self, default: Tuple[float, float, float]=(1.0, 1.0, 1.0), **metadata: Any) -> None:
        """TraitType initializer

This is the only method normally called directly by client code.
It defines the trait. The default implementation accepts an optional,
unvalidated default value, and caller-supplied trait metadata.

Override this method whenever a different method signature or a
validated default value is needed."""
        ...

class FilePath(traits.api.BaseFile):
    """A `trait type <https://docs.enthought.com/traits/traits_user_manual/intro.html>`__ that stores a filesystem path.
In the GUI, a file selection dialog is displayed for the user to pick the trait value.

See :ref:`writing_custom_modifiers.advanced_interface.user_params` for more information.

:param default: Initial parameter trait value.
:param metadata: Additional keyword arguments are forwarded to the base trait constructor."""

    def __init__(self, default: str='', **metadata: Any) -> None:
        """TraitType initializer

This is the only method normally called directly by client code.
It defines the trait. The default implementation accepts an optional,
unvalidated default value, and caller-supplied trait metadata.

Override this method whenever a different method signature or a
validated default value is needed."""
        ...

class Vector2(traits.api.BaseTuple):
    """A `trait type <https://docs.enthought.com/traits/traits_user_manual/intro.html>`__ that stores a tuple of two floats, which represent a vector or point in 2d space.

See :ref:`writing_custom_modifiers.advanced_interface.user_params` for more information.

:param default: The initial vector value to be assigned to the parameter trait.
:param metadata: Additional keyword arguments are forwarded to the base trait constructor."""

    def __init__(self, default: Tuple[float, float]=(0.0, 0.0), **metadata: Any) -> None:
        """TraitType initializer

This is the only method normally called directly by client code.
It defines the trait. The default implementation accepts an optional,
unvalidated default value, and caller-supplied trait metadata.

Override this method whenever a different method signature or a
validated default value is needed."""
        ...

class Vector3(traits.api.BaseTuple):
    """A `trait type <https://docs.enthought.com/traits/traits_user_manual/intro.html>`__ that stores a tuple of three floats, which represent a vector or point in 3d space.

See :ref:`writing_custom_modifiers.advanced_interface.user_params` for more information.

:param default: The initial vector value to be assigned to the parameter trait.
:param metadata: Additional keyword arguments are forwarded to the base trait constructor."""

    def __init__(self, default: Tuple[float, float, float]=(0.0, 0.0, 0.0), **metadata: Any) -> None:
        """TraitType initializer

This is the only method normally called directly by client code.
It defines the trait. The default implementation accepts an optional,
unvalidated default value, and caller-supplied trait metadata.

Override this method whenever a different method signature or a
validated default value is needed."""
        ...

class DataObjectReference(traits.api.Instance):
    """This `trait type <https://docs.enthought.com/traits/traits_user_manual/intro.html>`__ holds a `DataObject.Ref` reference
to a data object in a :py:class:`DataCollection`.
The stored reference tells where to find the selected object in the pipeline output but it does not hold the actual object.
The user can select the data object from a list of available objects in the OVITO graphical user interface.
To retrieve the actual object from a data collection, use the `DataCollection.get` method.

:param object_type: A :py:class:`DataObject`-derived class type.
:param filter: Optional callback function that can be used to additionally filter the list of data objects shown to the user in the GUI.
:param default_value: Optional `DataObject.Ref` instance to be used as the initial value of the trait.
:param metadata: Additional keyword arguments are forwarded to the base trait constructor.

Usage example: a custom modifier that lets the user select a :py:class:`DataTable` object from the pipeline:

```python
  from ovito.data import DataTable, DataObject
  from ovito.pipeline import ModifierInterface
  from ovito.traits import DataObjectReference
  
  class PrintTableModifier(ModifierInterface):
  
      # Define a parameter trait that lets the user select a DataTable:
      input_table = DataObjectReference(DataTable, label="Input table")
  
      def modify(self, data, **kwargs):
          # Look up the selected DataTable in the input data collection:
          table = data.get(self.input_table)
          print(table)
```

This is how you would insert the custom modifier into the pipeline and configure it to print a specific data table:

```python
  pipeline.modifiers.append(PrintTableModifier(input_table=DataObject.Ref(DataTable, 'structures')))
```"""

    def __init__(self, object_type: Type[ovito.data.DataObject], filter: Optional[Callable[[ovito.data.DataObject], bool]]=None, default_value: Optional[ovito.data.DataObject.Ref]=None, **metadata: Any) -> None:
        """TraitType initializer

This is the only method normally called directly by client code.
It defines the trait. The default implementation accepts an optional,
unvalidated default value, and caller-supplied trait metadata.

Override this method whenever a different method signature or a
validated default value is needed."""
        ...

class PropertyReference(traits.api.Str):
    """A `trait type <https://docs.enthought.com/traits/traits_user_manual/intro.html>`__ that manages a reference
to a :py:class:`Property`. The reference is encoded as a string containing the name of the property -
optionally followed by a dot and the name of a vector component of the property.

See :ref:`writing_custom_modifiers.advanced_interface.user_params` for more information.

:param container:   1. :py:class:`Ref` specifying a :py:class:`PropertyContainer` object
                       from which the user can select a property or
                    2. name of a :py:class:`DataObjectReference` trait defined in the same class,
                       which allows the user to select a property container.
:param default_value: Initial property name to be assigned to the parameter trait.
:param mode: Controls whether the trait should list entire properties, individual components of properties, or both.
:param filter: Optional callback function that can be used to filter the list of properties shown to the user.
:param metadata: Additional keyword arguments are forwarded to the base trait constructor.

Usage example:

```python
  from ovito.data import DataObject, PropertyContainer, Particles
  from ovito.pipeline import ModifierInterface
  from ovito.traits import DataObjectReference, PropertyReference
  
  class PrintTypesModifier(ModifierInterface):
  
      # Define a parameter trait that lets the user select a PropertyContainer.
      # A filter function is provided to show only containers that contain at least one typed property.
      input_container = DataObjectReference(
          PropertyContainer,
          default_value=DataObject.Ref(Particles),
          filter=lambda container: any(prop.types for prop in container.values()),
          label="Container")
  
      # Define a parameter trait that lets the user select a property from the selected container.
      # A filter function is provided to show only properties that are typed.
      input_property = PropertyReference(
          container="input_container",   # That's the name of the trait defined above
          default_value="Particle Type",
          mode=PropertyReference.Mode.Properties,
          filter=lambda c, p: len(p.types) != 0,
          label="Property")
  
      # Modifier function implementation:
      def modify(self, data, **kwargs):
          if not self.input_container: return
          if not self.input_property: return
          container = data.get(self.input_container) # Look up the selected PropertyContainer
          prop = container[self.input_property]  # Look up the selected property
          # Print the list of types attached to the selected property:
          for t in prop.types:
              print(t.id, t.name)
```"""

    class Mode(Enum):
        """Enumeration of possible component listing modes for vector properties."""
        Properties = 'properties'
        Components = 'components'
        PropertiesAndComponents = 'properties_and_components'

    def __init__(self, *, container: Union[str, ovito.data.DataObject.Ref]=ovito.data.DataObject.Ref(ovito.data.Particles), default_value: str='', mode: Mode=Mode.Components, filter: Optional[Callable[[ovito.data.PropertyContainer, ovito.data.Property], bool]]=None, **metadata: Any) -> None:
        """TraitType initializer

This is the only method normally called directly by client code.
It defines the trait. The default implementation accepts an optional,
unvalidated default value, and caller-supplied trait metadata.

Override this method whenever a different method signature or a
validated default value is needed."""
        ...