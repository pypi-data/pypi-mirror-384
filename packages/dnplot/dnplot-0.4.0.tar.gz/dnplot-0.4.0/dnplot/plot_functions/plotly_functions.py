import numpy as np
import pandas as pd
import xarray as xr
from scipy.stats import gaussian_kde
import os

from dash import Input, Output
from plotly.subplots import make_subplots
import plotly.express as px
import plotly.graph_objects as go

from threading import Timer
import webbrowser
import random
from flask import Flask
import cmocean.cm

from dnplot.stats import calculate_correlation, calculate_RMSE
from dnplot import sanitation
from dnplot.plot_functions import plotly_layout
from dnplot.draw_functions import plotly_draw
from dash import Dash, dcc, html


def open_browser(port):
    if not os.environ.get("WERKZEUG_RUN_MAIN"):
        webbrowser.open_new(f"http://127.0.0.1:{port}/")


def waveseries_plotter_basic(model, model1):
    xmodel = sanitation.force_to_ds(model)
    xdf = sanitation.xarray_to_dataframe(xmodel)
    ymodel = sanitation.force_to_ds(model1)
    if ymodel is not None:
        ydf = sanitation.xarray_to_dataframe(ymodel)

    if ymodel is not None:
        df = pd.merge(
            xdf.set_index("time").add_suffix(f" {xmodel.name}").reset_index(),
            ydf.set_index("time").add_suffix(f" {ymodel.name}").reset_index(),
            on="time",
        )
    else:
        df = xdf

    fig = go.Figure()

    variables = [col for col in df if col != "time"]
    for variable in variables:
        trace = go.Scatter(
            x=df["time"],
            y=df[variable],
            mode="lines",
            name=variable,
            visible="legendonly",
        )
        fig.add_trace(trace)

    fig.update_layout(title=f"{xmodel.name}", xaxis_title="UTC", yaxis_title="Values")
    fig.show()


def waveseries_plotter_dash(model, model1):
    lons, lats, names = {}, {}, {}
    xmodel_all = sanitation.force_to_ds(model)
    lons["a"], lats["a"] = xmodel_all.lon.values, xmodel_all.lat.values
    names["a"] = xmodel_all.name

    ymodel_all = sanitation.force_to_ds(model1)
    if ymodel_all is not None:
        lons["b"], lats["b"] = ymodel_all.lon.values, ymodel_all.lat.values
        names["b"] = ymodel_all.name

    app = plotly_layout.create_wave_data_layout(xmodel_all, ymodel_all)

    @app.callback(
        Output("data_chart", "figure"),
        Output("title", "children"),
        Output("map", "figure"),
        Input("dropdown1", "value"),
        Input("dropdown2", "value"),
        Input("xslider", "value"),
        Input("yslider", "value"),
        Input("map", "relayoutData"),
    )
    def display_time_series(var1, var2, ind_a, ind_b, relayout_data):
        __, __, df = sanitation.get_one_point_merged_dataframe(
            xmodel_all, ymodel_all, ind_a, ind_b
        )
        subfig = make_subplots()
        fig = px.line(df, x="time", y=var1)
        fig.data[0].name = var1
        subfig.add_trace(fig.data[0])
        subfig.data[-1].showlegend = True
        if var2 != "None":
            fig2 = px.line(df, x="time", y=var2)
            fig2.data[0].line.color = "red"
            fig2.data[0].name = var2
            subfig.add_trace(fig2.data[0])
            subfig.data[-1].showlegend = True

        # Remove name from var, 'hs NORA3' -> 'hs'
        title_var1 = var1.split(" ")[0]
        title_var2 = var2.split(" ")[0]

        if hasattr(xmodel_all[title_var1], "units"):
            unit1 = f" ({xmodel_all[title_var1].units})"
        else:
            unit1 = ""

        if title_var2 == "None":
            title_var2 = ""

        if names.get("b") is None:
            model = xmodel_all
        else:
            model = ymodel_all

        if title_var2 and hasattr(model[title_var2], "units"):
            unit2 = f" ({model[title_var2].units})"
        else:
            unit2 = ""

        if title_var1 == title_var2 or not title_var2:
            title_var = f"{title_var1}{unit1}"
        else:
            title_var = f"{title_var1}{unit1} / {title_var2}{unit2}"

        title_str = f"{names.get('a')} (lat: {lats.get('a')[ind_a]:.3f}, lon: {lons.get('a')[ind_a]:.3f})"
        if names.get("b") is not None:
            title_str += f"; {names.get('b')} (lat: {lats.get('b')[ind_b]:.3f}, lon: {lons.get('b')[ind_b]:.3f})"

        subfig.update_layout(
            xaxis_title="UTC",
            yaxis_title=title_var,
            title=title_str,
            margin=dict(l=0, r=0, t=50, b=50),
            showlegend=True,
            legend=dict(
                x=0.9,  # Position to the right
                y=1.0,  # Position at the top
                bgcolor="rgba(255, 255, 255, 0.5)",  # Transparent white background
                bordercolor="black",  # Border color of the legend
                borderwidth=1,  # Border width
            ),
        )

        fig = plotly_draw.draw_map(lons, lats, ind_a, ind_b, relayout_data, names)
        if names.get("b") is not None:
            title = f"{names.get('a')} and {names.get('b')} Waveseries"
        else:
            title = f"{names.get('a')} Waveseries"
        return subfig, title, fig

    port = random.randint(1000, 9999)
    Timer(1, open_browser, args=[port]).start()
    app.run(debug=False, port=port)


