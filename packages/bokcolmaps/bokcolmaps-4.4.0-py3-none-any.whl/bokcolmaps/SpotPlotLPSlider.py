"""
SplotPlotLPSlider class definition
"""

import numpy

from bokeh.model import DataModel

from bokeh.models.widgets import Slider
from bokeh.models.layouts import Column

from bokeh.core.properties import Instance

from bokcolmaps.SpotPlotLP import SpotPlotLP

from bokcolmaps.get_common_kwargs import get_common_kwargs
from bokcolmaps.check_kwargs import check_kwargs


class SpotPlotLPSlider(Column, DataModel):

    """
    A SpotPlotLP with a slider linked to the z coordinate
    (i.e. the row being displayed).
    """

    splotlp = Instance(SpotPlotLP)
    zslider = Instance(Slider)

    def __init__(self, x: numpy.array, y: numpy.array, z: numpy.array, dm: numpy.ndarray, **kwargs) -> None:

        """
        All init arguments same as for SpotPlotLP
        """

        check_kwargs(kwargs, extra_kwargs=['spheight', 'spwidth', 'lpheight', 'lpwidth', 'revz', 'padleft', 'padabove'])

        palette, cfile, revcols, xlab, ylab, zlab, dmlab, \
            rmin, rmax, xran, yran, alpha, nan_colour = get_common_kwargs(**kwargs)

        spheight = kwargs.get('spheight', 575)
        spwidth = kwargs.get('spwidth', 500)
        lpheight = kwargs.get('lpheight', 500)
        lpwidth = kwargs.get('lpwidth', 300)
        revz = kwargs.get('revz', False)
        padleft = kwargs.get('padleft', 0)
        padabove = kwargs.get('padabove', 0)

        super(SpotPlotLPSlider, self).__init__()

        self.height = spheight
        self.width = int((spwidth + lpwidth) * 1.1)

        self.splotlp = SpotPlotLP(x, y, z, dm,
                                  palette=palette, cfile=cfile, revcols=revcols,
                                  xlab=xlab, ylab=ylab, zlab=zlab, dmlab=dmlab,
                                  spheight=spheight, spwidth=spwidth,
                                  lpheight=lpheight, lpwidth=lpwidth,
                                  rmin=rmin, rmax=rmax, xran=xran, yran=yran,
                                  revz=revz, alpha=alpha, nan_colour=nan_colour,
                                  padleft=padleft, padabove=padabove)

        self.zslider = Slider(title=zlab + ' index', start=0, end=z.size - 1,
                              step=1, value=0, orientation='horizontal',
                              width=self.splotlp.spplot.plot.width)

        self.zslider.on_change('value', self.splotlp.spplot.input_change)

        self.children.append(Column(self.zslider, width=self.width))
        self.children.append(self.splotlp)
