from dash import Dash, dcc, html
import xarray as xr
from dnplot import sanitation
def create_spectra_app_layout(
    len_of_inds: int, len_of_inds_B: int, len_of_times: int, number_of_1d_plots: int, number_of_2d_plots: int, name:str, name_B: str
):


    if name_B is not None:
        slider_label = f"{name_B} index"
        slider_len = len_of_inds_B - 1
    else:
        slider_label = 'Inactive'
        slider_len = 0

    if number_of_2d_plots not in [0, 1,2]:
        raise ValueError("'number_of_2d_plots' must be 0, 1 or 2, not {number_of_plots}!")

    if number_of_1d_plots not in [0,1]:
        raise ValueError("'number_of_1d_plots' must be 0 or 1, not {number_of_1d_plots}!")

    return html.Div(
        [
            html.H1(id="title", style={"textAlign": "center"}),
            html.H2(id="smaller_title", style={"textAlign": "center"}),
            html.Label("time_index"),
            dcc.Slider(
                min=0,
                max=len_of_times - 1,
                step=1,
                value=0,
                tooltip={"placement": "bottom", "always_visible": True},
                updatemode="drag",
                persistence=True,
                persistence_type="session",
                id="time_slider",
            ),
            html.Label(f"{name} index"),
            dcc.Slider(
                min=0,
                max=len_of_inds - 1,
                step=1,
                value=0,
                tooltip={"placement": "bottom", "always_visible": True},
                updatemode="drag",
                persistence=True,
                persistence_type="session",
                id="inds_slider",
            ),
            html.Label(slider_label),
            dcc.Slider(
                min=0,
                max=slider_len,
                step=1,
                value=0,
                tooltip={"placement": "bottom", "always_visible": True},
                updatemode="drag",
                persistence=True,
                persistence_type="session",
                id="inds_slider_B",
            ),
            html.Div(
                [
                    html.Div(
                        dcc.Graph(id="1d_graph"),
                        style={
                            "flex-grow": "1",
                            #"width": "30%" if number_of_plots == 2 else "50%",  # Set width for each graph container
                            "display": "inline-block",
                        },
                    ) if number_of_1d_plots == 1 else None,
                    html.Div(
                        dcc.Graph(id="spectra_map"),
                        style={
                            "flex-grow": "1",
                            #"width": "30%" if number_of_plots == 2 else "50%",  # Set width for each graph container
                            "display": "inline-block",
                        },
                    ),
                ],
                style={
                    "display": "flex",  # Arrange graphs in a single row
                    "flexDirection": "row",  # Horizontal layout
                    "width": "100%",  # Ensure the container spans the full width
                },
            ),
                        html.Div(
                [
                    html.Div(
                        dcc.Graph(id="2d_graph1"),
                        style={
                            "flex-grow": "1",
                            #"width": "30%" if number_of_plots == 2 else "50%",  # Set width for each graph container
                            "display": "inline-block",
                        },
                    ) if number_of_2d_plots > 0 else None,
                    html.Div(
                        dcc.Graph(id="2d_graph2"),
                        style={
                            "flex-grow": "1",
                            #"width": "40%" if number_of_plots == 2 else "50%",  # Set width for each graph container
                            "display": "inline-block",
                        },
                    )
                    if number_of_2d_plots > 1
                    else None,  # Only include secondary_graph if number_of_plots == 2
                    
                ],
                style={
                    "display": "flex",  # Arrange graphs in a single row
                    "flexDirection": "row",  # Horizontal layout
                    "width": "100%",  # Ensure the container spans the full width
                },
            ),
        ]
    )

def create_wave_data_layout(xmodel_all: xr.Dataset, ymodel_all: xr.Dataset, set_y_start_val: bool=False):
    """Creates a layout for data with two soureces.

    2 dropdown menus
    1 plot
    2 sliders for indeces
    1 map to plot points"""

    
    xdf, ydf, df = sanitation.get_one_point_merged_dataframe(xmodel_all, ymodel_all, inds_x=0, inds_y=0)
    xvariables = [col for col in xdf if col != 'time']
    yvariables = [col for col in ydf if col != 'time']
    
    x_start_val = xvariables[0]
    x_options = [{"label": val, "value": val} for val in xvariables]
    
    if ymodel_all is not None:
        y_start_val = yvariables[0]
        y_options = [{"label": val, "value": val} for val in yvariables]
    else:
        y_options = x_options
    
    
    if not set_y_start_val:
        y_options = [{"label": "None", "value": "None"}] + y_options
        y_start_val = 'None'
    else:
        y_start_val = yvariables[0] if ymodel_all is not None else yvariables[1]

    if ymodel_all is not None:
        slider_label = f"{ymodel_all.name} index"
        slider_len = len(ymodel_all.lon)-1
    else:
        slider_label = 'Inactive'
        slider_len=0


    app = Dash(__name__)

    app.layout = html.Div(
        [
            html.H1(id="title", style={"textAlign": "center"}),
            html.P("Select variable:"),
            dcc.Dropdown(
                id="dropdown1",
                options=x_options,
                value=x_start_val,
                clearable=False,
                style={"width": "30%"},
            ),
            dcc.Dropdown(
                id="dropdown2",
                options=y_options,
                value=y_start_val,
                clearable=False,
                style={"width": "30%"},
            ),
            html.Div(
                [
                    dcc.Graph(id="data_chart"),
                ],
                style={
                    "display": "flex",
                    "flexDirection": "column",
                    "width": "75%",
                    "float": "left",
                    "marginTop": "200px"
                },
            ),
            html.Label(f"{xmodel_all.name} index"),
            
            html.Div([dcc.Slider(
                min=0,
                max=len(xmodel_all.lon)-1,
                step=1,
                value=0,
                tooltip={"placement": "bottom", "always_visible": True},
                updatemode="drag",
                persistence=True,
                persistence_type="session",
                id="xslider",
 
            )],
            style={'width':'75%'}),

            html.Label(slider_label),
            html.Div([dcc.Slider(
                min=0,
                max=slider_len,
                step=1,
                value=0,
                tooltip={"placement": "bottom", "always_visible": True},
                updatemode="drag",
                persistence=True,
                persistence_type="session",
                id="yslider",
 
            )],
            style={'width':'75%'}),
            html.Div(
                [dcc.Graph(id="map")],
                style={
                    "display": "flex",
                    "flexDirection": "column",
                    "width": "25%",
                    "float": "right",
                },
            ),
        ]
    )

    return app