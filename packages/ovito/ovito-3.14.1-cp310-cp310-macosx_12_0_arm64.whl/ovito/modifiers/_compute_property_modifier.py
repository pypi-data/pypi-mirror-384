from __future__ import annotations
from typing import Union
from . import ComputePropertyModifier
import collections.abc

# Implement the ComputePropertyModifier.neighbor_mode property.
def ComputePropertyModifier_neighbor_mode(self) -> "ComputePropertyModifier.NeighborMode":
    """
        Selects the criterion for visiting neighboring particles. Supported modes are:

          * ``ComputePropertyModifier.NeighborMode.Cutoff``
          * ``ComputePropertyModifier.NeighborMode.Bonded``

        :Default: ``ComputePropertyModifier.NeighborMode.Cutoff``
    """
    if self.operate_on != 'particles':
        return ComputePropertyModifier.NeighborMode.Cutoff
    return self.delegate.neighbor_mode
def ComputePropertyModifier_set_neighbor_mode(self, mode):
    self.operate_on = 'particles'
    self.delegate.neighbor_mode = mode
ComputePropertyModifier.neighbor_mode = property(ComputePropertyModifier_neighbor_mode, ComputePropertyModifier_set_neighbor_mode)

# Implement the ComputePropertyModifier.cutoff_radius property.
def ComputePropertyModifier_cutoff_radius(self) -> float:
    """
        The cutoff radius up to which neighboring particles are visited to compute :py:attr:`neighbor_expressions`.
        This parameter is only used if :py:attr:`operate_on` is set to ``'particles'``, :py:attr:`neighbor_mode` is set to ``Cutoff``,
        and :py:attr:`neighbor_expressions` has been specified.

        :Default: 3.0
    """
    if self.operate_on != 'particles':
        return 3.0
    return self.delegate.cutoff_radius
def ComputePropertyModifier_set_cutoff_radius(self, radius):
    self.operate_on = 'particles'
    self.delegate.cutoff_radius = radius
ComputePropertyModifier.cutoff_radius = property(ComputePropertyModifier_cutoff_radius, ComputePropertyModifier_set_cutoff_radius)

# Implement the ComputePropertyModifier.neighbor_expressions property.
def ComputePropertyModifier_neighbor_expressions(self) -> Union[str, collections.abc.Sequence[str]]:
    """
        The math expression(s) for the per-neighbor term(s), one for each vector component of the output particle property.
        The number of expressions in the list must match the number of vector components of the output property.
        If the output property is a scalar, only one expression string is required; otherwise, a list of strings.

        The neighbor expressions are evaluated for every neighboring particle and the obtained values are
        added to the output value of the central particle. Which neighboring particles are considered
        depends on the :py:attr:`neighbor_mode` and :py:attr:`cutoff_radius`. See :ref:`manual:particles.modifiers.compute_property.neighbor_expr`
        for more information.

        Neighbor expressions are only used if :py:attr:`operate_on` is set to ``'particles'``.

        **Example:** Compute mean velocity vector, averaged over all neighbors of a particle within a 3.8 Angstrom radius:

        .. literalinclude:: ../example_snippets/compute_property_modifier.py
           :lines: 81-94

        :Default: ``()``
    """
    if self.operate_on != 'particles':
        return ()
    expressions = self.delegate.neighbor_expressions
    if not isinstance(expressions, str):
        # Truncate tuple to include only non-empty strings.
        while len(expressions) != 0 and len(expressions[-1]) == 0:
            expressions = expressions[:-1]
    return expressions
def ComputePropertyModifier_set_neighbor_expressions(self, expressions):
    if not expressions and self.operate_on != 'particles': # To allow assigning "()" or an empty string to the property even if a non-particles delegate is active.
        return
    self.operate_on = 'particles'
    self.delegate.neighbor_expressions = expressions
ComputePropertyModifier.neighbor_expressions = property(ComputePropertyModifier_neighbor_expressions, ComputePropertyModifier_set_neighbor_expressions)
