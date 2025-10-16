from __future__ import annotations
from typing import Any, Union, Type
import os
import ovito
import ovito.io
from ..data import DataCollection, DataObject
from ..pipeline import Pipeline, StaticSource, PipelineNode
from ..nonpublic import AttributeFileExporter, PipelineStatus, PythonFileExporter, FileExporter
from . import FileWriterInterface

def export_file(data: Union[Pipeline, DataCollection, DataObject, None], file: Union[str, os.PathLike], format: Union[str, Type[ovito.io.FileWriterInterface]], **params: Any):
    """ Writes data to an output file. See section :ref:`file_output_overview` for an overview.

        :param data: The object to be exported. See available options below.
        :param file: The output file path.
        :param format: The kind of file to write. See available options below.
        :param params: Optional keyword arguments depending on the selected format.

        **Exportable objects**

        The following kinds of Python objects can be passed to this function:

        :py:class:`~ovito.pipeline.Pipeline`
            If you provide a data pipeline, the dynamically computed output of the pipeline gets exported. Since pipelines support evaluation at different animation times,
            a sequence of frames can be exported by passing the extra keyword argument ``multiple_frames=True``, see below.

        :py:class:`~ovito.data.DataCollection`
            If you provide a data collection, the static snapshot stored in the collection is exported.
            Note that it depends on the selected file format which objects from the data collection will be exported -
            or you may have to provide extra function arguments to specify which data object(s) to export.

        :py:class:`~ovito.data.DataObject`
            If you provide a single data object, e.g. a :py:class:`~ovito.data.DataTable` or :py:class:`~ovito.data.SurfaceMesh`,
            just that one object gets exported. The behavior is similar to providing a :py:class:`~ovito.data.DataCollection`
            containing a single data object.

        `None`
            This exports the entire visualization scene, i.e. the output of all data pipelines in the current scene (see :py:attr:`ovito.Scene.pipelines` list).
            This option is currently supported only by the :ref:`glTF <manual:file_formats.output.gltf>` and POV-Ray exporters, which generate a full scene description file.

        Additional keyword parameters, as documented below, let you control which aspects of a dataset will be written to the output file.
        For instance, for some file formats the ``columns`` keyword controls the set of particle properties to be exported.

        **Output filename**

        The parameter *file* specifies the path of the output file. If the filename ends with the suffix `.gz`,
        the output file will be compressed using the zlib library to save disk space (works only for text-based file formats).

        If a wildcard "*" character appears in the filename, then one file per animation frame is written and the "*" character is replaced
        with the frame number. This feature is typically used in conjunction with the ``multiple_frames=True`` option, see below.

        **Output formats**

        The parameter *format* may be one of the following strings selecting the kind of file to write (:ref:`list of supported file formats <manual:file_formats.output>`):

        ============================= ========================================================================
        Format string                 Description
        ============================= ========================================================================
        ``"txt/attr"``                Export global attributes to a text file (see below)
        ``"txt/table"``               Export tabular data of a py:class:`~ovito.data.DataTable` or other :py:class:`~ovito.data.PropertyContainer` to a text file
        ``"lammps/dump"``             LAMMPS text-based dump format
        ``"lammps/data"``             LAMMPS data format
        ``"imd"``                     IMD format
        ``"vasp"``                    POSCAR format
        ``"xyz"``                     XYZ format
        ``"fhi-aims"``                FHI-aims format
        ``"gsd/hoomd"``               GSD format used by the `HOOMD-blue simulation code <https://glotzerlab.engin.umich.edu/hoomd-blue/>`__
        ``"netcdf/amber"``            Binary format for MD data following the `AMBER format convention <https://ambermd.org/netcdf/nctraj.pdf>`__
        ``"vtk/trimesh"``             `ParaView VTK format <https://www.vtk.org/VTK/img/file-formats.pdf>`__ for exporting :py:class:`~ovito.data.SurfaceMesh` objects
        ``"vtk/disloc"``              `ParaView VTK format <https://www.vtk.org/VTK/img/file-formats.pdf>`__ for exporting :py:class:`~ovito.data.DislocationNetwork` objects
        ``"vtk/grid"``                `ParaView VTK format <https://www.vtk.org/VTK/img/file-formats.pdf>`__ for exporting :py:class:`~ovito.data.VoxelGrid` objects
        ``"ca"``                      :ref:`Text-based format for storing dislocation lines <manual:particles.modifiers.dislocation_analysis.fileformat>`
        ``"gltf"``                    `glTF <https://www.khronos.org/gltf/>`__ 3d scene format (`.glb` file extension) - See :ref:`manual:file_formats.output.gltf`
        ``"povray"``                  `POV-Ray <https://www.povray.org/>`__ scene format
        ``"ase/traj"``                `ASE trajectory file format <https://wiki.fysik.dtu.dk/ase/ase/io/trajectory.html>`__ - See :ref:`manual:file_formats.output.ase_trajectory`
        ============================= ========================================================================

        Alternatively, *format* may be a Python class derived from :py:class:`~ovito.io.FileWriterInterface` that implements a custom file writer.
        Depending on the selected output format, additional keyword arguments may be passed to :py:func:`!export_file` as documented in the following sections.

        **File columns**

        For output formats *lammps/dump*, *xyz*, *imd*, and *netcdf/amber* you must specify the list of particle properties to be exported
        by providing the ``columns`` keyword argument::

            export_file(pipeline, "output.xyz", "xyz", columns =
              ["Particle Identifier", "Particle Type", "Position.X", "Position.Y", "Position.Z"])

        When exporting a :ref:`vectorial property <particle-properties-list>`, you can specify a particular vector component by appending it as a suffix
        to the base name, e.g. ``"Position.Z"`` or ``"Atomic Strain.XY"`` (see :py:attr:`Property.component_names <ovito.data.Property.component_names>`).
        If you do not specify a component, all components of the vector property will be exported in the form of several consecutive data columns (since OVITO 3.8).

        .. tip::

            If you are not sure which particle properties are available for export, you can print the list of particle properties
            to the console as follows::

               print(pipeline.compute().particles)

        **Exporting several simulation frames**

        By default, only the current animation frame (frame 0 by default) is exported.
        To export a different trajectory frame, pass the ``frame`` keyword parameter to the :py:func:`!export_file` function.
        Alternatively, you can export all frames of the animation sequence at once by specifying ``multiple_frames=True``.
        More refined control is possible through the keyword arguments ``start_frame``, ``end_frame``, and ``every_nth_frame``.

        Some file formats such as *lammps/dump*, *xyz*, *gsd/hoomd* or *netcdf/amber* can store all frames of the exported trajectory
        in a single output file. For other formats, or if you prefer one file per frame, you must pass a filename pattern
        to :py:func:`!export_file`. The specified output filename must contain a ``*`` wildcard character as in the following example,
        which will be replaced with the animation frame number during export::

            export_file(pipeline, "output.*.dump", "lammps/dump", multiple_frames=True)

        This is equivalent to an explicit for-loop that exports the frames one by one to a series of files::

            for i in range(pipeline.num_frames):
                export_file(pipeline, f"output.{i}.dump", "lammps/dump", frame=i)

        **Floating-point number precision**

        For text-based file formats, you can specify the desired formatting precision for floating-point values using the
        ``precision`` keyword parameter. The default output precision is 10 digits; the maximum is 17.

        **LAMMPS atom style**

        When writing files in the *lammps/data* format, the LAMMPS atom style "atomic" is used by default. To generate
        a data file with a different `LAMMPS atom style <https://docs.lammps.org/atom_style.html>`__, specify it using the ``atom_style`` keyword parameter::

            export_file(pipeline, "output.data", "lammps/data", atom_style="bond")
            export_file(pipeline, "output.data", "lammps/data", atom_style="hybrid", atom_substyles=("template", "charge"))

        If at least one :py:class:`~ovito.data.ParticleType` of the exported model has a non-zero :py:attr:`~ovito.data.ParticleType.mass` value,
        OVITO writes a ``Masses`` section to the LAMMPS data file. You can suppress it by passing ``omit_masses=True`` to the export function.

        The option ``ignore_identifiers=True`` replaces any existing atom IDs (particle property `Particle Identifier`) with a new contiguous sequence of numeric IDs during export.
        The option ``consecutive_type_ids=True`` replaces existing numeric type IDs of particle/bond/angle/dihedral/improper types with new values during export.
        The option ``export_type_names=True`` writes the names of OVITO particle/bond/angle/dihedral/improper types to the data file as LAMMPS type maps.

        **LAMMPS triclinic simulation cell format**

        .. versionadded:: 3.10.6

        OVITO can export *lammps/dump* and *lammps/data* files using either the restricted or the new general `triclinic format <https://docs.lammps.org/Howto_triclinic.html#general-triclinic-simulation-boxes-in-lammps>`__.
        The option can be toggled using the ``restricted_triclinic`` keyword parameter. Currently this option defaults to ``True``, maintaining backward compatibility with previous versions of OVITO and LAMMPS.

        **VASP (POSCAR) format**

        When exporting to the *vasp* file format, OVITO will output atomic positions and velocities in Cartesian coordinates by default.
        You can request output in reduced cell coordinates by specifying the ``reduced`` keyword parameter::

            export_file(pipeline, "structure.poscar", "vasp", reduced=True)

        **Global attributes**

        The *txt/attr* file format allows you to write global quantities computed by the data pipeline to a text file.
        For example, here is how you export the number of FCC atoms identified by a :py:class:`~ovito.modifiers.CommonNeighborAnalysisModifier`
        as a function of simulation time to a simple text file::

            export_file(pipeline, "data.txt", "txt/attr",
                columns=["Timestep", "CommonNeighborAnalysis.counts.FCC"],
                multiple_frames=True)

        .. tip::

            If you are not sure which global attributes are available for export, you can print the list of :py:attr:`~ovito.data.DataCollection.attributes`
            produced by your current data pipeline to the console::

               print(pipeline.compute().attributes)

    """

    # Determine the animation frame(s) to be exported.
    if 'frame' in params:
        frame = int(params['frame'])
        params['multiple_frames'] = True
        params['start_frame'] = frame
        params['end_frame'] = frame
        del params['frame']

    # Process the export format specified by the caller.
    # This may either be a format string, a FileWriterInterface subclass, or a FileWriterInterface instance.
    if isinstance(format, str):
        # Resolve format string to a FileExporter or a FileWriterInterface subclass.
        if format not in export_file._formatTable:
            raise ValueError(f"Unknown output file format: {format}")
        format = export_file._formatTable[format]

    if issubclass(format, FileExporter):
        # Instantiate the FileExporter subclass and initialize it with the parameters dictionary.
        exporter = format(params)
    elif issubclass(format, FileWriterInterface):
        # Instantiate the Python exporter class and the PythonFileExporter wrapper.
        # Split the input params dictionary into parameters for the Python exporter and the PythonFileExporter.
        non_delegate_params = {'frame', 'multiple_frames', 'start_frame', 'end_frame', 'every_nth_frame', 'key', 'pipeline', 'scene'}
        delegate = format(**{key: params[key] for key in params if key not in non_delegate_params})
        exporter = PythonFileExporter(delegate=delegate, **{key: params[key] for key in non_delegate_params if key in params})
    elif isinstance(format, FileWriterInterface):
        # Instantiate the PythonFileExporter wrapper around the existing FileWriterInterface instance.
        exporter = PythonFileExporter(delegate=format, **params)
    else:
        raise TypeError(f"Invalid file format: {format}")

    # Convert from os.PathLike to string.
    file = os.fspath(file)

    # Pass function parameters to exporter object.
    exporter.output_filename = file

    # Detect wildcard filename.
    if '*' in file:
        exporter.wildcard_filename = file
        exporter.use_wildcard_filename = True

    # Pass data to be exported to the exporter:
    if isinstance(data, Pipeline):
        exporter.pipeline = data
    elif isinstance(data, PipelineNode):
        exporter.pipeline = Pipeline(source=data)
    elif isinstance(data, DataCollection):
        exporter.pipeline = Pipeline(source=StaticSource(data=data))
    elif isinstance(data, DataObject):
        data_collection = DataCollection()
        data_collection.objects.append(data)
        exporter.pipeline = Pipeline(source=StaticSource(data=data_collection))
        exporter.key = data.identifier
    elif data is not None:
        raise TypeError(f"Cannot export this kind of Python object: {data}")

    # Let the exporter pick exportable data if nothing has been specified by the user.
    exporter.select_default_exportable_data()

    # Automatically adjust frame interval to length of exportable trajectory.
    if exporter.multiple_frames:
        # This method will fetch the length of the trajectory from the pipeline and use it to set
        # the export interval. We also check whether the user has specified explicit interval bounds.
        exporter.determine_export_interval('start_frame' not in params, 'end_frame' not in params)

    # Let the exporter do its job.
    exporter.do_export()
ovito.io.export_file = export_file

# This is the table of export formats used by the export_file() function
# to look up the right exporter class for a file format.
# Plugins can register their exporter class by inserting a new entry in this dictionary.
export_file._formatTable = {}
export_file._formatTable["txt/attr"] = AttributeFileExporter