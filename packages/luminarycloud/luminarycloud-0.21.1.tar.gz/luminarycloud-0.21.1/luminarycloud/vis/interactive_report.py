import io
from .visualization import RenderOutput
from .report import ReportEntry

try:
    import luminarycloud_jupyter as lcj
except ImportError:
    lcj = None


class InteractiveReport:
    """
    Interactive report widget with lazy loading for large datasets.

    How it works:
    1. on initialization:
       - sends metadata for all rows (for filtering/selection)
       - downloads the first row (to determine grid dimensions)
       - other rows remain unloaded

    2. on user request:
       - _load_row_data() is called with row index
       - downloads and sends images/plots for that specific row
       - python sets row_states to 'loading' -> 'loaded' (or 'error')

    This allows working with 1000+ row datasets without waiting for all data upfront.
    """

    # TODO Will/Matt: this list of report entries could be how we store stuff in the DB
    # for interactive reports, to reference the post proc. extracts. A report is essentially
    # a bunch of extracts + metadata.
    def __init__(self, entries: list[ReportEntry]) -> None:
        if not lcj:
            raise ImportError("InteractiveScene requires luminarycloud[jupyter] to be installed")

        self.entries = entries
        if len(self.entries) == 0:
            raise ValueError("Invalid number of entries, must be > 0")

        # Determine grid dimensions by downloading first entry
        # to understand the structure (number of columns)
        first_entry = self.entries[0]
        first_entry.download_extracts()

        # Calculate actual number of columns by counting how many cells
        # each extract produces (RenderOutput can produce multiple images)
        ncols = 0
        for extract in first_entry._extracts:
            if isinstance(extract, RenderOutput):
                image_and_label = extract.download_images()
                ncols += len(image_and_label)
            else:
                ncols += 1  # Plot data extracts produce one cell

        nrows = len(self.entries)

        # Create widget with metadata but without data
        self.widget = lcj.EnsembleWidget([re._metadata for re in self.entries], nrows, ncols)

        # Set the callback for lazy loading row data
        self.widget.set_row_data_callback(self._load_row_data)

    def _load_row_data(self, row: int) -> None:
        """
        Load and send data for a specific row to the widget.
        This is called on-demand when the user requests data for a row.
        """
        re = self.entries[row]

        # Download extracts if not already downloaded
        if len(re._extracts) == 0:
            re.download_extracts()

        # Process each extract and send to widget
        # Track the actual column index as we may have multiple cells per extract
        col = 0
        for extract in re._extracts:
            if isinstance(extract, RenderOutput):
                image_and_label = extract.download_images()
                # Each image gets its own column
                for il in image_and_label:
                    self.widget.set_cell_data(row, col, il[0].getvalue(), "jpg")
                    col += 1
            else:
                plot_data = extract.download_data()
                data = plot_data[0][0]
                all_axis_labels = data[0]

                axis_data = []
                for axis_idx in range(len(all_axis_labels)):
                    axis_values = [row[axis_idx] for row in data[1:]]
                    axis_data.append(axis_values)

                self.widget.set_cell_scatter_plot(
                    row,
                    col,
                    f"Row #{row} - Multi-axis Plot",
                    all_axis_labels,
                    axis_data,
                    plot_name=f"plot-{row}",
                    plot_mode="markers",
                )
                col += 1

    def _ipython_display_(self) -> None:
        """
        When the InteractiveReport is shown in Jupyter we show the underlying widget
        to run the widget's frontend code
        """
        self.widget._ipython_display_()
