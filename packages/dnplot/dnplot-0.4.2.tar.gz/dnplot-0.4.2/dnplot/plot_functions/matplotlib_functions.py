import xarray as xr
import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde

from matplotlib.colors import Normalize
import cmocean.cm
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider

from dnplot import sanitation
from dnplot.stats import calculate_RMSE, calculate_correlation
from dnplot.defaults import default_variable, DEFAULT_VARIABLE_DATA
from dnplot.draw_functions import draw


def grid_plotter(fig_dict: dict, data_dict: dict, coastline: bool = None) -> dict:
    """Plot the depth information and land mask. Also plots information about e.g. wind data and spectral points"""
    fig_dict = topo_plotter(fig_dict, data_dict, coastline=coastline)
    fig_dict = draw.draw_nested_grid_box(fig_dict, data_dict)
    fig_dict = draw.draw_masked_points(
        fig_dict, data_dict.get("grid"), masks_to_plot=["boundary", "output"]
    )
    fig_dict = draw.draw_object_points(
        fig_dict,
        data_dict,
        objects_to_plot=["wind", "current", "ice", "spectra", "waveseries"],
    )
    return fig_dict


def topo_plotter(fig_dict: dict, data_dict: dict, coastline: bool = None) -> dict:
    """Plot the depth information and land mask"""
    grid = data_dict.get("grid")
    sea_mask = grid.get("sea_mask")
    if sea_mask is None or np.all(sea_mask):
        contour = False
    else:
        contour = True

    fig_dict = draw.draw_gridded_magnitude(
        fig_dict,
        grid.x(native=True),
        grid.y(native=True),
        grid.topo(),
        cmap=default_variable["topo"]["cmap"],
        contour=contour,
    )
    if grid.is_gridded():
        fig_dict = draw.draw_mask(fig_dict, grid, mask_to_plot="land")

    if coastline is None and not contour:
        # This has been gicen by the draw_gridded_magnitude
        # If we have used pcolor it is false, if contour it is true
        # Don't do this if we have just requested a countour plot
        coastline = fig_dict.get("want_coastline", False)

    if coastline:
        fig_dict = draw.draw_coastline(fig_dict)

    fig_dict["ax"].set_xlabel(grid.core.x_str)
    fig_dict["ax"].set_ylabel(grid.core.y_str)
    fig_dict["cbar"].set_label("Depth [m]")
    fig_dict["ax"].set_title(f"{grid.name} {grid.ds().attrs.get('source', '')}")

    return fig_dict


def wavegrid_plotter(
    fig_dict: dict,
    data_dict: dict,
    data_var: str,
    coastline: bool = None,
    contour: bool = False,
) -> dict:
    def update_plot(val):
        nonlocal fig_dict
        nonlocal figure_initialized

        nonlocal plotting_data
        nonlocal coastline
        nonlocal contour

        fig_dict = draw.draw_gridded_magnitude(
            fig_dict,
            obj.x(native=True),
            obj.y(native=True),
            obj.get(data_var, squeeze=False)[val, :, :],
            vmax=np.nanmax(obj.get(data_var)),
            vmin=0,
            cmap=plotting_data["cmap"],
            contour=contour,
        )
        if coastline is None:
            # This has been gicen by the draw_gridded_magnitude
            # If we have used pcolor it is false, if contour it is true
            coastline = fig_dict.get("want_coastline", False)
        if coastline:
            fig_dict = draw.draw_coastline(fig_dict)

        fig_dict["ax"].set_title(f"{obj.time(datetime=False)[val]} {obj.name}")
        figure_initialized = True

    obj = data_dict["wavegrid"]
    plotting_data = default_variable.get(data_var, DEFAULT_VARIABLE_DATA)

    figure_initialized = False
    if len(obj.time()) > 1:
        ax_slider = plt.axes([0.17, 0.05, 0.65, 0.03])
        time_slider = Slider(
            ax_slider, "time_index", 0, len(obj.time()) - 1, valinit=0, valstep=1
        )
        time_slider.on_changed(update_plot)

    update_plot(0)
    fig_dict["ax"].set_xlabel(obj.core.x_str)
    fig_dict["ax"].set_ylabel(obj.core.y_str)

    # Try to determine name and units
    std_name = plotting_data.get("name")
    unit = plotting_data.get("unit")

    metaparam = obj.core.meta_parameter(data_var)
    if metaparam is not None:
        std_name = std_name or metaparam.standard_name()
        unit = unit or metaparam.units()

    fig_dict["cbar"].set_label(f"{std_name} [{unit}]")
    plt.show(block=True)
    return fig_dict


