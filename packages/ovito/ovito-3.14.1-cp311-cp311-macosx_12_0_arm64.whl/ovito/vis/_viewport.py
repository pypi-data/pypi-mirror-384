from __future__ import annotations
import ovito
from . import Viewport
from ..nonpublic import RenderSettings, FrameBuffer, OpenGLViewportWindow, SceneRenderer
from typing import Optional
import collections.abc

# Helper function that injects the _repr_png_ special method into PySide6's QImage class.
# The _repr_png_ method is called by Jupyter to display QImage objects as embedded PNG images.
# See https://ipython.readthedocs.io/en/latest/config/integrating.html#custom-methods
def _register_qimage_display_hook(qimage_cls):
    if not hasattr(qimage_cls, '_repr_png_'):
        from PySide6.QtCore import QByteArray, QBuffer, QIODevice
        def _convert_qimage_to_bytes(img):
            ba = QByteArray()
            buffer = QBuffer(ba)
            buffer.open(QIODevice.WriteOnly)
            img.save(buffer, "PNG")
            buffer.close()
            return ba.data()
        qimage_cls._repr_png_ = _convert_qimage_to_bytes
        assert hasattr(qimage_cls, '_repr_png_')

# Implementation of the Viewport.render_image() method:
def _Viewport_render_image(self,
                           size: tuple[int,int]=(640,480),
                           frame: int=0,
                           filename: Optional[str]=None,
                           background: tuple[float,float,float]=(1.0,1.0,1.0),
                           alpha: bool=False,
                           renderer=None,
                           crop: bool=False,
                           layout: Optional[collections.abc.Sequence[tuple[Viewport, tuple[float,float,float,float]]]]=None,
                           stop_on_error: bool=True):
    """ Renders an image of the viewport's view.

        :param size: A pair of integers specifying the horizontal and vertical dimensions of the output image in pixels.
        :param int frame: The animation frame to render. Numbering starts at 0. See the :py:attr:`Pipeline.num_frames <ovito.pipeline.Pipeline.num_frames>` property for the number of loaded animation frames.
        :param str filename: The file path under which the rendered image should be saved (optional).
                             Supported output formats are: :file:`.png`, :file:`.jpeg`, and :file:`.tiff`.
        :param background: A triplet of RGB components in the range [0,1] specifying the background color of the rendered image (unless *alpha* is set).
        :param alpha: This option makes the background transparent so that the rendered image may later be superimposed on a different backdrop.
                      When using this option, make sure to save the image in the PNG format in order to preserve the generated transparency information.
        :param renderer: The rendering engine to use. If set to ``None``, either OpenGL or Tachyon are used,
                         depending on the availability of OpenGL in the current execution context.
        :param crop: This option cuts away border areas of the rendered image filled with the background color; the resulting image may thus turn out smaller than the requested *size*.
        :param layout: Optional definition of a :ref:`multi-viewport layout <manual:viewport_layouts>` to be rendered into the output image. The layout must be provided as a list of :py:class:`Viewport` objects
                       and corresponding rectangular areas, which determine where each viewport's picture appears within the composed output image.
                       Please make use of OVITO Pro's :ref:`code generation <manual:python_code_generation>` function to learn how to construct the *layout* argument.
        :param stop_on_error: Controls whether the rendering process should be aborted by raising an exception in case an error occurs in any of the scene's data pipelines.
        :returns: A `QImage <https://doc.qt.io/qtforpython-6/PySide6/QtGui/QImage.html>`__ object containing the rendered picture.

        **Populating the scene**

        Before rendering an image using this method, you should make sure the three-dimensional contains some
        visible objects. Typically this involves calling the :py:meth:`Pipeline.add_to_scene() <ovito.pipeline.Pipeline.add_to_scene>`
        method on a pipeline to insert its output data into the scene::

           pipeline = import_file('simulation.dump')
           pipeline.add_to_scene()

        **Selecting the rendering backend**

        OVITO supports several different rendering backends for producing pictures of the three-dimensional scene:

            * :py:class:`OpenGLRenderer` (default)
            * :py:class:`TachyonRenderer`
            * :py:class:`OSPRayRenderer`
            * :py:class:`AnariRenderer`

        Each of these backends exhibits specific parameters that control the image quality and other aspect of the image
        generation process. Typically, you would create an instance of one of these renderer classes, configure it and pass
        it to the :py:meth:`!render_image()` method:

        .. literalinclude:: ../example_snippets/viewport_select_renderer.py
           :lines: 5-

        **Post-processing images**

        If the ``filename`` parameter is omitted, the method does not save the rendered image to disk.
        This gives you the opportunity to paint additional graphics on top before saving the
        `QImage <https://doc.qt.io/qtforpython/PySide6/QtGui/QImage.html>`__ later using its ``save()`` method:

        .. literalinclude:: ../example_snippets/render_to_image.py

        As an alternative to the direct method demonstrated above, you can also make use of a :py:class:`PythonViewportOverlay`
        to paint custom graphics on top of rendered images.
    """
    # Check arguments passed by caller:
    assert len(size) == 2 and size[0] > 0 and size[1] > 0
    assert len(background) == 3
    assert background[0] >= 0.0 and background[0] <= 1.0
    assert background[1] >= 0.0 and background[1] <= 1.0
    assert background[2] >= 0.0 and background[2] <= 1.0
    assert renderer is None or isinstance(renderer, SceneRenderer)

    # Configure an ad-hoc RenderSettings object:
    rs = RenderSettings()
    rs.output_image_width, rs.output_image_height = size
    rs.background_color = background
    rs.generate_alpha = alpha
    rs.stop_on_pipeline_error = stop_on_error
    if renderer is not None:
        rs.renderer = renderer
    rs.range = RenderSettings.Range.CustomFrame
    rs.custom_frame = int(frame)

    # Create an ad-hoc standard viewport layout if caller didn't provide one.
    if layout is None:
        layout = [(self, (0.0, 0.0, 1.0, 1.0))]

    # Make sure the Viewport is associated with a scene.
    if self.scene is None:
        raise RuntimeError("Cannot render viewport which has no scene set.")

    # Prevent common mistake made by users.
    if len(self.scene.children) == 0:
        print("Warning: The scene to be rendered is empty. Did you forget to add a pipeline to the scene using Pipeline.add_to_scene()?")

    # Invoke the actual image rendering function. It returns a framebuffer object.
    fb = rs.render_scene(self.scene.anim, layout)

    # Crop away background pixels along the outer edges of the image if requested.
    if crop:
        fb.auto_crop()

    # Extract the QImage, which is the backing store of the framebuffer.
    img = fb.image

    # Adds the _repr_png_() special method to PySide6's QImage class such that
    # Jupyter can display the returned QImage object as embedded PNG image in a notebook.
    _register_qimage_display_hook(type(img))

    # Save image to the output file if requested by caller.
    if filename:
        ovito.init_qt_app(False) # The QImage.save() function requires a Qt application object.
        if not img.save(filename):
            raise RuntimeError(f"Failed to save rendered image to output file '{filename}'")

    # Return the QImage to the caller.
    return img
