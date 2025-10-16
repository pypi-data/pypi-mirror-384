"""
.. versionadded:: 3.12.0

This module defines functions for real-time interactive rendering using a graphical user interface (GUI):

    * :py:func:`create_qwidget` - Create an Qt widget that displays the contents of a virtual :py:class:`~ovito.vis.Viewport`
    * :py:func:`create_ipywidget` - Create an interactive viewport widget for embedding in Jupyter notebooks
    * :py:func:`create_window` - Create an *OVITO Pro* window with the full graphical user interface

Furthermore, the module defines the :py:class:`UtilityInterface` abstract base class, which lets you
implement custom utility applets for the command panel of OVITO Pro.
"""
from __future__ import annotations

__all__ = ['create_window', 'create_qwidget', 'UtilityInterface']
