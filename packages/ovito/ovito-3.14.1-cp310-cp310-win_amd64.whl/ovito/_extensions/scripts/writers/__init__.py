import importlib
import ovito.io

# Note: Using importlib.import_module() to import modules, because human-readable Python script names in this directory contain whitespaces.
ASETrajectoryWriter = importlib.import_module(".ASE Trajectory", __name__).ASETrajectoryWriter

# Register the export format with the ovito.io.export_file() function:
ovito.io.export_file._formatTable["ase/traj"] = ASETrajectoryWriter