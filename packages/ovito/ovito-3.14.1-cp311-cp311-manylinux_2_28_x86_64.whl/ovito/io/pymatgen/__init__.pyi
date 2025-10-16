"""This module provides functions for direct data exchange with the pymatgen (`Python Materials Genomics <https://pymatgen.org/>`__).
It contains two high-level functions for converting atomistic data back and forth between
the representations of OVITO and pymatgen:

    * :py:func:`ovito_to_pymatgen`
    * :py:func:`pymatgen_to_ovito`

    The functions of this module will raise an ``ImportError`` if the pymatgen package
    is not installed in the current Python interpreter. The embedded
    Python interpreter of OVITO Pro does *not* include the pymatgen package by default.
    You can install the pymatgen module by running ``ovitos -m pip install pymatgen`` if you are using the embedded Python interpreter of OVITO Pro.
    Alternatively, if you installed the ``ovito`` module in your own Python interpreter,
    simply run ``pip3 install pymatgen`` to make the pymatgen package available."""
__all__ = ['ovito_to_pymatgen', 'pymatgen_to_ovito']
from typing import Optional
import ovito.data
import pymatgen.core

def pymatgen_to_ovito(structure: pymatgen.core.Structure, data_collection: Optional[ovito.data.DataCollection]=None) -> ovito.data.DataCollection:
    """Converts a `pymatgen Structure object <https://pymatgen.org/pymatgen.core.html#pymatgen.core.structure.Structure>`__
to an OVITO :py:class:`DataCollection`.

:param structure: The `pymatgen Structure object <https://pymatgen.org/pymatgen.core.html#pymatgen.core.structure.Structure>`__ to be converted.
:param data_collection: An existing :py:class:`DataCollection` to fill in with the atomic structure. A new data collection will be created if not provided.
:return: The data collection containing the converted atoms data (in the form of a :py:class:`Particles` object).

Usage example:

```python
  from ovito.pipeline import StaticSource, Pipeline
  from ovito.io.pymatgen import pymatgen_to_ovito
  from pymatgen.core import Structure, Lattice
  
  lattice = Lattice.cubic(3.93)
  
  # Atomic basis for L12 structure
  species = ["Al", "Pt", "Pt", "Pt"]
  coords = [
      [0.0, 0.0, 0.0],
      [0.5, 0.5, 0.0],
      [0.5, 0.0, 0.5],
      [0.0, 0.5, 0.5],
  ]
  
  # The pymatgen Structure object to convert:
  pymatgen_structure = Structure(lattice, species, coords)
  
  # Convert the Structure object to an OVITO DataCollection:
  data = pymatgen_to_ovito(pymatgen_structure)
  
  # We may now create a Pipeline object with a StaticSource and use the
  # converted dataset as input for a data pipeline:
  pipeline = Pipeline(source=StaticSource(data=data))
```"""
    ...

def ovito_to_pymatgen(data_collection: ovito.data.DataCollection) -> pymatgen.core.Structure:
    """Constructs a `pymatgen Structure object <https://pymatgen.org/pymatgen.core.html#pymatgen.core.structure.Structure>`__
from the particle data found in an OVITO :py:class:`DataCollection`.
Since pymatgen structures do not support shifted simulation cell origins, the particle positions
and the :py:class:`SimulationCell` geometry will be translated if necessary so that the new origin is at (0,0,0).
Additionally, this routine attempts to convert OVITO particle types into
`pymatgen Element objects <https://pymatgen.org/pymatgen.core.html#pymatgen.core.periodic_table.Element>`__
using either their name (chemical symbol) or numeric id (atomic number). If no particle types are defined in the input (missing particle property "Particle Type"),
a `pymatgen DummySpecies <https://pymatgen.org/pymatgen.core.html#pymatgen.core.periodic_table.DummySpecies>`__
with name "X" will be assigned to all output atoms.

:param data_collection: The OVITO :py:class:`DataCollection` to convert. It must contain a :py:class:`Particles` object.
:return: An `pymatgen Structure object <https://pymatgen.org/pymatgen.core.html#pymatgen.core.structure.Structure>`__ containing the converted particle model.

Usage example:

```python
  from ovito.io import import_file
  from ovito.io.pymatgen import ovito_to_pymatgen
  
  # Create an OVITO data pipeline from an external file:
  pipeline = import_file("input/simulation.dump")
  
  # Evaluate pipeline to obtain a DataCollection:
  data = pipeline.compute()
  
  # Convert it to a pymatgen Structure object object:
  ase_atoms = ovito_to_pymatgen(data)
```"""
    ...