def waveseries_plotter(model, model1, plain: bool):
    if plain:
        waveseries_plotter_basic(model, model1)
    else:
        waveseries_plotter_dash(model, model1)


def scatter_plotter(model, model1):
    xmodel_all = sanitation.force_to_ds(model)
    xlon, xlat = xmodel_all.lon.values, xmodel_all.lat.values
    xname = xmodel_all.name
    ymodel_all = sanitation.force_to_ds(model1)
    if ymodel_all is None:
        ylon, ylat = None, None
        yname = None
    else:
        ylon, ylat = ymodel_all.lon.values, ymodel_all.lat.values
        yname = ymodel_all.name
    app = plotly_layout.create_wave_data_layout(
        xmodel_all, ymodel_all, set_y_start_val=True
    )

    @app.callback(
        Output("data_chart", "figure"),
        Output("title", "children"),
        Output("map", "figure"),
        Input("dropdown1", "value"),
        Input("dropdown2", "value"),
        Input("xslider", "value"),
        Input("yslider", "value"),
        Input("map", "relayoutData"),
    )
    def update_graph(xvar, yvar, inds_x, inds_y, relayout_data):
        __, __, df = sanitation.get_one_point_merged_dataframe(
            xmodel_all, ymodel_all, inds_x, inds_y
        )

        xdata, ydata = df[xvar].values, df[yvar].values
        RMSE = np.sqrt(np.mean((xdata - ydata) ** 2))
        R = np.corrcoef(xdata, ydata)[0, 1]
        SI = RMSE / np.mean(xdata) * 100
        xy = np.vstack([xdata, ydata])
        z = gaussian_kde(xy)(xy)

        if xvar not in df.columns or yvar not in df.columns:
            return go.Figure()

        # Add scatter
        xunit = sanitation.get_units(xmodel_all, xvar.split(" ")[0])
        if ymodel_all is not None:
            yunit = sanitation.get_units(ymodel_all, yvar.split(" ")[0])
        else:
            yunit = sanitation.get_units(xmodel_all, yvar.split(" ")[0])
        fig = px.scatter(
            df,
            x=xvar,
            y=yvar,
            color=z,
            color_continuous_scale="blues",
            labels={xvar: f"{xvar} ({xunit})", yvar: f"{yvar} ({yunit})"},
        )

        # Lines
        x_values = np.linspace(0, np.ceil(np.max(xdata)), 100)

        slope, intercept = np.polyfit(xdata, ydata, 1)
        fig.add_traces(
            go.Scatter(
                x=x_values,
                y=x_values * slope + intercept,
                mode="lines",
                name="Linear regression",
                visible=True,
            )
        )

        fig.add_traces(
            go.Scatter(
                x=x_values, y=x_values, mode="lines", name="x=y", visible="legendonly"
            )
        )

        a = np.mean(ydata) / np.mean(xdata)
        fig.add_traces(
            go.Scatter(
                x=x_values,
                y=a * x_values,
                mode="lines",
                name="one-parameter-linear regression",
                visible="legendonly",
            )
        )

        maxval = np.maximum(np.max(xdata), np.max(ydata))
        fig.update_layout(yaxis=dict(range=[0, maxval]), xaxis=dict(range=[0, maxval]))

        xvarname = sanitation.get_varname(xmodel_all, xvar.split(" ")[0])
        if ymodel_all is not None:
            yvarname = sanitation.get_varname(ymodel_all, yvar.split(" ")[0])
        else:
            yvarname = sanitation.get_varname(xmodel_all, yvar.split(" ")[0])

        text = [f"N={len(xdata)}"]
        if xunit == yunit:
            text.append(f"Bias={np.mean(xdata)-np.mean(ydata):.2f}{xunit}")
            text.append(f"RMSE={RMSE:.2f}{xunit}")
            text.append(f"SI={SI:.0f}%")
        text.append(f"r={R:.2f}")
        text = "; ".join(text)

        fig.update_layout(
            coloraxis_colorbar=dict(title="Density", y=0.45, x=1.015, len=0.9),
            annotations=[
                dict(
                    x=0.001,
                    y=0.995,
                    xref="paper",
                    yref="paper",
                    text=text,
                    showarrow=False,
                    font=dict(size=16, color="black"),
                    align="left",
                    bgcolor="white",
                    borderpad=4,
                    bordercolor="black",
                    opacity=0.55,
                )
            ],
        )

        fig.update_layout(width=800, height=800, margin=dict(l=0, r=0, t=40, b=0))

        mapfig = plotly_draw.draw_map(
            xlon, xlat, ylon, ylat, inds_x, inds_y, relayout_data, xname, yname
        )

        if yname is not None:
            title = f"{xname} and {yname} scatter"
        else:
            title = f"{xname} scatter"

        return fig, title, mapfig

    port = random.randint(1000, 9999)
    Timer(1, open_browser, args=[port]).start()
    app.run(debug=False, port=port)


