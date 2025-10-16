import importlib

# Note: Using importlib.import_module() to import modules, because human-readable Python script names in this directory contain whitespaces.
ASEDatabaseReader = importlib.import_module(".ASE Database", __name__).ASEDatabaseReader
ASETrajectoryReader = importlib.import_module(".ASE Trajectory", __name__).ASETrajectoryReader
