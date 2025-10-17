# Copyright 2023-2024 Luminary Cloud, Inc. All Rights Reserved.
from typing import Any, Literal
from dataclasses import dataclass

from datetime import datetime

from .arguments import PipelineArgValueType
from ..pipelines import Pipeline, PipelineArgs
from .._client import get_default_client


@dataclass
class LogLine:
    timestamp: datetime
    level: int
    message: str

    @classmethod
    def from_json(cls, json: dict) -> "LogLine":
        return cls(
            timestamp=datetime.fromisoformat(json["timestamp"]),
            level=json["level"],
            message=json["message"],
        )


@dataclass
class PipelineRecord:
    """
    A PipelineRecord represents a persisted pipeline.
    """

    id: str
    name: str
    description: str | None
    definition_yaml: str
    created_at: datetime
    updated_at: datetime

    # I don't think users need to get the Pipeline object from a PipelineRecord, but if they did,
    # it would be done like this.
    # def pipeline(self) -> Pipeline:
    #     return Pipeline._from_yaml(self.definition_yaml)

    @classmethod
    def from_json(cls, json: dict) -> "PipelineRecord":
        return cls(
            id=json["id"],
            name=json["name"],
            description=json["description"],
            definition_yaml=json["definition_yaml"],
            created_at=datetime.fromisoformat(json["created_at"]),
            updated_at=datetime.fromisoformat(json["updated_at"]),
        )

    def pipeline_jobs(self) -> "list[PipelineJobRecord]":
        """
        Returns a list of pipeline jobs that were created from this pipeline.

        Returns
        -------
        list[PipelineJobRecord]
            A list of PipelineJobRecord objects.
        """
        res = get_default_client().http.get(f"/rest/v0/pipelines/{self.id}/pipeline_jobs")
        return [PipelineJobRecord.from_json(p) for p in res["data"]]


@dataclass
class PipelineJobRecord:
    """
    A PipelineJobRecord represents a persisted pipeline job.
    """

    id: str
    pipeline_id: str
    name: str
    description: str | None
    status: Literal["pending", "running", "completed", "failed"]
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None
    completed_at: datetime | None

    @classmethod
    def from_json(cls, json: dict) -> "PipelineJobRecord":
        return cls(
            id=json["id"],
            pipeline_id=json["pipeline_id"],
            name=json["name"],
            description=json["description"],
            status=json["status"],
            created_at=datetime.fromisoformat(json["created_at"]),
            updated_at=datetime.fromisoformat(json["updated_at"]),
            started_at=datetime.fromisoformat(json["started_at"]) if json["started_at"] else None,
            completed_at=(
                datetime.fromisoformat(json["completed_at"]) if json["completed_at"] else None
            ),
        )

    def pipeline(self) -> PipelineRecord:
        """
        Returns the pipeline that this pipeline job was created from.

        Returns
        -------
        PipelineRecord
            The PipelineRecord for the pipeline that this pipeline job was created from.
        """
        return get_pipeline(self.pipeline_id)

    def runs(self) -> "list[PipelineJobRunRecord]":
        """
        Returns a list of runs for this pipeline job.

        Returns
        -------
        list[PipelineJobRunRecord]
            A list of PipelineJobRunRecord objects.
        """
        res = get_default_client().http.get(f"/rest/v0/pipeline_jobs/{self.id}/runs")
        return [PipelineJobRunRecord.from_json(r) for r in res["data"]]

    def logs(self) -> list[LogLine]:
        """
        Returns a list of log lines for this pipeline job.

        Each log line is a LogLine object, which has a timestamp, level, and message.

        Returns
        -------
        list[LogLine]
            A list of LogLine objects.
        """
        res = get_default_client().http.get(f"/rest/v0/pipeline_jobs/{self.id}/logs")
        return [LogLine.from_json(l) for l in res["data"]]

    def artifacts(self) -> list[dict]:
        """
        Returns a list of artifacts that were produced by this pipeline job.

        Artifacts are things like Geometries, Meshes, and Simulations. Each artifact is a dictionary
        with an "id" key, which is an identifier for the artifact.

        .. warning:: This feature is experimental and may change or be removed in the future.

        Returns
        -------
        list[dict]
            A list of artifact dictionaries.
        """
        res = get_default_client().http.get(f"/rest/v0/pipeline_jobs/{self.id}/artifacts")
        return res["data"]


