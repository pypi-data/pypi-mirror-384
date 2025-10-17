import json
import os
from typing import TYPE_CHECKING

from .visualization import Scene, RenderOutput, range_query
from .data_extraction import DataExtractor, ExtractOutput
from ..enum import RenderStatusType, ExtractStatusType, FieldAssociation
from ..solution import Solution
from .vis_util import _InternalToken, _get_status
from time import sleep
from .._proto.api.v0.luminarycloud.vis import vis_pb2
from .._client import get_default_client
from .._helpers._get_project_id import _get_project_id
import luminarycloud.enum.quantity_type as quantity_type

if TYPE_CHECKING:
    from .interactive_report import InteractiveReport


# TODO Will/Matt: this could be something like what we store in the DB
# A report can contain a list of report entries that reference post proc.
# extracts + styling info for how they should be displayed
class ReportEntry:
    """
    A single entry in a report, containing references to extracts and metadata.
    Each extract can have multiple pieces of data (e.g. multiple images for a
    RenderOutput, or multiple curves for an ExtractOutput).  Metadata is a
    dictionary of key/value pairs that can be used to store additional
    information about the report entry. Typically, the metadata would include
    things like simulation ID, lift/drag values, and scalar ranges for each
    solution. The metadata is used to filter and sort data in the ensemble
    widget.
    """

    def __init__(
        self, project_id: str, extract_ids: list[str] = [], metadata: dict[str, str | float] = {}
    ) -> None:
        self._project_id = project_id
        self._extract_ids = extract_ids
        self._extracts: list[ExtractOutput | RenderOutput] = []
        self._metadata = metadata
        self._statuses = statuses = [RenderStatusType.INVALID] * len(self._extract_ids)

    def to_dict(self) -> dict:
        return {
            "project_id": self._project_id,
            "extract_ids": self._extract_ids,
            "metadata": self._metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ReportEntry":
        return cls(
            project_id=data["project_id"],
            extract_ids=data.get("extract_ids", []),
            metadata=data.get("metadata", {}),
        )

    def refresh_statuses(self) -> None:
        for i, eid in enumerate(self._extract_ids):
            self._statuses[i] = _get_status(self._project_id, eid)

    def is_complete(self) -> bool:
        self.refresh_statuses()
        return all(
            (status == RenderStatusType.COMPLETED or status == RenderStatusType.FAILED)
            for status in self._statuses
        )

    # Download all extracts for this report entry
    def download_extracts(self) -> None:
        self._extracts = []
        for eid in self._extract_ids:
            status = _get_status(self._project_id, eid)
            if status != ExtractStatusType.COMPLETED:
                raise Exception(f"Extract {eid} is not complete")
            req = vis_pb2.DownloadExtractRequest()
            req.extract_id = eid
            req.project_id = self._project_id
            # TODO: This is a bit awkward in that we download the extract to figure out what type
            # it is, but this is just a temporary thing, later we'll have a report DB table that
            # stores the extracts for a report and their types, etc.
            res: vis_pb2.DownloadExtractResponse = get_default_client().DownloadExtract(req)
            extract = (
                ExtractOutput(_InternalToken())
                if res.HasField("line_data")
                else RenderOutput(_InternalToken())
            )
            extract._set_data(eid, self._project_id, eid, eid, status)
            self._extracts.append(extract)


class Report:
    """
    A report containing multiple report entries. There is support for
    serialization and deserialization to/from JSON since generating the extracts
    and metadata can be expensive.
    """

    def __init__(self, entries: list[ReportEntry]):
        self._entries = entries

    def to_dict(self) -> dict:
        return {"entries": [entry.to_dict() for entry in self._entries]}

    @classmethod
    def from_dict(cls, data: dict) -> "Report":
        entries = [ReportEntry.from_dict(e) for e in data.get("entries", [])]
        return cls(entries)

    def _check_status(self) -> bool:
        """Check the status of all ReportEntries and their extracts, grouped by entry."""
        still_pending = False
        print("\n" + "=" * 60)
        print("STATUS CHECK".center(60))
        print("=" * 60)

        if not self._entries:
            raise RuntimeError("No report entries to check status.")

        print(f"{'Entry':<8} | {'Extract ID':<20} | {'Status':<15}")
        print("-" * 60)
        for idx, entry in enumerate(self._entries):
            entry.refresh_statuses()
            for eid, status in zip(entry._extract_ids, entry._statuses):
                if status != RenderStatusType.COMPLETED and status != RenderStatusType.FAILED:
                    still_pending = True
                print(f"{idx:<8} | {eid:<20} | {status.name:<15}")
        print("=" * 60)
        return still_pending

    def wait_for_completion(self):
        """Wait for all report entries' extracts to complete."""
        if not self._entries:
            raise RuntimeError("No report entries to wait for.")
        while self._check_status():
            sleep(5)
        print("All report entries' extracts have completed.")

    def interact(self) -> "InteractiveReport":
        from .interactive_report import InteractiveReport

        if not self._check_status:
            raise ValueError("Error: report entries are still pending")
        return InteractiveReport(self._entries)


class ReportGenerator:
    """
    A helper for generating reports from multiple solutions, scenes, data extractors and
    per solution metatdata.

    Attributes:
    -----------
    calculate_ranges: bool
        Whether to auto-calculate solution quantity ranges and add them to the
        metadata. Default is False.
    """

    def __init__(self, solutions: list[Solution]):
        self._scenes: list[Scene] = []
        self._data_extractors: list[DataExtractor] = []
        self._solution: list[Solution] = solutions
        # When we fire off requests we use these objects to track the progress.
        self._extract_outputs: list[ExtractOutput] = []
        self._render_outputs: list[RenderOutput] = []
        # Controls if we should calculate solution quanity ranges
        self.calculate_ranges: bool = False
        # Key is solution ID, value is the metadata dict
        self._metadata: dict[str, dict[str, str | float]] = {}
        for solution in solutions:
            if not isinstance(solution, Solution):
                raise TypeError("Expected a list of Solution objects.")

    def add_scene(self, scene: Scene):
        if not isinstance(scene, Scene):
            raise TypeError("Expected a Scene object.")
        self._scenes.append(scene)

    # TODO(Matt): we could just make this a single data extract then control how they
    # are added to each solution.
    def add_data_extractor(self, data_extractor: DataExtractor):
        if not isinstance(data_extractor, DataExtractor):
            raise TypeError("Expected a DataExtractor object.")
        self._data_extractors.append(data_extractor)

    def add_metadata(self, solution_id: str, metadata: dict[str, str | float]):
        if solution_id not in self._metadata:
            self._metadata[solution_id] = {}
        self._metadata[solution_id].update(metadata)

    def create_report(self) -> Report:
        entries = []
        for solution in self._solution:
            extract_ids = []
            project_id = _get_project_id(solution)
            if not project_id:
                raise ValueError("Solution does not have a project_id.")
            metadata = self._metadata.get(solution.id, {})
            metadata["solution id"] = solution.id
            if self.calculate_ranges:
                print(f"Calculating solution quantity ranges {solution.id}")
                ranges = range_query(solution, FieldAssociation.CELLS)
                for range_res in ranges:
                    if not quantity_type._is_vector(range_res.quantity):
                        metadata[f"{range_res.field_name} min"] = range_res.ranges[0].min_value
                        metadata[f"{range_res.field_name} max"] = range_res.ranges[0].max_value
                    else:
                        for r in range(len(range_res.ranges)):
                            if r == 0:
                                comp = "x"
                            elif r == 1:
                                comp = "y"
                            elif r == 2:
                                comp = "z"
                            elif r == 3:
                                comp = "mag"
                            comp_range = range_res.ranges[r]
                            metadata[f"{range_res.field_name} min ({comp})"] = comp_range.min_value
                            metadata[f"{range_res.field_name} max ({comp})"] = comp_range.max_value
            for extractor in self._data_extractors:
                sol_extractor = extractor.clone(solution)
                extract = sol_extractor.create_extracts(
                    name="Report Extract", description="Generated Report Extract"
                )
                extract_ids.append(extract._extract_id)

            for scene in self._scenes:
                sol_scene = scene.clone(solution)
                render_extract = sol_scene.render_images(
                    name="Report Scene", description="Generated Report Scene"
                )
                extract_ids.append(render_extract._extract_id)

            entries.append(ReportEntry(project_id, extract_ids, metadata))
        return Report(entries)


def save_report_to_json(report: Report, name: str, directory: str = ".") -> str:
    """Save a Report object to a JSON file named {name}_lcreport.json in the specified directory."""
    filename = f"{name}_lcreport.json"
    filepath = os.path.join(directory, filename)
    with open(filepath, "w") as f:
        json.dump(report.to_dict(), f, indent=2)
    return filepath


def load_report_from_json(filepath: str) -> "Report":
    """Load a Report object from a JSON file at the given file path."""
    with open(filepath, "r") as f:
        data = json.load(f)
    return Report.from_dict(data)
