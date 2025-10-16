from ovito import Scene
from ovito.pipeline import Pipeline
import ovito.nonpublic
from typing import Optional
from collections.abc import MutableSequence

class _ScenePipelinesList(MutableSequence):
    # This is a helper class is used for the implementation of the Scene.pipelines field. It emulates a
    # mutable list of Pipeline objects based on the list of child nodes of the scene root node.

    def __init__(self, children):
        self.children = children

    def __len__(self):
        return len(self.children)

    def __getitem__(self, index):
        if isinstance(index, slice):
            return [node.pipeline for node in self.children[index]]
        return self.children[index].pipeline

    def __setitem__(self, index, pipeline: Pipeline):
        if isinstance(index, slice):
            raise TypeError("This sequence type does not support slicing operations.")
        self.children[index].pipeline = pipeline

    def __delitem__(self, index):
        del self.children[index]

    def insert(self, index, value: Pipeline):
        node = ovito.nonpublic.SceneNode(pipeline=value)
        self.children.insert(index, node)

    def __str__(self):
        return str([node.pipeline for node in self.children])

# Implementation of the Scene.pipelines property:
def _Scene_pipelines(self) -> MutableSequence[Pipeline]:
    """ The list of :py:class:`~ovito.pipeline.Pipeline` objects that are currently part of the three-dimensional scene.
        Only pipelines in this list will display their output data in the interactive viewports and in rendered images. You can add or remove a pipeline either by calling
        its :py:meth:`~ovito.pipeline.Pipeline.add_to_scene` or :py:meth:`~ovito.pipeline.Pipeline.remove_from_scene` methods or by directly manipulating this
        list using the standard Python ``append()`` and ``del`` statements:

        .. literalinclude:: ../example_snippets/scene_pipelines.py
          :lines: 1-11
    """
    return _ScenePipelinesList(self.scene_root.children)
Scene.pipelines = property(_Scene_pipelines)

# Implementation of the Scene.selected_pipeline property:
def _get_Scene_selected_pipeline(self) -> Optional[Pipeline]:
    """ The :py:class:`~ovito.pipeline.Pipeline` currently selected in the OVITO desktop application,
        or ``None`` if no pipeline is selected. Typically, this is the last pipeline that was added to the scene using
        :py:meth:`Pipeline.add_to_scene() <ovito.pipeline.Pipeline.add_to_scene>`.

        This field can be useful for macro scripts running in the context of an interactive OVITO session,
        which want to perform some operation on the currently selected pipeline, e.g. inserting a new modifier.
    """
    selected_scene_node = self.selection.first
    return selected_scene_node.pipeline if selected_scene_node else None
def _set_Scene_selected_pipeline(self, pipeline):
    """ Sets the :py:class:`~ovito.pipeline.Pipeline` that is currently selected in the graphical user interface of OVITO. """
    if pipeline:
        for node in self.scene_root.children:
            if node.pipeline is pipeline:
                self.selection.nodes = [node]
                return
        raise ValueError("The specified pipeline is not part of the scene.")
    else:
        del self.selection.nodes[:]
Scene.selected_pipeline = property(_get_Scene_selected_pipeline, _set_Scene_selected_pipeline)
