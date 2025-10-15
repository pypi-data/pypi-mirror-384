# Copyright 2025 Q-CTRL. All rights reserved.
#
# Licensed under the Q-CTRL Terms of service (the "License"). Unauthorized
# copying or use of this file, via any medium, is strictly prohibited.
# Proprietary and confidential. You may not use this file except in compliance
# with the License. You may obtain a copy of the License at
#
#    https://q-ctrl.com/terms
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS. See the
# License for the specific language.

from boulderopalscaleupsdk.plotting import (
    HeatmapData,
    HistogramData,
    HistogramPlot,
    LinePlot,
    Plot,
    PlotConfig,
    PlotData1D,
    PlotReport,
)
from plotly import graph_objects as go

_LIGHT_STYLE_COLORS = [
    "#680CE9",
    "#FF4242",
    "#0DBA9A",
    "#F3B435",
    "#E55285",
    "#2B95ED",
    "#DE6B08",
    "#32B84B",
]

_DARK_STYLE_COLORS = [
    "#896BF5",
    "#FF8A8A",
    "#4DE0C3",
    "#F8D859",
    "#FA89B2",
    "#5DB9FE",
    "#FD8535",
    "#79E289",
]


def _create_color_map(colors: list[str], positions: list[float] | None = None) -> list[list]:
    """
    Create a color map from the given colors.
    """

    def _hex_to_rgb(h: str) -> tuple[int, ...]:
        return tuple(int(h[i : i + 2], 16) for i in (1, 3, 5))

    if positions is None:
        positions = [index / (len(colors) - 1) for index in range(len(colors))]

    assert len(positions) == len(colors), "Positions and colors must have the same length."

    return [
        [position, f"rgb{_hex_to_rgb(color)}"]
        for position, color in zip(positions, colors, strict=False)
    ]


_SEQUENTIAL_COLORS = ["#FFFFFF", "#E5DBFF", "#AB8DFB", "#680CE9", "#44108E"]
_SEQUENTIAL_COLOR_MAP = _create_color_map(_SEQUENTIAL_COLORS)

_DIVERGENT_COLORS = ["#D02323", "#FF8A8A", "#FFC2C2", "#FFFFFF", "#D0BFFF", "#AB8DFB", "#680CE9"]
_DIVERGENT_COLOR_MAP = _create_color_map(_DIVERGENT_COLORS)