Viewport.render_image = _Viewport_render_image

# Implementation of the Viewport.render_anim() method:
def _Viewport_render_anim(self,
                          filename: str,
                          size: tuple[int, int]=(640,480),
                          fps: int=10,
                          background: tuple[float, float, float]=(1.0,1.0,1.0),
                          renderer=None,
                          range: Optional[tuple[int,int]]=None,
                          every_nth: int=1,
                          layout: Optional[collections.abc.Sequence[tuple[Viewport, tuple[float,float,float,float]]]]=None,
                          stop_on_error: bool=True):
    """ Renders an animation sequence.

        :param filename: The filename under which the rendered animation should be saved.
                         Supported video formats are: :file:`.avi`, :file:`.mp4`, :file:`.mov` and :file:`.gif`.
                         Alternatively, an image format may be specified (:file:`.png`, :file:`.jpeg`, :file:`.tiff`).
                         In this case, a series of static image files will be produced, one for each frame, which
                         may be combined into a video using an external encoding tool of your choice. The "*" wildcard character
                         may be used in the filename to specify a frame number placeholder.
        :param size: The resolution of the movie in pixels.
        :param fps: The number of frames per second of the encoded movie. This determines the playback speed of the animation.
        :param background: An RGB triplet in the range [0,1] specifying the background color of the rendered movie.
        :param renderer: The rendering engine to use. If none is specified, either OpenGL or Tachyon are used,
                         depending on the availability of OpenGL in the script execution context.
        :param range: The interval of frames to render, specified in the form ``(from,to)``.
                      Frame numbering starts at 0. If no interval is specified, the entire animation is rendered, i.e.
                      frame 0 through (:py:attr:`Pipeline.num_frames <ovito.pipeline.Pipeline.num_frames>`-1).
        :param every_nth: Frame skipping interval in case you don't want to render every frame of a very long animation.
        :param layout: Optional definition of a :ref:`multi-viewport layout <manual:viewport_layouts>` to be rendered into the output image.
        :param stop_on_error: Controls whether the rendering process should be aborted by raising an exception in case an error occurs in any of the scene's data pipelines.

        See also the :py:meth:`.render_image` method for a more detailed discussion of some of these parameters.
    """
    # Check arguments passed by caller:
    assert len(size) == 2 and size[0] > 0 and size[1] > 0
    assert fps >= 1
    assert every_nth >= 1
    assert len(background) == 3
    assert background[0] >= 0.0 and background[0] <= 1.0
    assert background[1] >= 0.0 and background[1] <= 1.0
    assert background[2] >= 0.0 and background[2] <= 1.0
    assert renderer is None or isinstance(renderer, SceneRenderer)

    # Configure an ad-hoc RenderSettings object:
    rs = RenderSettings()
    rs.output_image_width, rs.output_image_height = size
    rs.background_color = background
    rs.output_filename = str(filename)
    rs.save_to_file = True
    rs.stop_on_pipeline_error = stop_on_error
    rs.frames_per_second = int(fps)
    if renderer:
        rs.renderer = renderer
    rs.every_nth_frame = int(every_nth)
    if range:
        rs.range = RenderSettings.Range.CustomInterval
        rs.custom_range_start, rs.custom_range_end = range
    else:
        rs.range = RenderSettings.Range.Animation

    # Create an ad-hoc standard viewport layout if caller didn't provide one.
    if layout is None:
        layout = [(self, (0.0, 0.0, 1.0, 1.0))]

    # Make sure the Viewport is associated with a scene.
    if self.scene is None:
        raise RuntimeError("Cannot render viewport which has no scene set.")

    # Prevent common mistake made by users.
    if len(self.scene.children) == 0:
        print("Warning: The scene to be rendered is empty. Did you forget to add a pipeline to the scene using Pipeline.add_to_scene()?")

    # Invoke the actual image rendering function. It returns a framebuffer object.
    rs.render_scene(self.scene.anim, layout)
