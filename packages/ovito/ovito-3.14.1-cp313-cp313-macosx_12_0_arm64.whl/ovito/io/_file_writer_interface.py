from __future__ import annotations
import ovito.io
import ovito
from ..data import DataObject
from ..pipeline import Pipeline
import abc
import os
import traits.api
from typing import Any, Optional, Sequence, Type, Union

class FileWriterInterface(traits.api.HasTraits):
    """
    Base: :py:class:`traits.has_traits.HasTraits`

    Abstract base class for :ref:`Python-based file writers <writing_custom_file_writers>`. To implement a custom file writer for OVITO,
    derive from this class and implement the :py:meth:`write` method. Furthermore, the class provides a number of methods that can be overridden
    to specify the behavior of the file writer.

    **Code example:**

    .. literalinclude:: ../example_snippets/file_writer_interface_implementation.py
       :lines: 1-20

    Then perform the trajectory export by calling the :py:func:`export_file` function as follows:

    .. literalinclude:: ../example_snippets/file_writer_interface_implementation.py
       :lines: 30-30

    .. versionadded:: 3.12.0
    """

    @abc.abstractmethod
    def write(self, *, filename: str, frames: Sequence[int], frame: Optional[int], pipeline: Optional[Pipeline] = None, object_ref: DataObject.Ref = DataObject.Ref(), **kwargs: Any):
        """
        Main work function, which is called by OVITO to have the file writer produce an output file. The method must be implemented by the derived class.

        If the file writer supports exporting trajectories, as indicated by the :py:meth:`supports_trajectories` method,
        then the :py:meth:`write` method is invoked only once to export a sequence of animation frames to a single file.
        The method should then iterate over all frames specified by the *frames* parameter and write them to the destination file.

        If the user selected to export only a single frame, or if the user selected to export the trajectory to a sequence of
        separate files, then the method is invoked once per frame, each time with a different destination *filename*.

        All parameters are keyword-only arguments. Parameters the function is not interested in may go into the *kwargs* dictionary.

        :param filename: The local filesystem path the data should be written to.
                         The file writer should create a new file or overwrite an existing file at this location.
        :param frames: A sequence of 0-based frame numbers that should be written to the file.
                       The sequence may contain a single frame index, if the file writer is invoked to write a single static frame.
        :param frame: The 0-based index of the frame to write to the file. This parameter is only set when the file writer is invoked to write a single frame.
        :param pipeline: The pipeline object that produces the data to be written to the file.
                         The file writer should obtain the data using a call to :py:meth:`Pipeline.compute <ovito.pipeline.Pipeline.compute>`.
        :param object_ref: A reference to the data object in the pipeline's :py:class:`~ovito.data.DataCollection` the file writer should export.
                           The file writer may obtain the specified data object by calling :py:meth:`DataCollection.get <ovito.data.DataCollection.get>`.
        :param kwargs: Any further arguments that may be passed in by the system. This parameter should always be part of the function signature for forward compatibility with future versions of OVITO,
                       which may provide additional keyword arguments.
        """
        raise NotImplementedError("Abstract method write() must be implemented by the FileWriterInterface derived class.")

    # Define the optional methods only when generating the Sphinx documentation for the OVITO module.
    if os.environ.get('OVITO_SPHINX_BUILD', False):

        def supports_trajectories(self) -> bool:
            """
            This method can be overridden by a derived class to indicate whether the file writer supports exporting entire trajectories to a single file::

                def supports_trajectories(self):
                    return True

            If the method returns ``True``, the file writer may be invoked by OVITO to export a sequence of animation frames to a single output file in one go.
            If not implemented or if the method returns ``False``, the system assumes that the writer can only export single configurations (one frame per file).
            """
            return False

        def exportable_type(self) -> Union[Type[Pipeline], Type[DataObject]]:
            """
            This method can be overridden by a derived class to indicate the type of data that the file writer is able to export.

            The method should return a :py:class:`~ovito.data.DataObject`-derived class if this file writer is designed to export a single data object, for example
            :py:class:`ovito.data.Particles` or :py:class:`ovito.data.DataTable`.
            This will give the user the option to select a data object of the right type from the pipeline's data collection in the OVITO Pro GUI
            or by passing the *key* argument to the :py:func:`export_file` function. The selected data object will be passed to the :py:meth:`write` method
            as the *object_ref* parameter.

            .. literalinclude:: ../example_snippets/file_writer_interface_implementation2.py
              :lines: 1-16

            .. literalinclude:: ../example_snippets/file_writer_interface_implementation2.py
              :lines: 29-30

            If the file writer doesn't want to give the user a choice regarding the exported data object, it should return the :py:class:`~ovito.pipeline.Pipeline` class
            to indicate that the :py:meth:`write` method is going to automatically pick one or more data objects from the pipeline's output
            :py:class:`~ovito.data.DataCollection` to export. This is the default behavior::

                def exportable_type(self):
                    return ovito.pipeline.Pipeline
            """
            return Pipeline

ovito.io.FileWriterInterface = FileWriterInterface