@dataclass
class PipelineJobRunRecord:
    pipeline_job_id: str
    idx: int
    arguments: list[PipelineArgValueType]
    status: Literal["pending", "running", "completed", "failed"]

    @classmethod
    def from_json(cls, json: dict) -> "PipelineJobRunRecord":
        return cls(
            pipeline_job_id=json["pipeline_job_id"],
            idx=json["idx"],
            arguments=json["arguments"],
            status=json["status"],
        )

    def pipeline_job(self) -> PipelineJobRecord:
        """
        Returns the pipeline job that this pipeline job run was created from.

        Returns
        -------
        PipelineJobRecord
            The PipelineJobRecord for the pipeline job that this pipeline job run was created from.
        """
        return get_pipeline_job(self.pipeline_job_id)

    def logs(self) -> list[LogLine]:
        """
        Returns a list of log lines for this pipeline job run.

        Each log line is a LogLine object, which has a timestamp, level, and message.

        Returns
        -------
        list[LogLine]
            A list of LogLine objects.
        """
        res = get_default_client().http.get(
            f"/rest/v0/pipeline_jobs/{self.pipeline_job_id}/runs/{self.idx}/logs"
        )
        return [LogLine.from_json(l) for l in res["data"]]

    def artifacts(self) -> list[dict]:
        """
        Returns a list of artifacts that were produced by this pipeline job run.

        Artifacts are things like Geometries, Meshes, and Simulations. Each artifact is a dictionary
        with an "id" key, which is an identifier for the artifact.

        .. warning:: This feature is experimental and may change or be removed in the future.

        Returns
        -------
        list[dict]
            A list of artifact dictionaries.
        """
        res = get_default_client().http.get(
            f"/rest/v0/pipeline_jobs/{self.pipeline_job_id}/runs/{self.idx}/artifacts"
        )
        return res["data"]


def create_pipeline(
    name: str, pipeline: Pipeline | str, description: str | None = None
) -> PipelineRecord:
    """
    Create a new pipeline.

    Parameters
    ----------
    name : str
        Name of the pipeline.
    pipeline : Pipeline | str
        The pipeline to create. Accepts a Pipeline object or a YAML-formatted pipeline definition.
    description : str, optional
        Description of the pipeline.
    """
    if isinstance(pipeline, Pipeline):
        definition_yaml = pipeline.to_yaml()
    else:
        definition_yaml = pipeline
    body = {
        "name": name,
        "definition_yaml": definition_yaml,
        "description": description,
    }
    res = get_default_client().http.post("/rest/v0/pipelines", body)
    return PipelineRecord.from_json(res["data"])


def list_pipelines() -> list[PipelineRecord]:
    """
    List all pipelines.
    """
    res = get_default_client().http.get("/rest/v0/pipelines")
    return [PipelineRecord.from_json(p) for p in res["data"]]


def get_pipeline(id: str) -> PipelineRecord:
    """
    Get a pipeline by ID.

    Parameters
    ----------
    id : str
        ID of the pipeline to fetch.
    """
    res = get_default_client().http.get(f"/rest/v0/pipelines/{id}")
    return PipelineRecord.from_json(res["data"])


def create_pipeline_job(
    pipeline_id: str, args: PipelineArgs, name: str, description: str | None = None
) -> PipelineJobRecord:
    """
    Create a new pipeline job.

    Parameters
    ----------
    pipeline_id : str
        ID of the pipeline to invoke.
    args : PipelineArgs
        Arguments to pass to the pipeline.
    name : str
        Name of the pipeline job.
    description : str, optional
        Description of the pipeline job.
    """

    arg_rows = [row.row_values for row in args.rows]
    body = {
        "name": name,
        "description": description,
        "argument_names": [p.name for p in args.params],
        "argument_rows": arg_rows,
    }

    res = get_default_client().http.post(f"/rest/v0/pipelines/{pipeline_id}/pipeline_jobs", body)
    return PipelineJobRecord.from_json(res["data"])


def get_pipeline_job(id: str) -> PipelineJobRecord:
    """
    Get a pipeline job by ID.
    """
    res = get_default_client().http.get(f"/rest/v0/pipeline_jobs/{id}")
    return PipelineJobRecord.from_json(res["data"])


def list_pipeline_jobs() -> list[PipelineJobRecord]:
    """
    List all pipeline jobs.
    """
    res = get_default_client().http.get("/rest/v0/pipeline_jobs")
    return [PipelineJobRecord.from_json(p) for p in res["data"]]
