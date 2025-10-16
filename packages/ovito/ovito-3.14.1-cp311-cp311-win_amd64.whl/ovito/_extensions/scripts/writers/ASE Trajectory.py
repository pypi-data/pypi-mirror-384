##### ASE trajectory writer #####
#
# [See documentation](manual:file_formats.output.ase_trajectory)

from ovito.data import Particles
from ovito.pipeline import Pipeline
from ovito.io import FileWriterInterface
from ovito.io.ase import ovito_to_ase
from typing import Any, Optional, Sequence

# Helper function checking whether the ASE database module is installed in the Python interpreter.
def _load_ase_module():
    try:
        import ase.io
    except ImportError as exc:
        raise ImportError('The ASE file writer of OVITO requires the ASE Python module. Please install it. '
            'If you are using OVITO Pro, use the "Python->Install additional package" function in the application settings dialog to install ASE. '
            'If you are executing this script with a standalone Python interpreter, run "pip install ase". '
            'If you are working in a conda environment, use "conda install ase" instead.') from exc
    return ase.io

class ASETrajectoryWriter(FileWriterInterface):

    def supports_trajectories(self):
        return True

    def exportable_type(self):
        return Particles

    def write(self, *, filename: str, frames: Sequence[int], pipeline: Optional[Pipeline], **kwargs: Any):
        aseio = _load_ase_module()
        traj = aseio.Trajectory(filename, mode='w')
        for progress, frame in enumerate(frames):
            yield progress/len(frames)
            data = pipeline.compute(frame)
            traj.write(ovito_to_ase(data))
        traj.close()