def spectra_plotter(model, model1):
    spectra, spectra1d, lons, lats, names = {}, {}, {}, {}, {}

    spectra["a"] = model.spectra()
    spectra1d["a"] = model.spectra1d()

    if spectra["a"] is None and spectra1d["a"] is None:
        raise ValueError(
            "The primary data needs to have either a spectra or a spectra1d!"
        )

    if model1:
        spectra["b"] = model1.spectra()
        spectra1d["b"] = model1.spectra1d()

    if spectra.get("a") and spectra.get("b"):
        spectra["a"], spectra["b"] = spectra["a"].cut_to_common_times(spectra["b"])

    if spectra1d.get("a") and spectra1d.get("b"):
        spectra1d["a"], spectra1d["b"] = spectra1d["a"].cut_to_common_times(
            spectra1d["b"]
        )

    number_of_1d_plots = 0
    number_of_2d_plots = 0

    if spectra1d.get("a") or spectra1d.get("b"):
        number_of_1d_plots += 1

    if spectra.get("a"):
        spectra.get("a").set_convention("ocean")
        number_of_2d_plots += 1

    if spectra.get("b"):
        spectra.get("b").set_convention("ocean")
        number_of_2d_plots += 1

    if spectra.get("a"):
        lo, la = spectra["a"].lonlat()
        lons["a"] = lo
        lats["a"] = la
        times = spectra["a"].time(datetime=False)
        names["a"] = spectra["a"].name
    else:
        lo, la = spectra1d["a"].lonlat()
        lons["a"] = lo
        lats["a"] = la
        times = spectra1d["a"].time(datetime=False)
        names["a"] = spectra1d["a"].name

    if spectra.get("b"):
        lo, la = spectra["b"].lonlat()
        lons["b"] = lo
        lats["b"] = la
        names["b"] = spectra["b"].name
    elif spectra1d.get("b"):
        lo, la = spectra1d["b"].lonlat()
        lons["b"] = lo
        lats["b"] = la
        names["b"] = spectra1d["b"].name

    app = Dash(__name__)

    app.layout = plotly_layout.create_spectra_app_layout(
        len_of_inds=len(lons.get("a")),
        len_of_inds_B=len(lons.get("b", [])),
        len_of_times=len(times),
        number_of_1d_plots=number_of_1d_plots,
        number_of_2d_plots=number_of_2d_plots,
        name=names.get("a"),
        name_B=names.get("b"),
    )

    outputs = [
        Output("title", "children"),
        Output("smaller_title", "children"),
        Output("spectra_map", "figure"),
    ]

    if number_of_1d_plots == 1:
        outputs.append(Output("1d_graph", "figure"))
    if number_of_2d_plots > 0:
        outputs.append(Output("2d_graph1", "figure"))
    if number_of_2d_plots > 1:
        outputs.append(Output("2d_graph2", "figure"))

    @app.callback(
        outputs,
        [
            Input("time_slider", "value"),
            Input("inds_slider", "value"),
            Input("inds_slider_B", "value"),
            Input("spectra_map", "relayoutData"),
        ],
    )
    def display_spectra(ind_time, ind_a, ind_b, relayout_data):
        inds = {"a": ind_a, "b": ind_b}
        spectra_map = plotly_draw.draw_map(
            lons, lats, ind_a, ind_b, relayout_data, names
        )

        graphs = {}
        for key in ["a", "b"]:
            spec = spectra.get(key)
            if spec is not None:
                spec1 = spec.spec(squeeze=False)[:, inds.get(key), :, :].flatten()
                graphs[f"spectra_{key}"] = plotly_draw.draw_plotly_graph_spectra(
                    freq=spec.freq(),
                    spec=spec.spec(squeeze=False)[
                        ind_time, inds.get(key), :, :
                    ].flatten(),
                    dirs=spec.dirs(),
                    cmin=np.min(spec1),
                    cmax=np.max(spec1),
                )

                graphs[f"spectra_{key}"].update_layout(
                    # width=800,
                    # height=800,
                    margin=dict(l=0, r=0, t=50, b=0),
                    title=dict(
                        text=f"{names.get(key)}\n{times[ind_time]}; lat={lats.get(key)[inds.get(key)]:.4f}, lon={lons.get(key)[inds.get(key)]:.4f}",  # The title text
                        font=dict(size=18),  # Font size for the title
                        x=0.5,  # Center the title horizontally (0 = left, 1 = right)
                        y=1,  # Position the title near the top of the plot
                        xanchor="center",  # Anchor the title horizontally by its center
                        yanchor="top",  # Anchor the title vertically by its top
                    ),
                )

        maxdir, mindir = None, None
        maxdir_B, mindir_B = None, None
        max_ef = 0
        title_text = f"{times[ind_time]}"
        smaller_title_text = ""
        fig = None
        for key in ["a", "b"]:
            spec = spectra1d.get(key)
            if spec is not None:
                spec1d = spec.spec(squeeze=False)[:, inds.get(key), :].flatten()
                max_ef = np.maximum(max_ef, np.max(spec1d))
                dirm = (
                    spec.dirm(dir_type="to", squeeze=False)[ind_time, inds.get(key), :]
                    if spec.dirm() is not None
                    else None
                )
                spr = (
                    spec.spr(squeeze=False)[ind_time, inds.get(key), :]
                    if spec.spr() is not None
                    else None
                )
                fig = graphs[f"spectra1d"] = plotly_draw.draw_plotly_graph_spectra1d(
                    freq=spec.freq(),
                    spec=spec.spec(squeeze=False)[ind_time, inds.get(key), :],
                    dirm=dirm,
                    spr=spr,
                    name=names.get(key),
                    fig=fig,
                )
                maxdir = dirm
                mindir = dirm
                if spr is not None and maxdir is not None:
                    maxdir = maxdir + spr
                    mindir = mindir - spr
                smaller_title_text += f" {names.get(key)} ({lons.get(key)[inds.get(key)]:.4f}, {lats.get(key)[inds.get(key)]:.4f}) "

        # if maxdir_B is not None:
        #     maxdir = np.ceil(np.maximum(np.nanmax(maxdir), np.nanmax(maxdir_B))/10)*10+10
        # else:
        #     maxdir = np.ceil(np.nanmax(maxdir)/10)*10+10

        # if mindir_B is not None:
        #     mindir = np.floor(np.minimum(np.nanmin(mindir), np.nanmin(mindir_B))/10)*10-10
        # else:
        #     mindir = np.floor(np.nanmin(mindir)/10)*10-10
        spectra_map.update_layout(
            title=dict(
                text="Locations",
                font=dict(size=18),  # Font size for the title
                x=0.5,  # Center the title horizontally (0 = left, 1 = right)
                y=1,  # Position the title near the top of the plot
                xanchor="center",  # Anchor the title horizontally by its center
                yanchor="top",  # Anchor the title vertically by its top
            ),
        )
        graphs["spectra1d"].update_layout(
            title=dict(
                text=title_text + " " + smaller_title_text,
                font=dict(size=18),  # Font size for the title
                x=0.5,  # Center the title horizontally (0 = left, 1 = right)
                y=1,  # Position the title near the top of the plot
                xanchor="center",  # Anchor the title horizontally by its center
                yanchor="top",  # Anchor the title vertically by its top
            ),
            xaxis_title=f"Frequencyn (Hz)",
            yaxis=dict(
                title=f"Spectral density\n E(f) (m^2/Hs/rad)",
                range=[0, max_ef * 1.1],
            ),
            yaxis2=dict(
                title=f"Mean wave direction\n (deg to)",
                overlaying="y",
                side="right",
                range=[mindir, maxdir],
            ),
            # width=800,
            # height=500,
            margin=dict(l=0, r=0, t=50, b=0),
        )

        if number_of_1d_plots == 1:
            if number_of_2d_plots == 0:
                return (
                    title_text,
                    smaller_title_text,
                    spectra_map,
                    graphs.get("spectra1d"),
                )
            elif number_of_2d_plots == 1:
                graph_2d = graphs.get("spectra_a") or graphs.get("spectra_b")
                return (
                    title_text,
                    smaller_title_text,
                    spectra_map,
                    graphs.get("spectra1d"),
                    graph_2d,
                )
            else:
                return (
                    title_text,
                    smaller_title_text,
                    spectra_map,
                    graphs.get("spectra1d"),
                    graphs.get("spectra_a"),
                    graphs.get("spectra_b"),
                )
        else:
            if number_of_2d_plots == 1:
                graph_2d = graphs.get("spectra_a") or graphs.get("spectra_b")
                return title_text, smaller_title_text, spectra_map, graph_2d
            else:
                return (
                    title_text,
                    smaller_title_text,
                    spectra_map,
                    graphs.get("spectra_a"),
                    graphs.get("spectra_b"),
                )

    port = random.randint(1000, 9999)
    Timer(1, open_browser, args=[port]).start()
    app.run(debug=False, port=port)
