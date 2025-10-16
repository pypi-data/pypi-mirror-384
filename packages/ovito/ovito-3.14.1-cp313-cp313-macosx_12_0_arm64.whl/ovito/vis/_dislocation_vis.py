import types
import ovito.nonpublic
from . import DislocationVis

# Inject enum types.
# For backward compatibility with OVITO 3.11
DislocationVis.Shading = types.SimpleNamespace()
DislocationVis.Shading.Normal = ovito.nonpublic.ArrowShadingMode.Normal
DislocationVis.Shading.Flat = ovito.nonpublic.ArrowShadingMode.Flat