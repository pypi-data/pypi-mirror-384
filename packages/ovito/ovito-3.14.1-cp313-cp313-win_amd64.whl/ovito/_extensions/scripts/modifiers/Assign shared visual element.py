##### Assign shared visual element #####
# This modifier replaces the visual elements of a group of data objects with a single one.
#
# This allows you to synchronize the visual appearance of multiple
# data objects of the same type, e.g., surface meshes.
#
# Enter a search pattern into the "Name prefix" field to
# select the objects whose visual elements should be unified.

from ovito.data import DataCollection
from ovito.vis import DataVis, SurfaceMeshVis, VoxelGridVis, TriangleMeshVis, LinesVis, VectorVis
from ovito.pipeline import ModifierInterface
from ovito.traits import OvitoObject
from traits.api import Str, Map, observe
import fnmatch

# Table of supported data object classes, human readable names, corresponding visual element classes, and DataCollection accessor names.
data_object_types = {
    "Surface meshes": {
        "class": "SurfaceMesh",
        "vis_class": SurfaceMeshVis,
        "accessor": "surfaces"
    },
    "Voxel grids": {
        "class": "VoxelGrid",
        "vis_class": VoxelGridVis,
        "accessor": "grids"
    },
    "Triangle meshes": {
        "class": "TriangleMesh",
        "vis_class": TriangleMeshVis,
        "accessor": "triangle_meshes"
    },
    "Lines": {
        "class": "Lines",
        "vis_class": LinesVis,
        "accessor": "lines"
    },
    "Vectors": {
        "class": "Vectors",
        "vis_class": VectorVis,
        "accessor": "vectors"
    }
}

class AssignSharedVisualElementModifier(ModifierInterface):

    object_type = Map(
        {key: value["class"] for key, value in data_object_types.items()},
        label="Type of objects"
    )

    name_filter: str = Str(
        label='Name prefix',
        ovito_placeholder="‹any›")

    vis: DataVis = OvitoObject(
        DataVis,
        factory=lambda *args, **kwargs: SurfaceMeshVis(*args, **kwargs),
        ovito_hide_object=True)

    def matches_name_filter(self, id: str) -> bool:
        if not self.name_filter:
            return True
        elif '*' in self.name_filter or '?' in self.name_filter:
            return fnmatch.fnmatch(id, self.name_filter)
        else:
            return id.startswith(self.name_filter)

    def modify(self, data: DataCollection, **kwargs):
        objects = getattr(data, data_object_types[self.object_type]["accessor"], None)
        if not objects:
            raise ValueError(f"Unknown object type: {self.object_type}")
        if not self.vis:
            print(f"No visual element set for object type {self.object_type}")
            return
        if len(objects) == 0:
            print(f"{self.object_type}: No input objects of this type")
            return

        num_replaced = 0
        log_output = []
        for id in objects:
            if not self.matches_name_filter(id):
                log_output.append(f"  {id}")
                continue
            log_output.append(f"* {id}")
            obj = data.make_mutable(objects[id])
            obj.vis = self.vis
            num_replaced += 1
        print(f"{self.object_type}: {num_replaced} out of {len(objects)} selected\n")
        print("\n".join(log_output))

    def get_pipeline_short_info(self, *args, **kwargs):
        return self.name_filter

    @observe("object_type")
    def notify_object_type_change(self, event):
        self.vis = data_object_types[self.object_type]["vis_class"](_load_user_defaults_in_gui=True)