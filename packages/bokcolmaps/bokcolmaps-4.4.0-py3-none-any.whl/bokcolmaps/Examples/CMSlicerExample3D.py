"""
This class needs the Bokeh server,
i.e. to run this example at the command line enter:
bokeh serve --show CMSlicerExample3D.py
"""

from bokeh.io import curdoc

from bokcolmaps.CMSlicer3D import CMSlicer3D
from bokcolmaps.Examples import example_data

x, y, z, D = example_data()

cm = CMSlicer3D(x, y, z, D, xlab='x val', ylab='y val', zlab='power val', dmlab='Function val')

curdoc().add_root(cm)
