import matplotlib.pyplot as plt
from cartopy import crs as ccrs
from ..plot_functions import matplotlib_functions
from ..plot_functions import plotly_functions
from typing import Callable


def create_file_string(model, obj_str: str, prefix: str) -> str:
    """Creates a string for a filename based on the object that is given.
    Object can be given directly, or as a part of a ModelRun or data_dict"""
    obj = model.get(obj_str) or model
    return f"dnora_{prefix}_{obj.name}.png"


def show_or_save_fig(
    fig_dict: dict,
    model,
    obj_str: str,
    test_mode: bool,
    save_fig: bool,
    filename: str,
    prefix: str = None,
) -> None:
    """Eitiher shows the figure or saves it with a specified filename"""
    prefix = prefix or obj_str
    if not test_mode:
        if save_fig:
            filename = filename or create_file_string(model, obj_str, prefix)
            print(f">>> {filename}")
            fig_dict.get("fig").savefig(filename, bbox_inches="tight", dpi=300)
        else:
            plt.show(block=True)


class Matplotlib:
    def __init__(self, data_dict: dict, data_dict2: dict = None):
        self.data_dict = data_dict
        self.data_dict2 = data_dict2 or {}

    def wavegrid(
        self,
        data_var: str,
        plotter: Callable = matplotlib_functions.wavegrid_plotter,
        coastline: bool = None,
        contour: bool = False,
        test_mode: bool = False,
        save_fig: bool = False,
        filename: str = None,
    ):
        fig, ax = plt.subplots(subplot_kw={"projection": ccrs.PlateCarree()})
        gl = ax.gridlines(
            crs=ccrs.PlateCarree(),
            draw_labels=True,
            color="gray",
            alpha=0.5,
            linestyle="--",
        )
        gl.top_labels = None
        gl.right_labels = None
        fig_dict = {"fig": fig, "ax": ax, "gl": gl}
        fig_dict = plotter(
            fig_dict, self.data_dict, data_var, coastline=coastline, contour=contour
        )

        show_or_save_fig(
            fig_dict, self.data_dict, "wavegrid", test_mode, save_fig, filename
        )

        return fig_dict

    def topo(
        self,
        plotter: Callable = matplotlib_functions.topo_plotter,
        coastline: bool = None,
        test_mode: bool = False,
        save_fig: bool = False,
        filename: str = None,
    ) -> None:
        fig, ax = plt.subplots(subplot_kw={"projection": ccrs.PlateCarree()})
        gl = ax.gridlines(
            crs=ccrs.PlateCarree(),
            draw_labels=True,
            color="gray",
            alpha=0.5,
            linestyle="--",
        )
        gl.top_labels = None
        gl.right_labels = None
        fig_dict = {"fig": fig, "ax": ax, "gl": gl}
        fig_dict = plotter(fig_dict, self.data_dict, coastline=coastline)
        fig_dict.get("ax").legend()
        show_or_save_fig(
            fig_dict, self.data_dict, "topo", test_mode, save_fig, filename
        )

        return fig_dict

    def grid(
        self,
        plotter: Callable = matplotlib_functions.grid_plotter,
        coastline: bool = None,
        test_mode: bool = False,
        save_fig: bool = False,
        filename: str = None,
    ) -> None:
        fig, ax = plt.subplots(1)
        fig_dict = {"fig": fig, "ax": ax}
        fig_dict = plotter(fig_dict, self.data_dict, coastline=coastline)
        fig_dict.get("ax").legend()

        show_or_save_fig(
            fig_dict, self.data_dict, "grid", test_mode, save_fig, filename
        )

        return fig_dict

    def wind(
        self,
        plotter: Callable = matplotlib_functions.directional_data_plotter,
        coastline: bool = True,
        contour: bool = True,
        test_mode: bool = False,
        save_fig: bool = False,
        filename: str = None,
    ):
        fig, ax = plt.subplots(subplot_kw={"projection": ccrs.PlateCarree()})
        gl = ax.gridlines(
            crs=ccrs.PlateCarree(),
            draw_labels=True,
            color="gray",
            alpha=0.5,
            linestyle="--",
        )
        gl.top_labels = None
        gl.right_labels = None
        fig_dict = {"fig": fig, "ax": ax, "gl": gl}
        fig_dict = plotter(
            fig_dict,
            self.data_dict,
            obj_type="wind",
            coastline=coastline,
            contour=contour,
            test_mode=test_mode,
        )
        show_or_save_fig(
            fig_dict, self.data_dict, "wind", test_mode, save_fig, filename
        )

        return fig_dict

    def current(
        self,
        plotter: Callable = matplotlib_functions.directional_data_plotter,
        coastline: bool = False,
        contour: bool = False,
        test_mode: bool = False,
        save_fig: bool = False,
        filename: str = None,
    ):
        fig, ax = plt.subplots(subplot_kw={"projection": ccrs.PlateCarree()})
        gl = ax.gridlines(
            crs=ccrs.PlateCarree(),
            draw_labels=True,
            color="gray",
            alpha=0.5,
            linestyle="--",
        )
        gl.top_labels = None
        gl.right_labels = None
        fig_dict = {"fig": fig, "ax": ax, "gl": gl}
        fig_dict = plotter(
            fig_dict,
            self.data_dict,
            obj_type="current",
            coastline=coastline,
            contour=contour,
            test_mode=test_mode,
        )
        show_or_save_fig(
            fig_dict, self.data_dict, "current", test_mode, save_fig, filename
        )

        return fig_dict

    def spectra(
        self,
        plotter: Callable = matplotlib_functions.spectra_plotter,
        test_mode: bool = False,
        save_fig: bool = False,
        filename: str = None,
    ):
        fig, ax = plt.subplots(subplot_kw={"polar": True})
        fig_dict = {"fig": fig, "ax": ax}
        fig_dict = plotter(fig_dict, self.data_dict)
        show_or_save_fig(
            fig_dict, self.data_dict, "spectra", test_mode, save_fig, filename
        )

        return fig_dict

    def waveseries(
        self,
        var=["hs", ("tm01", "tm02"), "dirm"],
        plotter: Callable = matplotlib_functions.waveseries_plotter,
        lon: float = None,
        lat: float = None,
        separate_plots: bool = None,
        test_mode: bool = False,
        save_fig: bool = False,
        filename: str = None,
    ):
        """var = ['hs', 'tp'] or ['hs',('tp','tm01')]

        use 'separate_plots = True' to get separate figures for each parameter.
        Default is separate_plots = True for more than 4 parameters.

        Use 'lon', 'lat' to pick a point to plot in case the data has many."""
        fig_dict = plotter(
            self.data_dict, self.data_dict2, var, lon, lat, separate_plots
        )
        show_or_save_fig(
            fig_dict, self.data_dict, "waveseries", test_mode, save_fig, filename
        )

        return fig_dict

    def spectra1d(
        self,
        plotter: Callable = matplotlib_functions.spectra1d_plotter,
        test_mode: bool = False,
        save_fig: bool = False,
        filename: str = None,
    ):
        fig, ax = plt.subplots()
        fig, ax2 = fig, ax.twinx()
        fig_dict = {"fig": fig, "ax": ax, "ax2": ax2}
        fig_dict = plotter(fig_dict, self.data_dict)
        show_or_save_fig(
            fig_dict, self.data_dict, "spectra1d", test_mode, save_fig, filename
        )

        return fig_dict

    def scatter(
        self,
        xvar="hs",
        yvar="hs",
        plotter: Callable = matplotlib_functions.scatter_plotter,
        lon: float = None,
        lat: float = None,
        test_mode: bool = False,
        save_fig: bool = False,
        filename: str = None,
    ):
        fig, ax = plt.subplots()
        fig_dict = {"fig": fig, "ax": ax}
        data_dict2 = self.data_dict2 or self.data_dict
        fig_dict = plotter(
            fig_dict, self.data_dict, data_dict2, xvar, yvar, lon=lon, lat=lat
        )
        show_or_save_fig(
            fig_dict,
            self.data_dict,
            "waveseries",
            test_mode,
            save_fig,
            filename,
            prefix="scatter",
        )

        return fig_dict


class Plotly:
    def __init__(self, data_dict: dict, data_dict2: dict = None):
        self.data_dict = data_dict
        self.data_dict2 = data_dict2 or {}

    def waveseries(
        self,
        plain: bool = False,
        plotter: Callable = plotly_functions.waveseries_plotter,
    ):
        fig_dict = plotter(self.data_dict, self.data_dict2, plain)
        return fig_dict

    def spectra(self, plotter: Callable = plotly_functions.spectra_plotter):
        fig_dict = plotter(self.data_dict, self.data_dict2)
        return fig_dict

    def scatter(self, plotter: Callable = plotly_functions.scatter_plotter):
        fig_dict = plotter(self.data_dict, self.data_dict2)
        return fig_dict
