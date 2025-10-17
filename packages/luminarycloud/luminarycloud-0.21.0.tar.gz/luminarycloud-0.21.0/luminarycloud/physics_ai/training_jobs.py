# Copyright 2025 Luminary Cloud, Inc. All Rights Reserved.
from typing import List, Optional
from datetime import datetime

from .._client import get_default_client
from .._proto.api.v0.luminarycloud.physics_ai import physics_ai_pb2 as physaipb
from .._proto.base import base_pb2 as basepb
from .._wrapper import ProtoWrapper, ProtoWrapperBase
from ..types.ids import PhysicsAiArchitectureVersionID


@ProtoWrapper(physaipb.PhysicsAiTrainingJob)
class PhysicsAiTrainingJob(ProtoWrapperBase):
    """
    Represents a Physics AI training job.

    .. warning:: This feature is experimental and may change or be removed without notice.
    """

    id: str
    architecture_version_id: PhysicsAiArchitectureVersionID
    user_id: str
    training_config: str
    training_data_source_type: physaipb.TrainingDataSourceType
    training_description: str
    external_dataset_uri: str
    initialization_type: physaipb.ModelInitializationType
    base_model_version_id: str
    status: basepb.JobStatus
    error_message: str
    output_model_version_id: str
    creation_time: datetime
    update_time: datetime
    _proto: physaipb.PhysicsAiTrainingJob

    def get_status(self) -> str:
        return basepb.JobStatusType.Name(self.status.typ)