def directional_data_plotter(
    fig_dict: dict,
    data_dict: dict,
    obj_type: str,
    coastline: bool = None,
    contour: bool = False,
    test_mode: bool = False,
) -> dict:
    def update_plot(val):
        nonlocal fig_dict
        nonlocal figure_initialized
        nonlocal coastline
        fig_dict = draw.draw_gridded_magnitude(
            fig_dict,
            obj.x(native=True),
            obj.y(native=True),
            obj.mag(squeeze=False)[val, :, :],
            vmax=np.nanmax(obj.mag()),
            vmin=0,
            cmap=default_variable[obj_type]["cmap"],
            contour=contour,
        )
        if coastline is None:
            # This has been gicen by the draw_gridded_magnitude
            # If we have used pcolor it is false, if contour it is true
            coastline = fig_dict.get("want_coastline", False)
        if coastline:
            fig_dict = draw.draw_coastline(fig_dict)
        fig_dict = draw.draw_arrows(
            fig_dict,
            obj.x(native=True),
            obj.y(native=True),
            obj.u(squeeze=False)[val, :, :],
            obj.v(squeeze=False)[val, :, :],
        )
        # if not figure_initialized:
        #     masks_to_plot = ["output_mask"]
        #     fig_dict = draw.draw_masked_points(fig_dict, grid, masks_to_plot=masks_to_plot)
        #     fig_dict.get("ax").legend()
        fig_dict["ax"].set_title(f"{obj.time(datetime=False)[val]} {obj.name}")
        figure_initialized = True

    obj = data_dict[obj_type]
    # grid = data_dict["grid"]
    figure_initialized = False
    if len(obj.time()) > 1:
        ax_slider = plt.axes([0.17, 0.05, 0.65, 0.03])
        time_slider = Slider(
            ax_slider, "time_index", 0, len(obj.time()) - 1, valinit=0, valstep=1
        )
        time_slider.on_changed(update_plot)

    update_plot(0)
    fig_dict["ax"].set_xlabel(obj.core.x_str)
    fig_dict["ax"].set_ylabel(obj.core.y_str)

    # Try to determine name and units
    std_name = default_variable[obj_type].get("name")
    unit = default_variable[obj_type].get("unit")

    metaparam = obj.core.meta_parameter("mag")
    if metaparam is not None:
        std_name = std_name or metaparam.standard_name()
        unit = unit or metaparam.units()

    std_name = std_name or obj_type
    unit = unit or "?"

    fig_dict["cbar"].set_label(f"{std_name} [{unit}]")
    if not test_mode:
        plt.show(block=True)

    return fig_dict


def spectra_plotter(fig_dict: dict, model) -> dict:
    def update_plot(val):
        nonlocal fig_dict
        nonlocal figure_initialized
        fig_dict = draw.draw_polar_spectra(
            fig_dict,
            spectra.spec(squeeze=False)[sliders["time"].val, sliders["inds"].val, :, :],
            spectra.freq(),
            spectra.dirs(),
        )

        fig_dict["ax"].set_title(
            f"{spectra.time(datetime=False)[sliders['time'].val]} {spectra.name} \n Latitude={spectra.lat()[sliders['inds'].val]:.4f} Longitude={spectra.lon()[sliders['inds'].val]:.4f}"
        )
        figure_initialized = True

    spectra = model["spectra"]
    grid = model["grid"]
    figure_initialized = False
    sliders = {}
    if len(spectra.time()) > 1:
        ax_slider = plt.axes([0.17, 0.05, 0.65, 0.03])
        sliders["time"] = Slider(
            ax_slider, "time_index", 0, len(spectra.time()) - 1, valinit=0, valstep=1
        )
        sliders["time"].on_changed(update_plot)
    if len(spectra.inds()) > 0:
        ax_slider2 = plt.axes([0.17, 0.01, 0.65, 0.03])
        sliders["inds"] = Slider(
            ax_slider2, "inds_index", 0, len(spectra.inds()) - 1, valinit=0, valstep=1
        )
        sliders["inds"].on_changed(update_plot)
    update_plot(0)

    plt.show(block=True)

    return fig_dict


