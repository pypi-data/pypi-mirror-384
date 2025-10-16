"""This module defines functions for real-time interactive rendering using a graphical user interface (GUI):

    * :py:func:`create_qwidget` - Create an Qt widget that displays the contents of a virtual :py:class:`Viewport`
    * :py:func:`create_ipywidget` - Create an interactive viewport widget for embedding in Jupyter notebooks
    * :py:func:`create_window` - Create an *OVITO Pro* window with the full graphical user interface

Furthermore, the module defines the :py:class:`UtilityInterface` abstract base class, which lets you
implement custom utility applets for the command panel of OVITO Pro."""
__all__ = ['create_window', 'create_qwidget', 'UtilityInterface', 'create_ipywidget']
from __future__ import annotations
from typing import Union, Optional
import PySide6.QtWidgets
import ipywidgets
from dataclasses import dataclass
from ovito.pipeline import Pipeline
from ovito.vis import Viewport

class UtilityInterface:
    """Base: :py:class:`traits.has_traits.HasTraits`

Base class for utility applets running in the command panel of OVITO Pro.
See :ref:`writing_custom_utilities`."""
    pass

@dataclass(kw_only=True)
class JupyterViewportWidget(ipywidgets.DOMWidget):
    antialiasing: bool = True
    picking: bool = False
    vr_scale: float = 0.0

    def refresh(self) -> None:
        ...

def create_qwidget(contents: Union[Pipeline, Viewport, None]=None, parent: Optional[PySide6.QtWidgets.QWidget]=None, *, show_orientation_indicator: bool=True, show_title: bool=False) -> PySide6.QtWidgets.QWidget:
    """Creates an interactive visual widget that displays the three-dimensional scene as seen through a virtual :py:class:`Viewport`.
The method creates an interactive window accepting mouse inputs from the user similar to the viewport windows
of the OVITO desktop application. You can use this method to develop custom user interfaces based on the `Qt cross-platform framework <https://www.qt.io/qt-for-python>`__
that integrate OVITO's functionality and display the output of a data pipeline.

:param contents: The :py:class:`Pipeline` or :py:class:`Viewport` object to be displayed by the widget.
:param parent: An optional Qt widget to be set as parent for the new viewport widget.
:param show_orientation_indicator: Controls the visibility of the coordinate axes in the lower left corner of the viewport widget.
:param show_title: Controls the visibility of viewport title in the upper left corner of the viewport widget.
:return: `PySide6.QtWidgets.QWidget <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QWidget.html>`__

The Qt widget returned by this method is linked to the :py:class:`Viewport` instance if provided.
Any changes your Python script subsequently makes to the non-visual :py:class:`Viewport` object,
for example setting its :py:attr:`camera_pos` or :py:attr:`camera_dir`, will automatically be reflected by the
visual widget. Vice versa will user interactions with the viewport widget
automatically lead to changes of the associated :py:class:`Viewport` object.

If you provide a :py:class:`Pipeline` object as the *contents* argument, the method will create an
ad-hoc viewport showing the output of just the given pipeline. If you provide no *contents* argument, the method
will create an ad-hoc viewport showing the contents of the global :py:data:`ovito.scene`, including all pipelines that have been added.

OVITO automatically creates a global QApplication object if necessary, which can be accessed via the :py:meth:`!QApplication.instance()` static method.

The following code example demonstrates the use of the :py:meth:`create_qwidget` function in a standalone Python program. Please see the
`Qt for Python <https://doc.qt.io/qtforpython-6/>`__ documentation for more information on how to create graphical
user interfaces using the Qt framework.

```python
  from ovito.io import import_file
  from ovito.vis import Viewport
  from ovito.gui import create_qwidget
  from PySide6.QtWidgets import QApplication
  
  # Import a particle model and add it to the global visualization scene.
  pipeline = import_file('input/simulation.dump')
  pipeline.add_to_scene()
  
  # Create a virtual viewport.
  vp = Viewport(type=Viewport.Type.Perspective, camera_dir=(2, 1, -1))
  
  # Create a GUI widget associated with the viewport.
  widget = create_qwidget(vp)
  widget.resize(500, 400)
  widget.setWindowTitle('OVITO Viewport Demo')
  widget.show()
  widget.raise_()
  vp.zoom_all((widget.width(), widget.height()))
  
  # Start the Qt event loop by invoking the QApplication.exec() method.
  sys.exit(QApplication.instance().exec())
```"""
    ...

