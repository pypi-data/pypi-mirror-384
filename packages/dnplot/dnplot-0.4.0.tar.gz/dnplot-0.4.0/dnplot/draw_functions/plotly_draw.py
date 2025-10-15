import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def draw_plotly_graph_spectra1d(freq, spec, dirm, spr, name: str, fig=None):
    if fig is None:
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        color1 = "black"
        color2 = "blue"
    else:
        color1 = "red"
        color2 = "magenta"
    fig.add_trace(
        go.Scatter(
            x=freq,
            y=spec,
            mode="lines",
            name=f"{name} Spec (m<sup>2</sup>s)",
            line=dict(color=color1),
        ),
        secondary_y=False,
    )
    if dirm is not None:
        fig.add_trace(
            go.Scatter(
                x=freq,
                y=dirm,
                name=f"{name} dirm (deg to)",
                mode="lines",
                line=dict(color=color2, dash="dash"),
            ),
            secondary_y=True,
        )
        if spr is not None:
            fig.add_trace(
                go.Scatter(
                    x=freq,
                    y=dirm - spr,
                    name=f"{name} spr- (deg)",
                    line=dict(color=color2, dash="dot"),
                ),
                secondary_y=True,
            )
            fig.add_trace(
                go.Scatter(
                    x=freq,
                    y=dirm + spr,
                    name=f"{name} spr+ (deg)",
                    line=dict(color=color2, dash="dot"),
                ),
                secondary_y=True,
            )
    fig.update_yaxes(secondary_y=True, showgrid=False, range=[0, 360])
    return fig


def draw_plotly_graph_spectra(freq, spec, dirs, cmax, cmin):

    fig = go.Figure(
        go.Barpolar(
            r=freq.repeat(len(dirs)),
            theta=np.tile(dirs, len(freq)),
            width=[14.7] * len(np.tile(dirs, len(freq))),
            marker=dict(
                color=spec.flatten(),
                colorscale="Blues",
                cmin=cmin,
                cmax=cmax,
                colorbar=dict(
                    title={"text": "m<sup>2</sup>s", "side": "bottom"},
                    ticks="outside",
                    len=0.3,
                    orientation="h",  # Set the colorbar to be horizontal
                    y=-0.2,  # Position the colorbar to the left of the plot
                    x=0.5,  # Center the colorbar vertically
                    xanchor="center",  # Anchor the colorbar by its right edge
                    yanchor="top",  # Anchor the colorbar vertically at the center
                ),
            ),
        )
    )

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                tickmode="array",
                tickvals=[0, 1, 2, 3, 4, 5],
                ticktext=[0, 0.1, 0.2, 0.3, 0.4, 0.5],
            ),
            angularaxis=dict(visible=True, rotation=90, direction="clockwise"),
        ),
    )
    return fig


def draw_map(
    lons: dict[str, np.ndarray],
    lats: dict[str, np.ndarray],
    ind_a: int,
    ind_b: int,
    relayout_data,
    names: dict[str, str],
):
    """Create a map with point plotted on top with activated point highlighted"""
    fig = go.Figure()
    fig.add_trace(
        go.Scattermapbox(
            lat=lats.get("a"),
            lon=lons.get("a"),
            mode="markers",
            marker=dict(
                size=18,
                color=[
                    "blue" if i == ind_a else "darkblue"
                    for i in range(len(lats.get("a")))
                ],
            ),
            name=names.get("a"),
        )
    )
    if lats.get("b") is not None:
        fig.add_trace(
            go.Scattermapbox(
                lat=lats.get("b"),
                lon=lons.get("b"),
                mode="markers",
                marker=dict(
                    size=10,
                    color=[
                        "red" if i == ind_b else "darkred"
                        for i in range(len(lats.get("b")))
                    ],
                ),
                name=names.get("b"),
            )
        )

    # Default values for zoom and center
    zoom = 5
    center = dict(lat=np.mean(lats.get("a")), lon=np.mean(lons.get("a")))

    # Extract zoom and center from relayoutData if available
    if relayout_data:
        zoom = relayout_data.get("mapbox.zoom", zoom)
        center = relayout_data.get("mapbox.center", center)

    fig.update_layout(
        mapbox=dict(
            style="carto-positron",
            zoom=zoom,
            center=center,
        ),
        width=850,
        height=850,
        margin=dict(l=100, r=100, t=50, b=100),
    )

    return fig
