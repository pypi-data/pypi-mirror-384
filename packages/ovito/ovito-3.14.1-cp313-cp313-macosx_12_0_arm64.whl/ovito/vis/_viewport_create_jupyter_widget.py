from __future__ import annotations
from ovito.vis import Viewport

# For backward compatibility with OVITO 3.11.6:
# Implementation of the Viewport.create_jupyter_widget() method:
def _Viewport_create_jupyter_widget(self, antialiasing = True, picking = False, vr_scale = 0.0, layout=None, **kwargs):
    """
    .. deprecated:: 3.12.0
       Use :py:func:`ovito.gui.create_ipywidget` instead.
    """
    import ovito.gui
    return ovito.gui.create_ipywidget(self, antialiasing=antialiasing, picking=picking, vr_scale=vr_scale, layout=layout, **kwargs)
Viewport.create_jupyter_widget = _Viewport_create_jupyter_widget
