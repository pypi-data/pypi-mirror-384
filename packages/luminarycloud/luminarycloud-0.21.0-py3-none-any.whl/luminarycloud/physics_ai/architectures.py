# Copyright 2025 Luminary Cloud, Inc. All Rights Reserved.
from typing import List, Optional
import json

from .._client import get_default_client
from .._proto.api.v0.luminarycloud.physics_ai import physics_ai_pb2 as physaipb
from .._wrapper import ProtoWrapper, ProtoWrapperBase
from ..types.ids import PhysicsAiArchitectureID, PhysicsAiArchitectureVersionID
from ..enum.physics_ai_lifecycle_state import PhysicsAiLifecycleState

from .training_jobs import PhysicsAiTrainingJob


@ProtoWrapper(physaipb.PhysicsAiArchitectureVersion)
class PhysicsAiArchitectureVersion(ProtoWrapperBase):
    """
    Represents a specific version of a Physics AI architecture.

    .. warning:: This feature is experimental and may change or be removed without notice.
    """

    id: PhysicsAiArchitectureVersionID
    name: str
    architecture_name: str
    changelog: str
    lifecycle_state: PhysicsAiLifecycleState
    _proto: physaipb.PhysicsAiArchitectureVersion

    def get_training_description(self, config: dict) -> str:
        if config.get("description"):
            return config["description"]

        desc = f"Training job for architecture {self.name}"
        if config.get("custom_args"):
            desc += f" with custom args: {config['custom_args']}"
        return desc

    def train(self, config: dict) -> PhysicsAiTrainingJob:
        """
        Submit a training job for this architecture version.

        Parameters
        ----------
        config : dict, optional
            Training configuration dictionary

        Returns
        -------
        PhysicsAiTrainingJob
            The submitted training job object
        """

        if "custom_args" not in config:
            config["custom_args"] = ""
        if "priority_class" not in config:
            config["priority_class"] = "prod-batch-priority"
        if "resources" not in config:
            config["resources"] = {}
        if "process_cpus" not in config["resources"]:
            config["resources"]["process_cpus"] = 8
        if "train_gpus" not in config["resources"]:
            config["resources"]["train_gpus"] = 1
        if "test_gpus" not in config["resources"]:
            config["resources"]["test_gpus"] = 1
        if "mode" not in config:
            config["mode"] = "full"

        training_config_json = json.dumps(config, indent=2)
        external_dataset_uri = f"gs://training-data/architecture-{self.id}"
        req = physaipb.SubmitTrainingJobRequest(
            architecture_version_id=self.id,
            training_description=self.get_training_description(config),
            external_dataset_uri=external_dataset_uri,
            training_config=training_config_json,
            initialization_type=physaipb.MODEL_INITIALIZATION_TYPE_RANDOM,
            base_model_version_id="",
        )

        response = get_default_client().SubmitTrainingJob(req)

        return PhysicsAiTrainingJob(response.training_job)


@ProtoWrapper(physaipb.PhysicsAiArchitecture)
class PhysicsAiArchitecture(ProtoWrapperBase):
    """
    Represents a Physics AI architecture with all its versions.

    .. warning:: This feature is experimental and may change or be removed without notice.
    """

    id: PhysicsAiArchitectureID
    name: str
    description: str
    versions: List[PhysicsAiArchitectureVersion]
    _proto: physaipb.PhysicsAiArchitecture

    def get_latest_version(self) -> Optional[PhysicsAiArchitectureVersion]:
        """
        Get the latest version of this architecture based on name.

        Returns
        -------
        PhysicsAiArchitectureVersion or None
            The first architecture version, or None if no versions exist.
            Note: Version ordering is now determined by the backend.
        """
        if not self.versions:
            return None
        return self.versions[0] if self.versions else None


def list_architectures() -> List[PhysicsAiArchitecture]:
    """
    List available Physics AI architectures for model training.

    .. warning:: This feature is experimental and may change or be removed without notice.

    Returns
    -------
    list[PhysicsAiArchitecture]
        A list of all available Physics AI architectures.
    """
    req = physaipb.ListArchitecturesRequest()
    res = get_default_client().ListArchitectures(req)
    return [PhysicsAiArchitecture(arch) for arch in res.architectures]
