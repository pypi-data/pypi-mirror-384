# Copyright 2025 Luminary Cloud, Inc. All Rights Reserved.
from dataclasses import dataclass

from .core import Operator, OperatorInputs, OperatorOutputs, PipelineOutput
from .parameters import StringPipelineParameter, IntPipelineParameter
from ..meshing import MeshGenerationParams


# Concrete PipelineOutput classes, i.e. the things that can "flow" in a Pipeline


class PipelineOutputGeometry(PipelineOutput):
    """A representation of a Geometry in a Pipeline."""

    pass


class PipelineOutputMesh(PipelineOutput):
    """A representation of a Mesh in a Pipeline."""

    pass


class PipelineOutputSimulation(PipelineOutput):
    """A representation of a Simulation in a Pipeline."""

    pass


# Operators


@dataclass
class ReadGeometryOutputs(OperatorOutputs):
    geometry: PipelineOutputGeometry
    """
    The Geometry identified by the given `geometry_id`, in the state it was in when the Pipeline was
    invoked. I.e. the latest GeometryVersion at that moment.
    """


class ReadGeometry(Operator[ReadGeometryOutputs]):
    """
    Reads a Geometry into the Pipeline.

    .. warning:: This feature is experimental and may change or be removed in the future.

    Parameters
    ----------
    geometry_id : str | StringPipelineParameter
        The ID of the Geometry to retrieve.

    Outputs
    -------
    geometry : PipelineOutputGeometry
        The latest GeometryVersion of the Geometry as of the moment the Pipeline was invoked.
    """

    def __init__(
        self,
        *,
        task_name: str | None = None,
        geometry_id: str | StringPipelineParameter,
    ):
        super().__init__(
            task_name,
            {"geometry_id": geometry_id},
            OperatorInputs(self),
            ReadGeometryOutputs._instantiate_for(self),
        )


@dataclass
class ReadMeshOutputs(OperatorOutputs):
    mesh: PipelineOutputMesh
    """
    The Mesh read from the given `mesh_id`.
    """


class ReadMesh(Operator[ReadMeshOutputs]):
    """
    Reads a Mesh into the Pipeline.

    .. warning:: This feature is experimental and may change or be removed in the future.

    Parameters
    ----------
    mesh_id : str | StringPipelineParameter
        The ID of the Mesh to retrieve.
    wait_timeout_seconds : int | IntPipelineParameter | None
        The number of seconds to wait for the Mesh to be ready. If None, defaults to 1800 seconds
        (30 minutes).

    Outputs
    -------
    mesh : PipelineOutputMesh
        The Mesh with the given `mesh_id`.
    """

    def __init__(
        self,
        *,
        task_name: str | None = None,
        mesh_id: str | StringPipelineParameter,
        wait_timeout_seconds: int | IntPipelineParameter | None = None,
    ):
        if wait_timeout_seconds is None:
            wait_timeout_seconds = 30 * 60
        super().__init__(
            task_name,
            {"mesh_id": mesh_id, "wait_timeout_seconds": wait_timeout_seconds},
            OperatorInputs(self),
            ReadMeshOutputs._instantiate_for(self),
        )


@dataclass
class ModifyGeometryOutputs(OperatorOutputs):
    geometry: PipelineOutputGeometry
    """The modified Geometry, represented as a new GeometryVersion."""


# TODO: figure out what `mods` actually is. What does the non-pipeline geo mod interface look like?
class ModifyGeometry(Operator[ModifyGeometryOutputs]):
    """
    Modifies a Geometry.

    .. warning:: This feature is experimental and may change or be removed in the future.

    Parameters
    ----------
    mods : dict
        The modifications to apply to the Geometry.
    geometry : PipelineOutputGeometry
        The Geometry to modify.

    Outputs
    -------
    geometry : PipelineOutputGeometry
        The modified Geometry, represented as a new GeometryVersion.
    """

    def __init__(
        self,
        *,
        task_name: str | None = None,
        mods: list[dict],
        geometry: PipelineOutputGeometry,
    ):
        raise NotImplementedError("ModifyGeometry is not implemented yet.")
        super().__init__(
            task_name,
            {"mods": mods},
            OperatorInputs(self, geometry=(PipelineOutputGeometry, geometry)),
            ModifyGeometryOutputs._instantiate_for(self),
        )


@dataclass
class MeshOutputs(OperatorOutputs):
    mesh: PipelineOutputMesh
    """The Mesh generated from the given Geometry."""


class Mesh(Operator[MeshOutputs]):
    """
    Generates a Mesh from a Geometry.

    .. warning:: This feature is experimental and may change or be removed in the future.

    Parameters
    ----------
    geometry : PipelineOutputGeometry
        The Geometry to mesh.
    mesh_name : str | StringPipelineParameter | None
        The name to assign to the Mesh. If None, a default name will be used.
    target_cv_count : int | None
        The target number of control volumes to generate. If None, a minimal mesh will be generated.

    Outputs
    -------
    mesh : PipelineOutputMesh
        The generated Mesh.
    """

    def __init__(
        self,
        *,
        task_name: str | None = None,
        geometry: PipelineOutputGeometry,
        mesh_name: str | StringPipelineParameter | None = None,
        target_cv_count: int | None,
    ):
        super().__init__(
            task_name,
            {
                "mesh_name": mesh_name,
                "target_cv_count": target_cv_count,
            },
            OperatorInputs(self, geometry=(PipelineOutputGeometry, geometry)),
            MeshOutputs._instantiate_for(self),
        )

    # TODO: bring back the full MeshGenerationParams, but we need to be able to hydrate it from the
    # pipeline YAML. I can probably bake that logic into PipelineDictable, `from_pipeline_dict` or
    # something.
    # @classmethod
    # def _parse_params(cls, params: dict) -> dict:
    #     return {"mesh_gen_params": MeshGenerationParams.from_pipeline_dict(**params["mesh_gen_params"])}


@dataclass
class SimulateOutputs(OperatorOutputs):
    simulation: PipelineOutputSimulation
    """The Simulation."""


class Simulate(Operator[SimulateOutputs]):
    """
    Runs a Simulation.

    .. warning:: This feature is experimental and may change or be removed in the future.

    Parameters
    ----------
    mesh : PipelineOutputMesh
        The Mesh to use for the Simulation.
    sim_name : str | StringPipelineParameter | None
        The name to assign to the Simulation. If None, a default name will be used.
    sim_template_id : str | StringPipelineParameter
        The ID of the SimulationTemplate to use for the Simulation.

    Outputs
    -------
    simulation : PipelineOutputSimulation
        The Simulation.
    """

    def __init__(
        self,
        *,
        task_name: str | None = None,
        mesh: PipelineOutputMesh,
        sim_name: str | StringPipelineParameter | None = None,
        sim_template_id: str | StringPipelineParameter,
    ):
        super().__init__(
            task_name,
            {
                "sim_name": sim_name,
                "sim_template_id": sim_template_id,
            },
            OperatorInputs(self, mesh=(PipelineOutputMesh, mesh)),
            SimulateOutputs._instantiate_for(self),
        )
