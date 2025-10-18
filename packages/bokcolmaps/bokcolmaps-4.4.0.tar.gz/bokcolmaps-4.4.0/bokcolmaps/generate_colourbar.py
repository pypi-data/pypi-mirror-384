"""
generate_colourbar function definition
"""

from bokeh.models import ColorBar
from bokeh.models.tickers import AdaptiveTicker
from bokeh.models.mappers import LinearColorMapper


def generate_colourbar(cmap: LinearColorMapper, cbarwidth: int=25) -> ColorBar:

    """
    Generate a colourbar for the the ColourMap and SpotPlot classes
    """

    cbar = ColorBar(color_mapper=cmap, location=(0, 0),
                    label_standoff=5, orientation='horizontal',
                    height=cbarwidth, ticker=AdaptiveTicker(),
                    bar_line_color='Black', major_tick_line_color='Black')

    return cbar