Viewport.render_anim = _Viewport_render_anim

# Implementation of the Viewport.zoom_all() method:
def _Viewport_zoom_all(self, size: tuple[int,int]=(640,480)):
    """ Repositions the viewport camera such that all objects in the scene become completely visible.
        The current orientation (:py:attr:`camera_dir`) of the viewport's camera is maintained but
        the :py:attr:`camera_pos` and :py:attr:`fov` parameters are adjusted by this method.

        :param size: Size in pixels of the image that is going to be renderer from this viewport.
                     This information is used to compute the aspect ratio of the viewport rectangle into which
                     the visible objects should be fitted. The tuple should match the *size* argument you pass
                     to :py:meth:`render_image` later.

        Note that this method uses an axis-aligned bounding box computed at frame 0 of the
        loaded trajectory enclosing all visible objects to adjust the viewport camera.
        Make sure to call :py:meth:`Pipeline.add_to_scene() <ovito.pipeline.Pipeline.add_to_scene>` first
        to insert some visible object(s) into the scene.
    """
    assert len(size) == 2 and size[0] > 0 and size[1] > 0
    aspect_ratio = size[1] / size[0]
    self._zoom_to_scene_extents(aspect_ratio)
Viewport.zoom_all = _Viewport_zoom_all

# For backward compatibility with OVITO 3.11.6:
# Implementation of the Viewport.create_qt_widget() method:
def _Viewport_create_qt_widget(self, parent = None):
    """
    .. deprecated:: 3.12.0
       Use :py:func:`ovito.gui.create_qwidget` instead.
    """
    import ovito.gui
    return ovito.gui.create_qwidget(self, parent)
Viewport.create_qt_widget = _Viewport_create_qt_widget

# For backward compatibility with OVITO 3.5.4 (define alias for create_qt_widget() method):
Viewport.create_widget = lambda self, parent = None: self.create_qt_widget(parent)
