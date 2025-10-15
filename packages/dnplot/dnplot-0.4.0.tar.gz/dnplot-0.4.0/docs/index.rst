elcome to dnplot's Documentation!
==================================

**dnplot** is a Python package designed for visualizing `dnora <https://github.com/MET-OM/dnora>`_ objects, including 🌬️ wind, 🌊 waves, and ocean currents. 
This package supports various plot types utilizing the `matplotlib <https://matplotlib.org/>`_ and `plotly <https://plotly.com/>`_ libraries.

To get started, import `dnora` and `dnplot`:

.. code-block:: python

    import dnora as dn
    import dnplot


Example for the wind, grid, spectra, spectra1d
===============================================

.. code-block:: python

    grid = dn.grid.EMODNET(lon=(4, 6), lat=(59, 60))
    grid.set_spacing(dm=5000)
    grid.mesh_grid()
    model = dn.modelrun.NORA3(grid, year=2022, month=2, day=1)
    model.import_wind()
    model.import_spectra()
    model.spectra_to_1d()
    plot = dnplot.Dnora(model)


Plots using Matplotlib library
==============================


Grid plot 
---------

.. code-block:: python

    plot.grid()


.. image:: files/grid_plt.png
    :width: 500


Wind plot
---------

.. code-block:: python
    
    plot.wind()


.. image:: files/wind_plt.png
    :width: 500


Spectra Plot 
------------

.. code-block:: python

    plot.spectra()


.. image:: files/spectra_plt.png
    :width: 500


Spectra1D Plot 
--------------

.. code-block:: python
    
    plot.spectra1d()


.. image:: files/spectra1d_plt.png
    :width: 500



Example for the scatter plot
=============================

.. code-block:: python

    #Plots a scatter plot 
    e39 = dn.modelrun.ModelRun(year=2019, month=3)
    e39.import_waveseries(dn.waveseries.read.E39(loc="D"), point_picker=dn.pick.Trivial())

    point = dn.grid.Grid(lon=e39.waveseries().lon(), lat=e39.waveseries().lat())
    nora3 = dn.modelrun.NORA3(point, year=2019, month=3)
    nora3.import_spectra()
    nora3.spectra_to_waveseries()
    plot = dnplot.Dnora1(nora3, e39)


Scatter Plot 
------------

.. code-block:: python

    plot.scatter(['hs','hs'])


.. image:: files/scatter_plt.png
    :width: 500



Example for the waveseries plot
===============================

.. code-block:: python

    #plots a waveseries plot
    point = dn.grid.Grid(lon=4.308, lat=62.838, name="Svinoy")
    model = dn.modelrun.NORA3(point, year=2022, month=3, day=18)
    model.import_spectra()
    model.spectra_to_waveseries()
    model.waveseries()
    plot = dnplot.Dnora(model)


Waveseries Plot
---------------

There are two types of wave series plots, depending on the number of variables you have. 

If you have more than 3 variables, where (var1, var2) are treated as one, you will be given 4 different figures with the chosen variables. 

If you have 3 or fewer variables, you will receive a single figure with labels corresponding to the selected variables.

.. code-block::python

    plot.waveseries([('hs','tm01'),('hs', 'tm01'), 'hs'])
    plot.waveseries([('hs','tm01'),('hs', 'tm01'),('hs','dirm') 'hs'])


Waveseries when variables are 3 or less:

.. image:: files/waveseries_plt3.png
    :width: 500

Waveseries when variables are more than 3:

.. image:: files/waveseries_plt4.png
    :width: 500




Plots using Plotly library
==============================

Example for the spectra, spectra1d
===============================================

.. code-block:: python

    grid = dn.grid.EMODNET(lon=(4, 6), lat=(59, 60))
    grid.set_spacing(dm=5000)
    grid.mesh_grid()
    model = dn.modelrun.NORA3(grid, year=2022, month=2, day=1)
    model.import_wind()
    model.import_spectra()
    model.spectra_to_1d()
    plot = dnplot.Plotly(model)


Spectra Plot
------------

.. code-block:: python

    plot.spectra()


.. image:: files/spectra_plotly.png
    :width: 500

Spectra1D Plot
--------------

.. code-block:: python

    plot.spectra1d()


.. image:: files/spectra1d_plotly.png
    :width: 500


Example for the scatter plot
=============================

.. code-block:: python

    #Plots a scatter plot 
    e39 = dn.modelrun.ModelRun(year=2019, month=3)
    e39.import_waveseries(dn.waveseries.read.E39(loc="D"), point_picker=dn.pick.Trivial())

    point = dn.grid.Grid(lon=e39.waveseries().lon(), lat=e39.waveseries().lat())
    nora3 = dn.modelrun.NORA3(point, year=2019, month=3)
    nora3.import_spectra()
    nora3.spectra_to_waveseries()
    plot = dnplot.Plotly1(nora3, e39)

Scatter Plot
------------

.. code-block:: python

    plot.scatter()

    
.. image:: files/scatter_plotly.png
    :width: 500


Example for the waveseries plot
===============================

.. code-block:: python

    #plots a waveseries plot
    point = dn.grid.Grid(lon=4.308, lat=62.838, name="Svinoy")
    model = dn.modelrun.NORA3(point, year=2022, month=3, day=18)
    model.import_spectra()
    model.spectra_to_waveseries()
    model.waveseries()
    plot = dnplot.Plotly(model)


Waveseries Plot
---------------

.. code-block:: python

    plot.waveseries(use_dash=True)


You can plot wave series with drop-down buttons by setting use_dash=True,
or without them by setting use_dash=False.


Waveseries use_dash=True:

.. image:: files/waveseries_plotly.png
    :width: 500

Waveseries use_dash=False:

.. image:: files/waveseries_plotly1.png
    :width: 500

