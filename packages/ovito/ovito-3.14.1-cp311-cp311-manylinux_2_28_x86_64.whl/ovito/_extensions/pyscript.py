# Load the C extension module.
import ovito.plugins.PyScript

try:
    # The GUI part is optional and may not be available in all builds of OVITO.
    import ovito.plugins.PyScriptGui
except ImportError:
    pass

# Load class add-ons.
import ovito._scene_class
import ovito.nonpublic._frame_buffer
import ovito.nonpublic._render_settings
import ovito.nonpublic._viewport_configuration
import ovito.data._data_collection
import ovito.pipeline._file_source
import ovito.pipeline._pipeline_node
import ovito.pipeline._pipeline_source_interface
import ovito.pipeline._modifier_interface
import ovito.pipeline._pipeline_class # Depends on 'ovito.pipeline.modifier_interface'
import ovito.vis._data_vis
import ovito.vis._viewport
import ovito.vis._viewport_overlay_interface
import ovito.io._file_reader_interface
import ovito.io._file_writer_interface
import ovito.io._import_file_func
import ovito.io._export_file_func
import ovito.gui._utility_interface
import ovito.gui._create_window
import ovito.gui._create_qwidget

# For backward compatibility with OVITO 3.9.2:
ovito.modifiers.PythonScriptModifier = ovito.modifiers.PythonModifier
ovito.pipeline.PythonScriptSource = ovito.pipeline.PythonSource
