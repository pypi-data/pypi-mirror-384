import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import ipywidgets as widgets
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mascope_tools.alignment.calibration import CentroidedSpectrum
    import pandas as pd


def plot_mz_shifts_ppm(
    spectra: list["CentroidedSpectrum"], corrected_spectra: list["CentroidedSpectrum"]
) -> None:
    """Plots the m/z shifts in ppm before and after alignment correction.

    :param spectra: List of original spectra before alignment correction.
    :type spectra: list[CentroidedSpectrum]
    :param corrected_spectra: List of corrected spectra after alignment correction.
    :type corrected_spectra: list[CentroidedSpectrum]
    """
    # Flatten all m/z values before and after
    all_mzs_before = np.concatenate([s.mz for s in spectra])
    all_mzs_after = np.concatenate([s.mz for s in corrected_spectra])

    diff_ppm = (all_mzs_after - all_mzs_before) / all_mzs_before * 1e6

    plt.figure(figsize=(6, 3))
    plt.scatter(all_mzs_before, diff_ppm, s=2, alpha=0.3)
    plt.xlabel("m/z (before)")
    plt.ylabel("Δm/z (ppm, after - before)")
    plt.title("Alignment Correction Across m/z Range")

    plt.show()


def flatten_spectra(specs):
    """Flatten spectra into arrays of mz, intensity."""
    total_len = np.sum(s.mz.size for s in specs)
    mz = np.empty(total_len)
    intensity = np.empty(total_len)
    idx = 0
    for s in specs:
        n = len(s.mz)
        mz[idx : idx + n] = s.mz
        intensity[idx : idx + n] = s.intensity
        idx += n
    return mz, intensity


def compare_initial_and_corrected_spectra(
    spectra: list["CentroidedSpectrum"],
    corrected_spectra: list["CentroidedSpectrum"],
    total_averaged_signal: dict[str, np.ndarray],
) -> "widgets.interact":
    """Compare initial and corrected spectra using an interactive plot.

    :param spectra: List of original spectra before alignment correction.
    :type spectra: list[CentroidedSpectrum]
    :param corrected_spectra: List of corrected spectra after alignment correction.
    :type corrected_spectra: list[CentroidedSpectrum]
    :param total_averaged_signal: Averaged signal data containing m/z and intensity.
    :type total_averaged_signal: dict[str, np.ndarray]
    :return: Interactive widget for selecting m/z range and plotting spectra.
    :rtype: widgets.interact
    """
    # Precompute flattened arrays for performance
    mz_before, int_before = flatten_spectra(spectra)
    mz_after, int_after = flatten_spectra(corrected_spectra)

    window_factor = 2
    preliminary_sum_spec = corrected_spectra.compute_sum_spectrum(
        average=True, window_factor=window_factor
    )
    mz_binned = preliminary_sum_spec.mz
    int_binned = preliminary_sum_spec.intensity
    fwhm_binned = mz_binned / preliminary_sum_spec.resolution

    mz_slider = widgets.SelectionSlider(
        options=[float(f"{mz:.4f}") for mz in mz_binned],
        value=float(f"{mz_binned[0]:.4f}"),
        description="m/z window start",
        layout=widgets.Layout(width="80%"),
        continuous_update=False,
    )

    def plot_spectra_points(mz_center):
        closest_mz_binned_indx = np.argmin(np.abs(mz_binned - mz_center))
        peak_width_in_window = fwhm_binned[closest_mz_binned_indx]
        mz_start = mz_center - peak_width_in_window * window_factor
        mz_end = mz_center + peak_width_in_window * window_factor

        centroid_mask_before = (mz_before >= mz_start) & (mz_before <= mz_end)
        centroid_mask_after = (mz_after >= mz_start) & (mz_after <= mz_end)
        centroid_mask_binned = (mz_binned >= mz_start) & (mz_binned <= mz_end)
        averaged_spec_mask = (total_averaged_signal["mz"] >= mz_start) & (
            total_averaged_signal["mz"] <= mz_end
        )

        spec_mz_to_plot = total_averaged_signal["mz"][averaged_spec_mask]
        spec_intensity_to_plot = total_averaged_signal["intensity"][averaged_spec_mask]

        fig = make_subplots(
            rows=2,
            cols=1,
            subplot_titles=("Original", "Corrected"),
            shared_xaxes=True,
            shared_yaxes=True,
        )

        for row in [1, 2]:
            fig.add_trace(
                go.Scatter(
                    x=spec_mz_to_plot,
                    y=spec_intensity_to_plot,
                    mode="lines",
                    line=dict(color="black", width=1),
                    name="Averaged Spectrum",
                    showlegend=True,
                ),
                row=row,
                col=1,
            )

            # --- Semitransparent vertical red bands for binned centroids ---
            for x, y, w in zip(
                mz_binned[centroid_mask_binned],
                int_binned[centroid_mask_binned],
                fwhm_binned[centroid_mask_binned],
            ):
                fig.add_shape(
                    type="rect",
                    xref="x",
                    yref="paper",
                    x0=x - w / 2,
                    x1=x + w / 2,
                    y0=0,
                    y1=y,
                    fillcolor="red",
                    opacity=0.2,
                    line_width=0,
                    layer="below",
                    row=row,
                    col=1,
                )

        # Add a single dummy trace for legend entry
        fig.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode="lines",
                line=dict(color="red", width=5),
                name="Centroid Aggregation Width = FWHM",
                showlegend=True,
                opacity=0.2,
            ),
            row=2,
            col=1,
        )

        # --- Before centroids ---
        for x, y in zip(
            mz_before[centroid_mask_before], int_before[centroid_mask_before]
        ):
            fig.add_trace(
                go.Scatter(
                    x=[x, x],
                    y=[0, y],
                    mode="lines",
                    line=dict(color="darkgreen", width=1),
                    name="Centroids",
                    showlegend=True,
                ),
                row=1,
                col=1,
            )

        # --- After centroids ---
        for x, y in zip(mz_after[centroid_mask_after], int_after[centroid_mask_after]):
            fig.add_trace(
                go.Scatter(
                    x=[x, x],
                    y=[0, y],
                    mode="lines",
                    line=dict(color="darkgreen", width=1),
                    showlegend=False,
                ),
                row=2,
                col=1,
            )

        # --- Binned centroids ---
        for x, y in zip(
            mz_binned[centroid_mask_binned], int_binned[centroid_mask_binned]
        ):
            fig.add_trace(
                go.Scatter(
                    x=[x, x],
                    y=[0, y],
                    mode="lines",
                    line=dict(color="red", width=3),
                    name="Aggregated Centroid",
                    showlegend=True,
                ),
                row=2,
                col=1,
            )

        # Remove duplicate legend entries
        unique_names = set()
        for trace in fig.data:
            name = trace.name
            if name in unique_names:
                trace.showlegend = False
            else:
                unique_names.add(name)

        # Remove grids from both subplots
        fig.update_xaxes(showgrid=False, row=1, col=1)
        fig.update_xaxes(showgrid=False, row=2, col=1)
        fig.update_yaxes(showgrid=False, row=1, col=1)
        fig.update_yaxes(showgrid=False, row=2, col=1)

        fig.update_xaxes(title_text="m/z", row=1, col=1)
        fig.update_xaxes(title_text="m/z", row=2, col=1)
        fig.update_yaxes(title_text="Intensity", row=1, col=1)
        fig.update_yaxes(title_text="Intensity", row=2, col=1)
        fig.update_layout(
            height=500,
            width=800,
            title_text=f"Spectra Points ({mz_start:.1f}–{mz_end:.1f} m/z)",
            margin=dict(t=60, b=10, l=10, r=10),
        )
        fig.show()

    return widgets.interact(plot_spectra_points, mz_center=mz_slider)


