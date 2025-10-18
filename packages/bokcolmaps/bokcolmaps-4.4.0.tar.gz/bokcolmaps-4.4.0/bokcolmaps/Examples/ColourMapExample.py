"""
To run this example at the command line enter:
python ColourMapExample.py
"""

import numpy

from bokeh.plotting import show
from bokeh.io import output_file

from bokcolmaps.ColourMap import ColourMap
from bokcolmaps.Examples import example_data

x, y, z, D = example_data()
D = D[0]  # Data for first value of z
z = numpy.array([z[0]])  # First value of z

cm = ColourMap(x, y, z, D, xlab='x val', ylab='y val', zlab='power val', dmlab='Function val')

# Calls below not needed, only added for code coverage test
cm.update_image(0)

output_file('ColourMapExample.html', mode='inline')
show(cm)
