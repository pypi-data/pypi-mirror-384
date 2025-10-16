from __future__ import annotations
from typing import Union
from ovito.pipeline import Pipeline
from ovito.vis import Viewport
import ovito
import ovito.nonpublic

# Implementation of the ovito.gui.create_window() function:
def create_window(contents: Union[Pipeline, Viewport, None] = None):
    """
    Opens a new OVITO main window, including all GUI elements such as the interactive pipeline editor.

    This function is meant to be used in Jupyter notebooks to launch an OVITO session with a full graphical user interface.
    Changes you make to the scene, pipeline(s), or viewport(s) are synchronized between the Jupyter notebook and the GUI in both directions.

    :param contents: The :py:class:`~ovito.pipeline.Pipeline` or :py:class:`~ovito.vis.Viewport` to be displayed in the OVITO main window.
                     If none is provided, the current :py:data:`ovito.scene`, including all added pipelines, will be displayed.
    :return: `PySide6.QtWidgets.QWidget <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QWidget.html>`__

    .. important::

        This function is only available in the :ref:`OVITO Pro Jupyter kernel <ovito_jupyter_kernel>` and the Python interpreter embedded in OVITO Pro.
        It is not available in the standalone OVITO Python package from PyPI, because this version lacks support for a full graphical user interface.
        Calling this function in such an environment will raise a :py:exc:`RuntimeError`.
    """
    from ovito.qt_compat import shiboken, QtWidgets

    # Check if the function is available in this version of the Python package.
    if not hasattr(ovito.nonpublic, "create_main_window") or not ovito.gui_mode:
        raise RuntimeError("This function is not available in this version of the OVITO Python module. "
                            "You are currently using a headless version of the ovito package that does not contain support for a full graphical user interface. "
                            "Please use the OVITO Pro Jupyter kernel (available as part of the OVITO Pro conda package) or the embedded Python interpreter of OVITO Pro to access the GUI feature.")

    zoom_all_viewport_config = None

    # Determine what to display in the new window.
    if contents is None:
        # Use the current dataset including all pipelines in the current scene.
        dataset = ovito.dataset
    elif isinstance(contents, Pipeline):
        # Create a new dataset containing just the given pipeline.
        dataset = ovito.Scene()
        dataset.pipelines.append(contents)
        dataset.selected_pipeline = contents
        zoom_all_viewport_config = dataset.viewport_config
    elif isinstance(contents, Viewport):
        # Create a new dataset with a new viewport configuration.
        layout_cell = ovito.nonpublic.ViewportLayoutCell(viewport=contents)
        viewport_config = ovito.nonpublic.ViewportConfiguration(layout_root_cell=layout_cell)
        viewport_config.active_vp = contents
        dataset = ovito.Scene(viewport_config=viewport_config)
    else:
        raise ValueError("Invalid contents argument. Expected a Pipeline, Viewport, or None.")

    # Initialize main event loop, which is needed for displaying a graphical user interface with the Qt framework.
    ovito.init_qt_app(support_gui=True)

    # Create a new OVITO Pro main window.
    widget_ptr = ovito.nonpublic.create_main_window(dataset)

    # Zoom all viewports in the new window to fully show pipeline.
    if zoom_all_viewport_config:
        zoom_all_viewport_config.zoom_all_when_ready()

    # Return a QWidget to the caller.
    return shiboken.wrapInstance(widget_ptr, QtWidgets.QWidget)

# Inject function into public module:
ovito.gui.create_window = create_window