def plot_peak_assignment_results(
    matches: "pd.DataFrame",
    peaks: "pd.DataFrame",
    total_averaged_signal: dict,
    dmz: float = 0.01,
):
    """Plot interactive visualization of peak assignment results.

    :param matches: Matches dataframe with peak assignment results.
    :type matches: pd.DataFrame
    :param peaks: Peaks dataframe with detected peaks.
    :type peaks: pd.DataFrame
    :param total_averaged_signal: Averaged signal data containing m/z and intensity.
    :type total_averaged_signal: dict[str, np.ndarray]
    :param dmz: m/z window half-width for plotting around each isotope peak, defaults to 0.01
    :type dmz: float, optional
    :raises ValueError: If no monoisotopic (M0) rows are found in matches.
    :return: Interactive widget for selecting and plotting peak assignments.
    :rtype: widgets.VBox
    """
    # Dropdown: only monoisotopic (M0) rows
    m0_matches = (
        matches[matches.isotope_label == "M0"]
        .sort_values(by="mz")
        .reset_index(drop=False)  # keep original index in 'index'
    )

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

    def plot_selected_match(row_idx):
        fig_output.clear_output(wait=True)

        # Selected monoisotopic row
        sel_row = m0_matches.loc[row_idx]
        formula = sel_row["formula"]
        ion = sel_row["ion"]

        # All isotopes with the same formula (sorted by mz)
        isotopes_df = (
            matches[matches.formula == formula].sort_values("mz").reset_index(drop=True)
        )
        n_isotopes = len(isotopes_df)

        if n_isotopes == 0:
            return

        #  Find M0 peak intensity in peaks df
        m0_idx = (peaks["mz"] - sel_row["mz"]).abs().idxmin()
        m0_peak = peaks.loc[m0_idx]
        # Correct predicted intensities of isotopes by M0 for visualization
        isotopes_df["predicted_intensity"] *= m0_peak["intensity"]

        fig = make_subplots(
            rows=n_isotopes,
            cols=1,
            shared_xaxes=False,
        )

        mz_all = total_averaged_signal["mz"]
        intensity_all = total_averaged_signal["intensity"]

        for i, iso_row in isotopes_df.iterrows():
            mz_center = iso_row["mz"]
            mz_min = mz_center - dmz
            mz_max = mz_center + dmz

            # Windowed signal
            mask = (mz_all >= mz_min) & (mz_all <= mz_max)
            mz_win = mz_all[mask]
            intensity_win = intensity_all[mask]

            # Add signal trace
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
            nearest_idx = (peaks["mz"] - mz_center).abs().idxmin()
            nearest_peak = peaks.loc[nearest_idx]

            if abs(nearest_peak["mz"] - mz_center) <= dmz:
                # Vertical line of the detected peak
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
                # Marker of the detected peak
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
                # Annotation of the detected peak
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
