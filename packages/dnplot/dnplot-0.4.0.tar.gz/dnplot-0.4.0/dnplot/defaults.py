import cmocean.cm

DEFAULT_VARIABLE_DATA = {
    "name": None,
    "unit": None,
    "cmap": cmocean.cm.thermal,
}

default_variable = {
    "hs": {"name": "Significant wave height", "unit": "m", "cmap": cmocean.cm.amp},
    "tp": {"name": "Peak wave period", "unit": "s", "cmap": cmocean.cm.tempo},
    "tm01": {"name": "Mean wave period", "unit": "s", "cmap": cmocean.cm.tempo},
    "tm02": {
        "name": "Spectral zero-crossing wave period",
        "unit": "s",
        "cmap": cmocean.cm.tempo,
    },
    "tm_10": {"name": "Energy period", "unit": "s", "cmap": cmocean.cm.tempo},
    "dirp": {"name": "Peak wave direction", "unit": "s", "cmap": cmocean.cm.phase},
    "dirm": {"name": "Mean wave direction", "unit": "s", "cmap": cmocean.cm.phase},
    "wind": {"name": "Wind", "unit": "m/s", "cmap": cmocean.cm.tempo},
    "current": {"name": "Current", "unit": "m/s", "cmap": cmocean.cm.tempo},
    "topo": {
        "name": "Topography",
        "unit": "m",
        "cmap": cmocean.tools.crop_by_percent(cmocean.cm.topo_r, 50, which="min"),
    },
    "mask": {"name": " ", "unit": " ", "cmap": "gray"},
}

default_markers = {
    # To have something to plot for all objects
    "generic_objects": {"marker": "x", "color": "m", "size": 2},
    "generic_points": {"marker": "*", "color": "m", "size": 2},
    # These are objects that represent DNORA unstructured data
    "spectra": {"marker": "x", "color": "k", "size": 7},
    "waveseries": {"marker": "x", "color": "r", "size": 7},
    # These are objects that represent DNORA gridded data
    "wind": {"marker": ".", "color": "k", "size": 1},
    "current": {"marker": ".", "color": "r", "size": 1},
    "ice": {"marker": ".", "color": "b", "size": 1},
    # These are points that correspond to boolean masks
    "boundary_points": {"marker": "*", "color": "k", "size": 5},
    "output_points": {"marker": "*", "color": "r", "size": 5},
}
