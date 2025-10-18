"""
To run this example at the command line enter:
python ColourMapLPSLiderExample.py
"""

from bokeh.plotting import show
from bokeh.io import output_file

from bokcolmaps.ColourMapLPSlider import ColourMapLPSlider
from bokcolmaps.Examples import example_data

x, y, z, D = example_data()

cm = ColourMapLPSlider(x, y, z, D, xlab='x val', ylab='y val', zlab='power val', dmlab='Function val')

output_file('ColourMapLPSliderExample.html', mode='inline')
show(cm)
