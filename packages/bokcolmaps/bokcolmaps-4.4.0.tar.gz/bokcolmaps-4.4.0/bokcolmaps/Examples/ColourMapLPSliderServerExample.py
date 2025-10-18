"""
To run this example at the command line enter:
bokeh serve --show ColourMapLPSliderServerExample.py

To use the ColourMapSlider (i.e. without a line plot)
just import and instantiate that instead (same init parameters)
To disable the hover tool readout, add kwarg hoverdisp=False.
"""

from bokeh.io import curdoc

from bokcolmaps.ColourMapLPSlider import ColourMapLPSlider
from bokcolmaps.Examples import example_data

x, y, z, D = example_data()

cm = ColourMapLPSlider(x, y, z, D, xlab='x val', ylab='y val', zlab='power val', dmlab='Function val', scbutton=True)

curdoc().add_root(cm)
