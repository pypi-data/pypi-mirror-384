from __future__ import annotations
from typing import Union
from ..pipeline import Pipeline
from ..vis import Viewport
import ovito
import ovito.nonpublic

# Implementation of the ovito.gui.create_qwidget() function:
def create_qwidget(contents: Union[Pipeline, Viewport, None] = None, parent: "PySide6.QtWidgets.QWidget | None" = None, *, show_orientation_indicator: bool = True, show_title: bool = False):
    """
    Creates an interactive visual widget that displays the three-dimensional scene as seen through a virtual :py:class:`~ovito.vis.Viewport`.
    The method creates an interactive window accepting mouse inputs from the user similar to the viewport windows
    of the OVITO desktop application. You can use this method to develop custom user interfaces based on the `Qt cross-platform framework <https://www.qt.io/qt-for-python>`__
    that integrate OVITO's functionality and display the output of a data pipeline.

    :param contents: The :py:class:`~ovito.pipeline.Pipeline` or :py:class:`~ovito.vis.Viewport` object to be displayed by the widget.
    :param parent: An optional Qt widget to be set as parent for the new viewport widget.
    :param show_orientation_indicator: Controls the visibility of the coordinate axes in the lower left corner of the viewport widget.
    :param show_title: Controls the visibility of viewport title in the upper left corner of the viewport widget.
    :return: `PySide6.QtWidgets.QWidget <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QWidget.html>`__

    The Qt widget returned by this method is linked to the :py:class:`~ovito.vis.Viewport` instance if provided.
    Any changes your Python script subsequently makes to the non-visual :py:class:`~ovito.vis.Viewport` object,
    for example setting its :py:attr:`~ovito.vis.Viewport.camera_pos` or :py:attr:`~ovito.vis.Viewport.camera_dir`, will automatically be reflected by the
    visual widget. Vice versa will user interactions with the viewport widget
    automatically lead to changes of the associated :py:class:`~ovito.vis.Viewport` object.

    If you provide a :py:class:`~ovito.pipeline.Pipeline` object as the *contents* argument, the method will create an
    ad-hoc viewport showing the output of just the given pipeline. If you provide no *contents* argument, the method
    will create an ad-hoc viewport showing the contents of the global :py:data:`ovito.scene`, including all pipelines that have been added.

    OVITO automatically creates a global QApplication object if necessary, which can be accessed via the :py:meth:`!QApplication.instance()` static method.

    The following code example demonstrates the use of the :py:meth:`!create_qwidget` function in a standalone Python program. Please see the
    `Qt for Python <https://doc.qt.io/qtforpython-6/>`__ documentation for more information on how to create graphical
    user interfaces using the Qt framework.

    .. literalinclude:: ../example_snippets/viewport_create_widget.py
        :lines: 17-

    .. seealso:: :ref:`example_trajectory_viewer`
    """
    from ovito.qt_compat import shiboken, QtWidgets

    # Determine what to display in the viewport window.
    if contents is None:
        # Create an ad-hoc viewport showing the global scene.
        viewport = Viewport()
    elif isinstance(contents, Pipeline):
        # Create a new scene containing just the given pipeline and an ad-hoc viewport.
        scene = ovito.nonpublic.Scene()
        scene.children.append(ovito.nonpublic.SceneNode(pipeline=contents))
        viewport = Viewport(scene=scene)
    elif isinstance(contents, Viewport):
        viewport = contents
    else:
        raise ValueError("Invalid contents argument. Expected a Pipeline, Viewport, or None.")

    # Get memory address of parent widget.
    if parent is None:
        parent_ptr = 0
    elif isinstance(parent, QtWidgets.QWidget):
        parent_ptr = shiboken.getCppPointer(parent)[0]
    else:
        raise ValueError("Invalid parent argument. Expected a QWidget instance or None.")

    # Initialize main event loop, which is needed for displaying a widget with the Qt framework.
    ovito.init_qt_app(support_gui=True)

    # Create viewport window widget.
    vpwin = ovito.nonpublic.OpenGLViewportWindow(viewport, parent_ptr)
    vpwin.show_title = show_title
    vpwin.show_orientation_indicator = show_orientation_indicator

    # Return a QWidget to the caller.
    return shiboken.wrapInstance(vpwin._widget, QtWidgets.QWidget)

# Inject function into public module:
ovito.gui.create_qwidget = create_qwidget
