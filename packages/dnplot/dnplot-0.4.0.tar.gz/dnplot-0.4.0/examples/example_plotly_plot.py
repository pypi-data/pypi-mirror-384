# Plotting with the new dnora version 2
import dnora as dn
import dnplot

# import os
# os.environ["DNORA_LOCAL_GRID_PATH"] = "~/bathy"

"""
These examples plots are using library plotly
"""

#Plots a barpolar spectra plot together with spectra1D a map with location points.  
#Plots separete spectra1d plot.
grid = dn.grid.EMODNET(lon=(4, 6), lat=(59, 60))
grid.import_topo(folder="~/kodai/bathy")
grid.set_spacing(dm=5000)
grid.mesh_grid()
model = dn.modelrun.NORA3(grid, year=2022, month=2, day=1)
model.import_spectra()
model.spectra_to_1d()

plot = dnplot.Plotly(model)
plot.spectra()
plot.spectra1d()


#Plots a scatter plot 
e39 = dn.modelrun.ModelRun(year=2019, month=3)
e39.import_waveseries(dn.waveseries.read.E39(loc="D"), point_picker=dn.pick.Trivial())

point = dn.grid.Grid(lon=e39.waveseries().lon(), lat=e39.waveseries().lat())
nora3 = dn.modelrun.NORA3(point, year=2019, month=3)
nora3.import_spectra()
nora3.spectra_to_waveseries()
plot = dnplot.Plotly1(e39, nora3)
plot.scatter()

#Plots waveseries plot
point = dn.grid.Grid(lon=4.308, lat=62.838, name="Svinoy")
model = dn.modelrun.NORA3(point, year=2022, month=3, day=18)
model.import_spectra()
model.spectra_to_waveseries()
model.waveseries()
plot = dnplot.Plotly(model)
plot.waveseries(use_dash=True)

