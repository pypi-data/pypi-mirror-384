"""
.. versionadded:: 3.11.3

This module provides functions for direct data exchange with the pymatgen (`Python Materials Genomics <https://pymatgen.org/>`__).
It contains two high-level functions for converting atomistic data back and forth between
the representations of OVITO and pymatgen:

    * :py:func:`ovito_to_pymatgen`
    * :py:func:`pymatgen_to_ovito`

.. note::

    The functions of this module will raise an ``ImportError`` if the pymatgen package
    is not installed in the current Python interpreter. The embedded
    Python interpreter of OVITO Pro does *not* include the pymatgen package by default.
    You can install the pymatgen module by running ``ovitos -m pip install pymatgen`` if you are using the :ref:`embedded Python interpreter of OVITO Pro <ovitos_install_modules>`.
    Alternatively, if you installed the ``ovito`` module in your :ref:`own Python interpreter <use_ovito_with_system_interpreter>`,
    simply run ``pip3 install pymatgen`` to make the pymatgen package available.

"""

from __future__ import annotations
from typing import Optional

from ...data import DataCollection
import ovito.data

__all__ = ["ovito_to_pymatgen", "pymatgen_to_ovito"]


def ovito_to_pymatgen(data_collection: DataCollection) -> "pymatgen.core.Structure":
    """
    Constructs a `pymatgen Structure object <https://pymatgen.org/pymatgen.core.html#pymatgen.core.structure.Structure>`__
    from the particle data found in an OVITO :py:class:`~ovito.data.DataCollection`.
    Since pymatgen structures do not support shifted simulation cell origins, the particle positions
    and the :py:class:`~ovito.data.SimulationCell` geometry will be translated if necessary so that the new origin is at (0,0,0).
    Additionally, this routine attempts to convert OVITO particle types into
    `pymatgen Element objects <https://pymatgen.org/pymatgen.core.html#pymatgen.core.periodic_table.Element>`__
    using either their name (chemical symbol) or numeric id (atomic number). If no particle types are defined in the input (missing particle property "Particle Type"),
    a `pymatgen DummySpecies <https://pymatgen.org/pymatgen.core.html#pymatgen.core.periodic_table.DummySpecies>`__
    with name "X" will be assigned to all output atoms.

    :param data_collection: The OVITO :py:class:`~ovito.data.DataCollection` to convert. It must contain a :py:class:`~ovito.data.Particles` object.
    :return: An `pymatgen Structure object <https://pymatgen.org/pymatgen.core.html#pymatgen.core.structure.Structure>`__ containing the converted particle model.

    Usage example:

    .. literalinclude:: ../example_snippets/ovito_to_pymatgen.py
       :lines: 9-

    .. versionadded:: 3.11.3
    """

    from pymatgen.core import Lattice, Structure, Element, DummySpecies

    if not isinstance(data_collection, DataCollection):
        raise ValueError(
            f"Expected 'data_collection' to be an instance of DataCollection, but got {type(data_collection).__name__} instead."
        )

    if data_collection.cell is None:
        raise ValueError("Simulation cell cannot be `None`.")

    # Extract origin
    origin = data_collection.cell[:, 3]

    # Construct the pymatgen lattice
    lattice = Lattice(
        matrix=data_collection.cell[:3, :3].T, pbc=data_collection.cell.pbc
    )

    # Remap OVITO particle types to pymatgen Element / DummySpecies
    if data_collection.particles.particle_types is not None and len(data_collection.particles.particle_types.types) != 0:
        type_names = {}
        for t in data_collection.particles.particle_types.types:
            try:
                type_names[t.id] = Element(t.name)
            except ValueError:
                type_names[t.id] = Element.from_Z(t.id)
        symbols = [type_names[id] for id in data_collection.particles.particle_types]
    else:
        symbols = data_collection.particles.count * [
            DummySpecies("X", oxidation_state=None)
        ]

    site_properties = {}
    for key in data_collection.particles.keys():
        if key in ("Particle Type", "Position"):
            continue
        site_properties[key] = data_collection.particles[key]

    # Return the structure object
    return Structure(
        lattice=lattice,
        species=symbols,
        coords=data_collection.particles["Position"] - origin,
        coords_are_cartesian=True,
        site_properties=site_properties,
        properties={"cell_origin": origin},
    )


def pymatgen_to_ovito(
    structure: "pymatgen.core.Structure",
    data_collection: Optional[ovito.data.DataCollection] = None,
) -> DataCollection:
    """
    Converts a `pymatgen Structure object <https://pymatgen.org/pymatgen.core.html#pymatgen.core.structure.Structure>`__
    to an OVITO :py:class:`~ovito.data.DataCollection`.

    :param structure: The `pymatgen Structure object <https://pymatgen.org/pymatgen.core.html#pymatgen.core.structure.Structure>`__ to be converted.
    :param data_collection: An existing :py:class:`~ovito.data.DataCollection` to fill in with the atomic structure. A new data collection will be created if not provided.
    :return: The data collection containing the converted atoms data (in the form of a :py:class:`~ovito.data.Particles` object).

    Usage example:

    .. literalinclude:: ../example_snippets/pymatgen_to_ovito.py
       :lines: 9-

    .. versionadded:: 3.11.3
    """

    from pymatgen.core import Lattice, Structure, Element, DummySpecies

    if not data_collection:
        data_collection = DataCollection()

    # Set the unit cell and origin (if specified in atoms.info)
    cell = data_collection.create_cell(
        matrix=structure.lattice.matrix.T, pbc=structure.lattice.pbc
    )
    origin = (
        structure.properties["cell_origin"]
        if "cell_origin" in structure.properties
        else (0.0, 0.0, 0.0)
    )
    cell[:, 3] = origin

    # Create particle property from atomic positions
    particles = data_collection.create_particles(count=len(structure))
    particles.create_property("Position", data=structure.cart_coords + origin)

    # Create named particle types from chemical symbols
    if all([species.symbol == "X" for species in structure.types_of_species]):
        pass
    else:
        # Create named particle types from chemical symbols
        type_property = particles.create_property("Particle Type")
        # Map chemical element names to numeric type IDs.
        for i, sym in enumerate(structure.species):
            type_property[...][i] = type_property.add_type_name(
                sym.symbol, particles
            ).id

    # Create user-defined properties
    for key, value in structure.site_properties.items():
        particles.create_property(key, data=value)

    return data_collection