def waveseries_plotter(
    model, model1, var: list[str], lon: float, lat: float, separate_plots: bool
):
    """var = ['hs', 'tp'] or ['hs',('tp','tm01')]

    use 'separate_plots = True' to get separate figures for each parameter.
    Default is separate_plots = True for more than 4 parameters."""

    if separate_plots is None:
        separate_plots = len(var) > 4

    xmodel = sanitation.force_to_ds(model)
    ymodel = sanitation.force_to_ds(model1)

    xmodel = sanitation.cut_ds_to_one_point(xmodel, lon, lat)
    ymodel = sanitation.cut_ds_to_one_point(ymodel, lon, lat)

    if separate_plots:
        axes = []
        for i in range(len(var)):
            fig, ax = plt.subplots()
            axes.append(ax)

            fig.suptitle(
                f"lat: {np.atleast_1d(xmodel.lat)[0]:.4f}, lon: {np.atleast_1d(xmodel.lon)[0]:.4f}"
            )
    else:
        fig, axes = plt.subplots(len(var), 1)
        fig.suptitle(
            f"lat: {np.atleast_1d(xmodel.lat)[0]:.4f}, lon: {np.atleast_1d(xmodel.lon)[0]:.4f}"
        )
        axes = axes if len(var) > 1 else [axes]

    # Get a list of axes, keeping in mind that we can have twin axes if we give a tuple ('tp','tm01') in vars
    list_of_axes = []
    list_of_variables = []
    list_of_colors = []
    draw_legend = []
    for i, axe in enumerate(axes):
        list_of_axes.append(axe)
        if isinstance(var[i], tuple) or isinstance(var[i], list):
            list_of_axes.append(axe.twinx())
            if len(var[i]) > 2:
                raise ValueError(
                    f"Can give a maximum of 2 parameters to plot in same plot! ({var[i]})"
                )
            list_of_variables.append(var[i][0])
            list_of_variables.append(var[i][1])
            list_of_colors.append(("b", "r"))
            list_of_colors.append(("g", "m"))
            draw_legend.append(False)
            draw_legend.append(True)
        else:
            list_of_variables.append(var[i])
            list_of_colors.append(("b", "r"))
            draw_legend.append(True)

    lines, labels = [], []
    for v, a, c, lgnd in zip(
        list_of_variables, list_of_axes, list_of_colors, draw_legend
    ):
        ylabel_set = False
        for i, ts in enumerate([xmodel, ymodel]):
            if ts is not None:
                varname = sanitation.get_varname(ts, v)
                unit = sanitation.get_units(ts, v)

                if ts.get(v) is not None:
                    a.plot(
                        ts.get("time"),
                        ts.get(v).squeeze(),
                        color=c[i],
                        label=f"{ts.name} {v} ({unit})",
                    )

                    # Set it only once so we get the first color
                    if not ylabel_set:
                        a.set_ylabel(
                            f"{varname} ({unit})",
                            color=c[0],
                        )
                        ylabel_set = True

        # If not set, then set withouth data (then missing units etc.)
        if not ylabel_set:
            a.set_ylabel(
                f"{varname} ({unit})",
                color=c[0],
            )
        a.grid(True)

        # This is to handle twin axes correctly
        li, la = a.get_legend_handles_labels()
        lines += li
        labels += la
        if lgnd:
            a.legend(lines, labels)
            lines, labels = [], []

    plt.tight_layout()
    return {"fig": fig, "ax": axes}


def spectra1d_plotter(fig_dict: dict, model) -> dict:
    def update_plot(val):
        nonlocal fig_dict
        nonlocal figure_initialized
        ax = fig_dict["ax"]
        ax2 = fig_dict["ax2"]
        ax.cla()
        ax2.cla()
        dirm = None
        spr = None
        if spectra1d.dirm() is not None:
            dirm = spectra1d.dirm(squeeze=False)[
                sliders["time"].val, sliders["inds"].val, :
            ]
        if spectra1d.spr() is not None:
            spr = spectra1d.spr(squeeze=False)[
                sliders["time"].val, sliders["inds"].val, :
            ]

        fig_dict = draw.draw_graph_spectra1d(
            fig_dict,
            spectra1d.spec(squeeze=False)[sliders["time"].val, sliders["inds"].val, :],
            spectra1d.freq(),
            dirm,
            spr,
        )

        ax.set_ylim(
            0, np.nanmax(spectra1d.spec(squeeze=False)[:, sliders["inds"].val, :]) * 1.1
        )
        ax.set_title(
            f"{spectra1d.time(datetime=False)[sliders['time'].val]} {spectra1d.name} \n Latitude={spectra1d.lat()[sliders['inds'].val]:.4f} Longitude={spectra1d.lon()[sliders['inds'].val]:.4f}"
        )
        ax.set_xlabel("Frequency")
        ax.set_ylabel(
            f"{spectra1d.meta.get('spec').get('long_name')}\n {'E(f)'}", color="b"
        )
        ax2.set_ylim(0, np.nanmax(spectra1d.dirm()) * 1.1)
        ax2.set_ylabel(
            f"{spectra1d.meta.get('dirm').get('long_name')}\n {spectra1d.meta.get('dirm').get('units')}",
            color="g",
        )
        ax2.yaxis.set_label_position("right")
        ax2.yaxis.tick_right()
        ax.grid()
        figure_initialized = True

    spectra1d = model["spectra1d"]
    grid = model["grid"]
    figure_initialized = False
    sliders = {}
    if len(spectra1d.time()) > 1:
        ax_slider = plt.axes([0.17, 0.05, 0.65, 0.03])
        sliders["time"] = Slider(
            ax_slider, "time_index", 0, len(spectra1d.time()) - 1, valinit=0, valstep=1
        )
        sliders["time"].on_changed(update_plot)
    if len(spectra1d.inds()) > 0:
        ax_slider2 = plt.axes([0.17, 0.01, 0.65, 0.03])
        sliders["inds"] = Slider(
            ax_slider2, "inds_index", 0, len(spectra1d.inds()) - 1, valinit=0, valstep=1
        )
        sliders["inds"].on_changed(update_plot)
    update_plot(0)
    plt.show(block=True)
    return fig_dict


