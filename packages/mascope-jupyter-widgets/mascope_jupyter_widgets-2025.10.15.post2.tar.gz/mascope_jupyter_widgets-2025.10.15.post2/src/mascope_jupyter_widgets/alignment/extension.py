import re
from functools import cached_property
from traitlets import HasTraits, Float
import pandas as pd
import ipywidgets as widgets
from plotly.subplots import make_subplots
import plotly.graph_objs as go
from mascope_tools.alignment.utils import (
    collect_spectra,
    filter_centroids,
    flag_satellite_peaks,
    average_sample_item_spectra,
)
from mascope_tools.alignment.calibration import MassAligner, calibrate_aligned_spectra
from ..mascope_data.access import load_mascope_token, load_url


class PeakAssignmentExtension(HasTraits):
    """Peak assignment extension for mascope Jupyter widgets"""

    # --- Centroid filtering parameters --- #
    min_intensity = Float(0.0, help="Minimum intensity for centroid filtering")
    snr_threshold = Float(3.0, help="SNR threshold for centroid filtering")

    # --- Mass alignment parameters --- #
    alignment_min_intensity = Float(0.0, help="Minimum intensity for mass alignment")
    alignment_window_factor = Float(
        1.0, help="Mass alignment window factor (times FWHM)"
    )
    alignment_min_fraction = Float(
        1.0, help="Minimum fraction of scans for mass alignment"
    )

    # --- Peak binning and assignment parameters --- #
    peak_window_factor = Float(
        2.0, help="Sum centroided spectrum binning window factor (times FWHM)"
    )
    base_peak_percentile = Float(
        99.99, help="Base peak percentile for satellite flagging"
    )
    symmetry_tolerance_ppm = Float(
        20.0, help="Symmetry tolerance for satellite flagging"
    )

    correction_factors_per_sample = None

    @property
    def mascope_url(self):
        """Mascope instance URL"""
        return load_url()[0]

    @property
    def access_token(self):
        """Mascope Jupyter Notebook access token"""
        return load_mascope_token()

    @cached_property
    def centroids(self):
        """Calibrated centroids per scan for samples in match_samples"""
        # --- Collect centroids from mascope --- #
        centroids_per_scan = collect_spectra(
            mascope_url=self.mascope_url,
            access_token=self.access_token,
            samples=self.match_samples,
            update_cached=False,
        )

        # --- Filter centroids --- #
        print("Filtering centroids per scan...")
        filtered_centroids_per_scan = filter_centroids(
            centroids_per_scan,
            min_intensity=self.min_intensity,
            snr_threshold=self.snr_threshold,
        )

        # --- Align centroids --- #
        print("Aligning centroids per scan...")
        vlm_corrector = MassAligner(
            min_peak_intensity=self.alignment_min_intensity,
            min_fraction=self.alignment_min_fraction,
            window_factor=self.alignment_window_factor,
        )
        vlm_corrector.fit(filtered_centroids_per_scan)
        alligned_centroids_per_scan = vlm_corrector.transform(
            filtered_centroids_per_scan
        )
        if vlm_corrector.points_mz.size < 2:
            raise ValueError(
                "Mass alignment failed: fewer than 2 alignment points found. "
                "Check your filtering parameters and input data quality."
            )

        vlm_min_mz = vlm_corrector.points_mz.min()
        vlm_max_mz = vlm_corrector.points_mz.max()

        print(
            f"Centroids per scan were alligned in range {vlm_min_mz:.4f}...{vlm_max_mz:.4f}. "
            "Peak assignment is unreliable outside this range."
        )

        # --- Calibrate aligned centroids --- #
        print("Calibrating aligned centroids...")
        match_isotopes = self.match_isotopes
        good_matches = match_isotopes[match_isotopes.match_score > 0].sort_values(
            by="sample_peak_intensity"
        )
        correction_factors = None
        for target_mz in good_matches.mz.values:
            try:
                calibrated_centroids_per_scan, correction_factors = (
                    calibrate_aligned_spectra(
                        alligned_centroids_per_scan, target_mz=target_mz, tol_ppm=3.0
                    )
                )
                print(f"Centroids calibrated using isotope at m/z {target_mz:.4f}.")
                break
            except ValueError:
                continue
        if correction_factors is None:
            raise ValueError(
                "No suitable isotope present in each scan found for calibration."
            )

        self.correction_factors_per_sample = (
            pd.DataFrame(
                {
                    "sample_item_id": [
                        i.metadata["sample_item_id"]
                        for i in calibrated_centroids_per_scan
                    ],
                    "correction_factors": correction_factors,
                }
            )
            .groupby("sample_item_id")
            .mean()
            .correction_factors.values
        )

        return calibrated_centroids_per_scan

    @cached_property
    def peaks(self):
        """Peaks dataframe after summing centroids across all samples, removing satellite peaks"""
        centroids = self.centroids
        sum_spectrum = centroids.compute_sum_spectrum(
            average=True, window_factor=self.peak_window_factor
        )
        peaks = pd.DataFrame(
            {"mz": sum_spectrum.mz, "intensity": sum_spectrum.intensity}
        )
        peaks = flag_satellite_peaks(
            peaks,
            base_peak_percentile=self.base_peak_percentile,
            symmetry_tolerance_ppm=self.symmetry_tolerance_ppm,
        )
        # Remove satellite peaks
        peaks = peaks[~peaks.is_satellite_peak].reset_index(drop=True)
        return peaks

    @cached_property
    def average_spectrum(self):
        """Averaged spectrum across all samples in match_samples, calibrated by correction factors"""
        samples_item_ids = self.match_samples.sample_item_id.values
        if self.correction_factors_per_sample is None:
            # Make sure centroids are there and calibrated
            self.centroids
        average_spectrum = average_sample_item_spectra(
            mascope_url=self.mascope_url,
            access_token=self.access_token,
            sample_item_ids=samples_item_ids,
            calibration_factors=self.correction_factors_per_sample,
        )
        return average_spectrum

    def matched_peak_timeseries(self, matches: pd.DataFrame) -> pd.DataFrame:
        """Extract timeseries of matched peaks from centroids"""
        centroids = self.centroids
        peak_timeseries = centroids.get_timeseries(
            window_factor=self.peak_window_factor
        )
        peak_timeseries.columns = peak_timeseries.columns + (
            pd.to_datetime(self.match_samples.datetime.iloc[0])
            - peak_timeseries.columns[0]
        )
        # Leave only matched peaks
        matched_mzs = matches.mz.values
        peak_timeseries = peak_timeseries.loc[matched_mzs]
        return peak_timeseries

    def plot_peak_assignment_results(
        self,
        matches: pd.DataFrame,
        dmz: float = 0.01,
    ):
        """Plot interactive visualization of peak assignment results.

        :param matches: Matches dataframe with peak assignment results.
        :type matches: pd.DataFrame
        :param dmz: m/z window half-width for plotting around each isotope peak, defaults to 0.01
        :type dmz: float, optional
        :raises ValueError: If no monoisotopic (M0) rows are found in matches.
        :return: Interactive widget for selecting and plotting peak assignments.
        :rtype: widgets.VBox
        """
        # Dropdown: only monoisotopic (M0) rows
        m0_matches = matches[matches.isotope_label == "M0"].reset_index(
            drop=False
        )  # keep original index in 'index'

        if m0_matches.empty:
            raise ValueError("No rows with isotope_label == 'M0' found in matches.")

        row_selector = widgets.Dropdown(
            options=[
                (f"{row['ion']} | {row['formula']} | m/z={row['mz']:.4f}", row.name)
                for _, row in m0_matches.iterrows()
            ],
            description="Match:",
            layout=widgets.Layout(width="80%"),
        )

        fig_output = widgets.Output()

        def plot_selected_match(row_idx: int) -> None:
            fig_output.clear_output(wait=True)
            sel_row = m0_matches.loc[row_idx]
            formula = sel_row["formula"]
            ion = sel_row["ion"]

            # All isotopes for this formula, sorted by m/z
            isotopes_df = (
                matches[matches.formula == formula]
                .sort_values("mz")
                .reset_index(drop=True)
            )
            n_isotopes = len(isotopes_df)
            if n_isotopes == 0:
                return

            # Find M0 peak intensity in peaks df
            m0_idx = (self.peaks["mz"] - sel_row["mz"]).abs().idxmin()
            m0_peak = self.peaks.loc[m0_idx]
            # Scale predicted intensities by M0 for visualization
            isotopes_df = isotopes_df.copy()
            isotopes_df["predicted_intensity"] *= m0_peak["intensity"]

            fig = make_subplots(
                rows=n_isotopes,
                cols=1,
                shared_xaxes=False,
                vertical_spacing=0.08,
            )

            mz_all = self.average_spectrum["mz"]
            intensity_all = self.average_spectrum["intensity"]

            for i, iso_row in isotopes_df.iterrows():
                mz_center = iso_row["mz"]
                mz_min = mz_center - dmz
                mz_max = mz_center + dmz

                # Windowed signal
                mask = (mz_all >= mz_min) & (mz_all <= mz_max)
                mz_win = mz_all[mask]
                intensity_win = intensity_all[mask]

                # Calibrated signal trace
                fig.add_trace(
                    go.Scatter(
                        x=mz_win,
                        y=intensity_win,
                        mode="lines",
                        name="Calibrated Signal" if i == 0 else None,
                        showlegend=(i == 0),
                        line=dict(color="#1f77b4"),
                    ),
                    row=i + 1,
                    col=1,
                )

                # Find nearest peak in peaks df to annotate
                nearest_idx = (self.peaks["mz"] - mz_center).abs().idxmin()
                nearest_peak = self.peaks.loc[nearest_idx]

                if abs(nearest_peak["mz"] - mz_center) <= dmz:
                    # Detected peak vertical line
                    fig.add_trace(
                        go.Scatter(
                            x=[nearest_peak["mz"], nearest_peak["mz"]],
                            y=[0, nearest_peak["intensity"]],
                            mode="lines",
                            line=dict(color="black", width=2),
                            showlegend=(i == 0),
                            name="Detected Peak",
                        ),
                        row=i + 1,
                        col=1,
                    )
                    # Detected peak marker
                    fig.add_trace(
                        go.Scatter(
                            x=[nearest_peak["mz"]],
                            y=[nearest_peak["intensity"]],
                            mode="markers",
                            marker=dict(color="black", size=8),
                            showlegend=False,
                        ),
                        row=i + 1,
                        col=1,
                    )
                    # Annotation for detected peak
                    fig.add_annotation(
                        x=nearest_peak["mz"],
                        y=nearest_peak["intensity"],
                        text=(
                            f"m/z={iso_row['mz']:.5f}<br>"
                            f"Errors, m/z: {iso_row['mz_error_ppm']:.2f}, intensity: {iso_row['intensity_error']:.2f}<br>"
                            f"{iso_row['isotope_label']}"
                        ),
                        showarrow=False,
                        yshift=25,
                        font=dict(size=10, color="black"),
                        bgcolor="rgba(255,255,255,0.7)",
                        row=i + 1,
                        col=1,
                    )

                    # Predicted intensity line
                    fig.add_trace(
                        go.Scatter(
                            x=[iso_row["predicted_mz"], iso_row["predicted_mz"]],
                            y=[0, iso_row["predicted_intensity"]],
                            mode="lines",
                            line=dict(color="red", width=2),
                            name="Predicted Peak",
                            showlegend=(i == 0),
                        ),
                        row=i + 1,
                        col=1,
                    )

                fig.update_xaxes(title_text="m/z", row=i + 1, col=1)
                fig.update_yaxes(title_text="Intensity", row=i + 1, col=1)

            fig.update_layout(
                title=f"{formula} | {ion}",
                height=280 * n_isotopes,
                width=750,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
                margin=dict(t=80),
            )

            with fig_output:
                fig.show()

        widgets.interactive_output(plot_selected_match, {"row_idx": row_selector})

        return widgets.VBox([row_selector, fig_output])

    def plot_match_timeseries(
        self,
        matches: pd.DataFrame,
        matched_peak_timeseries: pd.DataFrame,
        ions: list = None,
    ):
        """
        Interactive Plotly lineplot for matched peak timeseries.
        Dropdown allows selection of unique ions; all isotope_labels for the selected ion are plotted.
        """
        if not ions or len(ions) == 0:
            raise ValueError(
                "No ions specified. Please provide a non-empty list of ions to plot."
            )

        ions_found = [ion for ion in ions if ion in matches["ion"].unique()]
        if not ions_found:
            raise ValueError(
                "None of the specified ions were found in the matches DataFrame."
                "Make sure the ion names are the same as in the 'ion' column of matches."
            )

        fig = go.Figure()
        for ion in ions_found:
            ion_match = matches[matches["ion"] == ion]
            mz = ion_match["mz"].values[0]
            y = matched_peak_timeseries.loc[mz].values
            x = matched_peak_timeseries.columns
            label = f"{ion}, m/z={mz:.4f}"
            fig.add_trace(
                go.Scatter(
                    x=x,
                    y=y,
                    mode="lines",
                    name=label,
                    hovertemplate=(
                        "Time: %{x}<br>" "Intensity: %{y:.2f}<br>" f"{label}"
                    ),
                )
            )
        fig.update_layout(
            title="Peak Timeseries",
            xaxis_title="Timestamp",
            yaxis_title="Intensity [counts/s]",
            yaxis_type="log",
            height=500,
            width=900,
            margin=dict(t=60, b=40, l=40, r=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        )
        return fig
