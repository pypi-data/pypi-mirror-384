"""
Module to plot artof data using plotly.
"""

from typing import Union

import numpy as np
from plotly import graph_objects as go


def get_axis_label(axis: str) -> str:
    """
    Build string for matplotlib axis label including Greek characters.

    Args:
        axis: String containing the axis label and unit separated by '_'.

    Returns:
        Formatted string for plotly.
    """

    name, unit = axis.split("_")
    match name:
        case "phi":
            name = "&#966;"
        case "theta":
            name = "&#977;"
    return f"{name} [{unit}]"


def plot_1d(
    fig: Union[go.FigureWidget, go.Figure],
    x_values: dict,
    y_value_wins: list,
    axes: list,
    proj_axes: list,
    photon_energy: float,
    height: int,
    title: Union[str, None] = None,
) -> None:
    """
    Plot spectrum evolution in 1D.

    Args:
        fig: figure object to plot on.
        x_values: x values for the plot.
        y_value_wins: Dictionary containing the y values for each window. .
        axes: List of axes.
        proj_axes: List of axes to project onto.
        photon_energy: If not None, the binding energy will be used for the x-axis.
        height: Height of plot.
        title: Title of the plot. Defaults to None.
    """

    # Create frames for each window
    n_frames = len(y_value_wins)  # Number of frames
    spectra = list(y_value_wins.values())
    frame_names = list(y_value_wins.keys())
    frames = [create_scatter_frame(x_values, spectra[t], frame_names[t]) for t in range(n_frames)]

    # show first frame
    fig.add_trace(frames[0].data[0])

    # set axis labels
    fig.update_layout(
        xaxis_title=get_axis_label(axes[proj_axes[0]]),
        yaxis_title="Counts",
    )

    # set title if provided
    if title is not None:
        fig.update_layout(title_text=title, title_x=0.5)

    # if more than one window is present show animation layout
    if len(y_value_wins) > 1:
        setup_animation_layout(fig, height, frame_names)
        fig.frames = frames

    if photon_energy is not None and includes_energy_axis(axes, proj_axes):
        fig.update_xaxes(autorange="reversed")
        fig.update_xaxes(title_text="Binding Energy [eV]")


def plot_2d(
    fig: Union[go.FigureWidget, go.Figure],
    z_value_wins: dict,
    x_edges: Union[np.ndarray, list],
    y_edges: Union[np.ndarray, list],
    axes: list,
    proj_axes: list,
    height: int,
    photon_energy: Union[float, None] = None,
    title: Union[str, None] = None,
) -> None:
    """
    Plot spectrum evolution in 2D.

    Args:
        fig: Figure object to plot on.
        z_value_wins: Dictionary containing the z values for each window.
        x_edges: x edges for the plot.
        y_edges: y edges for the plot.
        axes: List of axes.
        proj_axes: List of axes to project onto.
        photon_energy: If not None, the binding energy will be used for the x-axis.
        height: Height of plot.
        title: Title of the plot. Defaults to None.

    """

    # setup extent for image
    dx = x_edges[1] - x_edges[0]
    x0 = x_edges[0] + dx / 2
    dy = y_edges[1] - y_edges[0]
    y0 = y_edges[0] + dy / 2

    # Create frames for each window
    n_frames = len(z_value_wins)  # Number of frames
    spectra = list(z_value_wins.values())  # Spectral data for each frame
    frame_names = list(z_value_wins.keys())
    frames = [
        create_heatmap_frame(spectra[t], x0=x0, dx=dx, y0=y0, dy=dy, name=frame_names[t])
        for t in range(n_frames)
    ]

    # show first frame
    fig.add_trace(frames[0].data[0])

    # set axis labels
    fig.update_layout(
        xaxis_title=get_axis_label(axes[proj_axes[0]]),
        yaxis_title=get_axis_label(axes[proj_axes[1]]),
    )

    # set title if provided
    if title is not None:
        fig.update_layout(title_text=title, title_x=0.5)

    # if more than one window is present show animation layout
    if len(z_value_wins) > 1:
        setup_animation_layout(fig, height, frame_names)
        fig.frames = frames

    # invert energy axis if displayed in binding energy
    if photon_energy is not None and includes_energy_axis(axes, proj_axes):
        energy_idx = proj_axes.index(0)
        if energy_idx == 0:
            x0 = np.abs(x0 - photon_energy)
            dx = -dx
            fig.update_xaxes(autorange="reversed")
            fig.update_xaxes(title_text="Binding Energy [eV]")
        else:
            y0 = np.abs(y0 - photon_energy)
            dy = -dy
            fig.update_yaxes(autorange="reversed")
            fig.update_yaxes(title_text="Binding Energy [eV]")


def includes_energy_axis(axes: list, proj_axes: list) -> bool:
    """
    Check if the projection includes the energy axis.

    Args:
        axes: List of axes.
        proj_axes: List of projection axes.

    Returns:
        Boolean indicating if the projection includes the energy axis.
    """
    return 0 in proj_axes and "E_eV" in axes