class Plotter:
    """
    A class used to create and manage plots using Plotly.

    Parameters
    ----------
    data : Plot
        The data to be plotted.
    dark_mode : bool, optional
        Whether to use dark mode for the plot. Defaults to True.

    Attributes
    ----------
    figure : go.Figure
        The Plotly figure object.
    """

    def __init__(self, data: Plot, dark_mode: bool = True):
        self._plot_count = 0

        self._fig: go.Figure = go.Figure()
        if dark_mode:
            self._color_palette = _DARK_STYLE_COLORS
            self._fig.update_layout(
                font_color="white",
                title_font_color="white",
                legend_title_font_color="white",
                xaxis_gridcolor="black",
                yaxis_gridcolor="black",
                xaxis_zerolinecolor="black",
                yaxis_zerolinecolor="black",
                plot_bgcolor="#222222",
                paper_bgcolor="#111111",
            )
        else:
            self._color_palette = _LIGHT_STYLE_COLORS

        match data:
            case LinePlot():
                self._create_line_plot(data)
            case HistogramPlot():
                self._create_histogram_plot(data)
            case _:
                raise TypeError(f"Unsupported plot type: {data.plot_type}.")

    def _set_size(self):
        self._fig.update_layout(autosize=False, width=800, height=600)

    def _get_color(self, color_index: int | None = None):
        """
        Return a color from the palette.
        Use the provided color index or use the plot count if none is provided.
        """
        if color_index is None:
            color_index = self._plot_count
        self._plot_count += 1
        return self._color_palette[color_index % len(self._color_palette)]

    def _add_1d_data(self, data: PlotData1D):
        color = self._get_color(data.color_index)
        match data.style:
            case "scatter":
                mode = "markers"
                marker: dict[str, str] = {"color": color}
                line: dict[str, str] = {}
            case "dash" | "solid":
                mode = "lines"
                marker = {}
                line = {"color": color, "dash": data.style}
        self._fig.add_trace(
            go.Scatter(
                x=data.x,
                y=data.y,
                error_x={"type": "data", "array": data.x_error, "visible": True},
                error_y={"type": "data", "array": data.y_error, "visible": True},
                name=data.label,
                mode=mode,
                line=line,
                marker=marker,
                showlegend=data.label is not None,
            ),
        )

    def _add_heatmap(self, data: HeatmapData, default_name: str | None):
        text = None
        texttemplate = None
        if data.heatmap_text:
            text = [[f"{val:.2f}" for val in row] for row in data.z]
            texttemplate = "%{text}"

        match data.color_map:
            case "sequential":
                colorscale = _SEQUENTIAL_COLOR_MAP
            case "divergent":
                colorscale = _DIVERGENT_COLOR_MAP

        self._fig.add_heatmap(
            x=data.x,
            y=data.y,
            z=data.z.T,
            text=text,
            texttemplate=texttemplate,
            colorbar={"y": 0, "yanchor": "bottom", "len": 0.6, "title": data.label or default_name},
            colorscale=colorscale,
        )

    def _add_histogram(self, histogram_data: HistogramData, default_name: str | None):
        self._fig.add_trace(
            go.Histogram(
                x=histogram_data.data,
                name=histogram_data.label or default_name,
                opacity=histogram_data.opacity,
                marker_color=self._get_color(histogram_data.color_index),
                showlegend=(histogram_data.label or default_name) is not None,
            ),
        )

    def _set_axis_labels(self, x_label: str, y_label: str):
        self._fig.update_layout(xaxis_title=x_label, yaxis_title=y_label)

    def _set_title(self, title: str, subtitle: str | None):
        self._fig.update_layout(title=f"{title}<br>{subtitle}" if subtitle is not None else title)

    def _add_report(self, report: PlotReport):
        self._fig.add_annotation(
            text=f"[ {report.title} ]",
            x=1,
            y=-0.1,
            xanchor="right",
            yanchor="top",
            showarrow=False,
            hovertext=report.text.replace("\n", "<br>"),
            yref="paper",
            xref="paper",
        )

    def _create_base_plot(self, config: PlotConfig) -> None:
        self._set_title(config.title, config.subtitle)
        self._set_axis_labels(x_label=config.x_label, y_label=config.y_label)

        if config.report is not None:
            self._add_report(config.report)

        self._fig.update_xaxes(range=config.x_bounds)
        self._fig.update_yaxes(range=config.y_bounds)

        if config.axes_ratio is not None:
            self._fig.update_yaxes(scaleanchor="x", scaleratio=config.axes_ratio)

        if config.x_ticks is not None:
            self._fig.update_xaxes(tickvals=config.x_ticks.values, ticktext=config.x_ticks.labels)
        if config.y_ticks is not None:
            self._fig.update_yaxes(tickvals=config.y_ticks.values, ticktext=config.y_ticks.labels)

        if config.reverse_yaxis:
            self._fig.update_yaxes(autorange="reversed")

        self._set_size()

    def _create_line_plot(self, data: LinePlot) -> None:
        self._create_base_plot(data.config)

        # Add heatmap.
        if data.heatmap is not None:
            self._add_heatmap(data=data.heatmap, default_name="Experimental 2D data")

        for line in data.lines:
            self._add_1d_data(data=line)

        # Add markers.
        for marker in data.markers:
            self._fig.add_trace(
                go.Scatter(
                    x=[marker.x],
                    y=[marker.y],
                    mode="markers",
                    name=marker.label,
                    marker={"symbol": marker.symbol, "size": 10, "color": marker.color},
                    showlegend=marker.label is not None,
                ),
            )

        # Add vertical lines.
        for vline in data.vlines:
            self._fig.add_vline(vline.value, line={"dash": vline.line_dash, "color": vline.color})

    def _create_histogram_plot(self, data: HistogramPlot) -> None:
        self._create_base_plot(data.config)

        for idx, histogram in enumerate(data.histograms):
            self._add_histogram(histogram_data=histogram, default_name=f"Dataset {idx + 1}")

        for vline in data.vlines:
            self._fig.add_vline(vline.value, line={"dash": vline.line_dash, "color": vline.color})

        self._fig.update_layout(barmode="overlay")

    @property
    def figure(self) -> go.Figure:
        return self._fig