def create_window(contents: Union[Pipeline, Viewport, None]=None) -> PySide6.QtWidgets.QWidget:
    """Opens a new OVITO main window, including all GUI elements such as the interactive pipeline editor.

This function is meant to be used in Jupyter notebooks to launch an OVITO session with a full graphical user interface.
Changes you make to the scene, pipeline(s), or viewport(s) are synchronized between the Jupyter notebook and the GUI in both directions.

:param contents: The :py:class:`Pipeline` or :py:class:`Viewport` to be displayed in the OVITO main window.
                 If none is provided, the current :py:data:`ovito.scene`, including all added pipelines, will be displayed.
:return: `PySide6.QtWidgets.QWidget <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QWidget.html>`__

.. important::

    This function is only available in the OVITO Pro Jupyter kernel and the Python interpreter embedded in OVITO Pro.
    It is not available in the standalone OVITO Python package from PyPI, because this version lacks support for a full graphical user interface.
    Calling this function in such an environment will raise a :py:exc:`RuntimeError`."""
    ...

def create_ipywidget(contents: Union[Pipeline, Viewport, None]=None, *, antialiasing: bool=True, picking: bool=False, vr_scale: float=0.0, layout=None, **kwargs) -> JupyterViewportWidget:
    """Creates an interactive widget for embedding in a Jupyter notebook, which displays the 3d scene as seen through a virtual :py:class:`Viewport`.
The method returns an interactive notebook element, which accepts mouse inputs similar to the viewport windows
of the OVITO desktop application. It may be necessary to call :func:`display <ipython:IPython.display.display>` in order to show the widget:

.. code-block::

    vp = Viewport(type=Viewport.Type.Perspective, camera_dir=(0.5, 1.0, -0.4))
    vp.zoom_all()
    widget = ovito.gui.create_ipywidget(vp)
    display(widget)

The `Jupyter widget <https://ipywidgets.readthedocs.io/en/stable/>`__ returned by this method is permanently linked to the :py:class:`Viewport` instance.
Any changes you subsequently make to the non-visual :py:class:`Viewport`, for example, setting its :py:attr:`camera_pos` or :py:attr:`camera_dir`, will be
reflected by the visual viewport widget. Vice versa do all user interactions with the viewport widget
update the corresponding fields of the :py:class:`Viewport` object.

.. important::

    This method requires the `ipywidgets <https://ipywidgets.readthedocs.io/en/stable/user_install.html>`__ Python package.
    Please install this package in your Jupyter environment.

:param contents: The :py:class:`Pipeline` or :py:class:`Viewport` object to be displayed by the widget.
:param antialiasing: Enables anti-aliasing to reduce jagged edges, which appear during WebGL rasterization.
:param picking: Enables object picking. When hovering the mouse cursor over an object, the widget will display the object's properties as text.
:param vr_scale: Enables VR support (WebXR browser interface) if set to a positive value. The parameter value specifies the ratio of 1 length unit
                 of the simulation model and 1 meter in VR space. It thus controls the apparent size (scaling) of the model in virtual reality mode.
                 For example, if object dimensions are specified in terms of nanometers in the simulation model, then a *vr_scale* value of 0.2 would let
                 a 1 nanometer sphere appear 20 centimeters large in virtual reality space.
:param layout: The `layout attribute <https://ipywidgets.readthedocs.io/en/latest/examples/Widget%20Layout.html>`__ for the new Jupyter widget.
:return: `ipywidgets.DOMWidget <https://ipywidgets.readthedocs.io/en/stable/>`__

If you provide a :py:class:`Pipeline` object as the *contents* argument, the method will create an
ad-hoc viewport showing the output of just that pipeline. If you provide no *contents* argument at all,
an ad-hoc viewport is created showing the contents of the global :py:data:`ovito.scene`, including all pipelines that have been added.

The ``layout`` attribute lets you control the `size of the widget <https://ipywidgets.readthedocs.io/en/stable/examples/Widget%20Layout.html>`__, e.g.:

.. code-block::

    from ipywidgets import Layout
    widget = create_ipywidget(vp, layout=Layout(width='100%', height='400px'))

.. caution::

    This method is still under active development and not fully functional yet. Expect these (known) limitations:

        * Semi-transparent objects will likely be rendered incorrectly.
        * Viewport layers are not supported yet.

    Please support the development of this new feature and report any issues you may encounter in our `issue tracker <https://gitlab.com/stuko/ovito/-/issues>`__
    or in the `OVITO support forum <https://matsci.org/c/ovito/>`__."""
    ...