def plot_counts(fig: go.FigureWidget, steps: list[int], counts: list[int], sum_iters: bool) -> None:
    """
    Plot counts.

    Args:
        fig: figure object to plot on.
        iterations: x values for the plot.
        counts: y values for the plot.
        sum_iters: If True, set xlabel to "Iterations", else set to "Steps".

    """
    xlabel = "Iterations" if sum_iters else "Steps"
    fig.update_layout(
        xaxis_title=xlabel, yaxis_title="Counts", title_text="Total counts", title_x=0.5
    )
    fig.add_scatter(x=steps, y=counts)


def update_subtitle(fig: go.Figure, subtitle: str) -> None:
    """
    Update the subtitle of the figure.

    Args:
        fig: Figure object to update.
        subtitle: Subtitle to set.

    """
    # get current title
    title = fig.layout.title.text
    # remove current subtitle
    title = title.split("<br>")[0]
    # set new title
    fig.update_layout(title_text=f"{title}<br><sup>{subtitle}</sup>")


def create_scatter_frame(x_values: list, y_values: list, name: str) -> go.Frame:
    """
    Create a scatter plot frame.

    Args:
        x_values: x values for the plot.
        y_values: y values for the plot.
        name: Name of the frame.

    Returns:
        Frame object containing the scatter plot.

    """
    # setup limits for scatter plot
    x_min = x_values[0]
    x_max = x_values[-1]
    y_span = y_values.max() - y_values.min()
    y_min = y_values.min() - 0.055 * y_span
    y_max = y_values.max() + 0.055 * y_span

    return go.Frame(
        data=[create_scatter(x_values, y_values)],
        name=name,
        layout=go.Layout(
            xaxis={"range": [x_min, x_max]},
            yaxis={"range": [y_min, y_max]},
        ),
    )


def create_scatter(x_values: list, y_values: list) -> go.Scatter:
    """
    Create a scatter plot.

    Args:
        x_values: x values for the plot.
        y_values: y values for the plot.

    Returns:
        Scatter plot from given data.

    """

    return go.Scatter(x=x_values, y=y_values, mode="lines", line={"color": "blue"})


def create_heatmap_frame(
    z_values: list,
    x0: Union[int | float],
    dx: Union[int | float],
    y0: Union[int | float],
    dy: Union[int | float],
    name: str,
) -> go.Frame:
    """
    Create a heatmap frame.

    Args:
        z_values: z values for the plot.
        x0: Lower x edge for the plot.
        dx: x step size for the plot.
        y0: Lower y edge for the plot.
        dy: y step size for the plot.
        name: Name of the frame.

    Returns:
        Frame object containing the heatmap.

    """

    return go.Frame(
        data=[create_heatmap(z_values, x0, dx, y0, dy)],
        name=name,
    )


def create_heatmap(
    z_values: list,
    x0: Union[int | float],
    dx: Union[int | float],
    y0: Union[int | float],
    dy: Union[int | float],
) -> go.Heatmap:
    """
    Create a heatmap.

    Args:
        z_values: z values for the plot.
        x0: Lower x edge for the plot.
        dx: x step size for the plot.
        y0: Lower y edge for the plot.
        dy: y step size for the plot.

    Returns:
        Heatmap from given data.

    """
    # other interesting colorscales: Electric, Terrain, Blackbody, Jet
    return go.Heatmap(colorscale="Viridis", z=z_values, x0=x0, dx=dx, y0=y0, dy=dy)


def setup_animation_layout(fig: go.Figure, height: int, frame_names: list[str]) -> None:
    """
    Setup layout for animation.

    Args:
        fig: figure object to plot on.
        height: Height of plot.
        frame_names: List of frame names.

    Raises:
        ValueError: If the figure is a FigureWidget. Animations only work with Figure.
    """
    # throw error if figure is a FigureWidget
    if isinstance(fig, go.FigureWidget):
        raise ValueError("FigureWidget cannot show animation. Use Figure instead.")

    fig.update_layout(
        updatemenus=[
            {
                "type": "buttons",
                "showactive": False,
                "buttons": [
                    {
                        "label": "▶",
                        "method": "animate",
                        "args": [
                            None,
                            {
                                "frame": {"duration": 100, "redraw": True},
                                "fromcurrent": True,
                                "mode": "immediate",
                                "transition": {"duration": 0},
                            },
                        ],
                    },
                    {
                        "label": "⏸",
                        "method": "animate",
                        "args": [
                            [None],
                            {
                                "frame": {"duration": 0, "redraw": False},
                                "mode": "immediate",
                                "transition": {"duration": 0},
                            },
                        ],
                    },
                ],
                "direction": "left",
                "pad": {"r": 10, "t": 87},
                "x": 0,  # button position
                "xanchor": "right",
                "y": 70 / height,  # button position
                "yanchor": "top",
            }
        ],
        sliders=[
            {
                "steps": [
                    {
                        "method": "animate",
                        "args": [
                            [name],
                            {
                                "frame": {"duration": 0, "redraw": True},
                                "mode": "immediate",
                                "transition": {"duration": 0},
                            },
                        ],
                        "label": f"{name}",
                    }
                    for name in frame_names
                ],
                "transition": {"duration": 0},
                "x": 0,  # slider position
                "y": 0,
                "currentvalue": {
                    "font": {"size": 12},
                    "prefix": "Window: ",
                    "visible": True,
                    "xanchor": "left",
                },
                "len": 1.0,  # Full width
            }
        ],
    )
