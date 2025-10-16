import pandas as pd
import ipywidgets as widgets
from ..mascope_data.wrapper import MascopeDataWrapper
from .extension import PeakAssignmentExtension


class PeakAssignmentWidget:

    def __init__(self, dataset: MascopeDataWrapper) -> None:
        self.dataset = dataset
        self.dataset.extend(PeakAssignmentExtension)

    def plot_peak_assignment_results(self, matches: pd.DataFrame) -> widgets.Widget:
        return self.dataset.plot_peak_assignment_results(matches)

    def plot_match_timeseries(
        self,
        matches: pd.DataFrame,
        matched_peak_timeseries: pd.DataFrame,
        ions: list = None,
    ) -> widgets.Widget:
        return self.dataset.plot_match_timeseries(
            matches, matched_peak_timeseries, ions
        )

    def matched_peak_timeseries(self, matches: pd.DataFrame) -> pd.DataFrame:
        return self.dataset.matched_peak_timeseries(matches)
