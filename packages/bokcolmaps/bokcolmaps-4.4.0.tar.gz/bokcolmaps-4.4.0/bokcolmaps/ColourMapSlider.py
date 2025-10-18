"""
ColourMapSlider class definition
"""

import numpy

from bokeh.model import DataModel

from bokeh.models.widgets import Slider
from bokeh.models.layouts import Column

from bokeh.core.properties import Instance

from bokcolmaps.ColourMap import ColourMap

from bokcolmaps.get_common_kwargs import get_common_kwargs
from bokcolmaps.check_kwargs import check_kwargs


class ColourMapSlider(Column, DataModel):

    """
    A ColourMap with a slider linked to the z coordinate
    (i.e. the 2D slice being displayed).
    """

    cmap = Instance(ColourMap)
    zslider = Instance(Slider)

    def __init__(self, x: numpy.array, y: numpy.array, z: numpy.array, dm: numpy.ndarray, **kwargs) -> None:

        """
        All init arguments same as for ColourMap
        """

        check_kwargs(kwargs, extra_kwargs=['height', 'width', 'hover'])

        palette, cfile, revcols, xlab, ylab, zlab, dmlab, \
            rmin, rmax, xran, yran, alpha, nan_colour = get_common_kwargs(**kwargs)

        height = kwargs.get('height', 575)
        width = kwargs.get('width', 500)
        hover = kwargs.get('hover', True)

        super().__init__()

        self.height = height
        self.width = width

        self.cmap = ColourMap(x, y, z, dm,
                              palette=palette, cfile=cfile, revcols=revcols,
                              xlab=xlab, ylab=ylab, zlab=zlab, dmlab=dmlab,
                              height=height, width=width, rmin=rmin, rmax=rmax,
                              xran=xran, yran=yran, hover=hover,
                              alpha=alpha, nan_colour=nan_colour)

        self.zslider = Slider(title=zlab + ' index', start=0, end=z.size - 1,
                              step=1, value=0, orientation='horizontal',
                              width=self.cmap.plot.width)

        self.zslider.js_on_change('value', self.cmap.cjs_slider)

        self.children.append(Column(self.zslider, width=self.width))
        self.children.append(self.cmap)