def scatter_plotter(
    fig_dict: dict, model, model1, xvar: str, yvar: str, lon: float, lat: float
):
    """Plots a scatter plot of data from two different objects"""

    xmodel = sanitation.force_to_ds(model)
    ymodel = sanitation.force_to_ds(model1)
    xmodel = sanitation.cut_ds_to_one_point(xmodel, lon, lat)
    ymodel = sanitation.cut_ds_to_one_point(ymodel, lon, lat)
    xunit = sanitation.get_units(xmodel, xvar)
    yunit = sanitation.get_units(ymodel, yvar)
    xvarname = sanitation.get_varname(xmodel, xvar)
    yvarname = sanitation.get_varname(ymodel, yvar)
    xdf = sanitation.xarray_to_dataframe(xmodel)
    ydf = sanitation.xarray_to_dataframe(ymodel)

    combined_df = pd.concat([xdf, ydf], axis=1)
    combined_df_cleaned = combined_df.dropna()

    xdf = combined_df_cleaned.iloc[:, : xdf.shape[1]].reset_index(drop=True)
    ydf = combined_df_cleaned.iloc[:, xdf.shape[1] :].reset_index(drop=True)

    xdata, ydata = xdf[xvar], ydf[yvar]

    # Statistics
    RMSE = np.sqrt(np.mean((xdata - ydata) ** 2))
    R = np.corrcoef(xdata, ydata)[0, 1]
    SI = RMSE / np.mean(xdata) * 100
    # Text on the figure
    text = [f"N={len(xdf)}"]
    if xunit == yunit:
        text.append(f"Bias={np.mean(xdata)-np.mean(ydata):.2f}{xunit}")
        text.append(f"RMSE={RMSE:.2f}{xunit}")
        text.append(f"SI={SI:.0f}%")
    text.append(f"r={R:.2f}")
    text = "\n".join(text)

    # color for scatter density
    xy = np.vstack([xdata, ydata])
    z = gaussian_kde(xy)(xy)
    norm = Normalize(vmin=z.min(), vmax=z.max())
    cmap = cmocean.cm.dense

    title = f"{xmodel.name} ({xvar}) vs {ymodel.name} ({yvar})"
    fig_dict["ax"].set_title(title, fontsize=14)
    cont = fig_dict["ax"].scatter(xdata, ydata, c=z, cmap=cmap, norm=norm, s=50)

    maxval = np.maximum(np.max(xdata), np.max(ydata))
    fig_dict["ax"].set_xlim([0, maxval])
    fig_dict["ax"].set_ylim([0, maxval])

    slope, intercept = np.polyfit(xdata, ydata, 1)
    x_range = np.linspace(0, np.ceil(np.max(xdata)), 100)
    fig_dict["ax"].plot(
        x_range, x_range, linewidth=1, color="k", linestyle="--", label="x=y"
    )

    sign = "+" if intercept >= 0 else "-"
    fig_dict["ax"].plot(
        x_range,
        slope * x_range + intercept,
        color="r",
        linewidth=2,
        label=f"Regression line y={slope:.2f}x{sign}{np.abs(intercept):.2f}",
    )
    slope_1p = np.mean(ydata) / np.mean(xdata)
    fig_dict["ax"].plot(
        x_range,
        x_range * slope_1p,
        linewidth=2,
        color="k",
        label=f"One parameter line y={slope_1p:.2f}x ",
    )

    fig_dict["ax"].set_xlabel(f"{xmodel.name} {xvarname}\n ({xunit})")
    fig_dict["ax"].set_ylabel(f"{ymodel.name} {yvarname}\n ({yunit})")

    # color bar
    cbar = plt.colorbar(cont, ax=fig_dict["ax"])
    cbar.set_label("Density", rotation=270, labelpad=15)

    props = dict(boxstyle="square", facecolor="white", alpha=0.6)
    ax = fig_dict["ax"]
    fig_dict["ax"].text(
        0.05,
        0.7,
        text,
        bbox=props,
        fontsize=10,
        transform=ax.transAxes,
        verticalalignment="top",
        horizontalalignment="left",
    )
    fig_dict["ax"].grid(linestyle="--")
    fig_dict["ax"].legend(loc="upper left")

    return fig_dict
