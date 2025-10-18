"""
CMSlicer class definition
"""

import numpy

from bokeh.core.properties import List
from bokeh.model import DataModel
from bokeh.events import Tap

from bokeh.models.sources import ColumnDataSource
from bokeh.models.layouts import Row
from bokeh.models.renderers import GlyphRenderer
from bokeh.models.glyphs import Line

from bokeh.core.properties import Instance, Bool

from bokcolmaps.ColourMapLPSlider import ColourMapLPSlider
from bokcolmaps.ColourMap import ColourMap

from bokcolmaps.get_common_kwargs import get_common_kwargs
from bokcolmaps.check_kwargs import check_kwargs


class CMSlicer(Row, DataModel):

    """
    Base class for CMSlicer2D and CMSlicer3D.
    """

    sl_src = Instance(ColumnDataSource)
    cmap_params = Instance(ColumnDataSource)
    lr = Instance(GlyphRenderer)

    _is_selecting = Bool
    _extra_kwargs = List

    def __init__(self, x: numpy.array, y: numpy.array, **kwargs) -> None:

        """
        args...
            x: 1D NumPy array of x coordinates
            y: 1D NumPy array of y coordinates
        kwargs...
            cmheight: ColourMap height (pixels)
            cmwidth: ColourMap width (pixels)
            spheight: slice plot height (pixels)
            spwidth: slice plot width (pixels)
            splab: slice plot label
            revz: reverse z axis in line plot if True
            hoverdisp: display the hover tool readout if True
            padleft: padding (pixels) to left of slice plot (default 0)
            padabove: padding (pixels) above slice plot (default 0)
        """

        super().__init__()

        self._extra_kwargs = ['cmheight', 'cmwidth', 'spheight', 'spwidth', 'lpheight', 'lpwidth', 'splab', 'revz', 'hoverdisp', 'sphoverdisp',
                              'padleft', 'padabove', 'padleftlp', 'padabovelp']

        check_kwargs(kwargs, extra_kwargs=self._extra_kwargs)

        palette, cfile, revcols, xlab, ylab, zlab, dmlab, \
            rmin, rmax, xran, yran, alpha, nan_colour = get_common_kwargs(**kwargs)

        cmheight = kwargs.get('cmheight', 575)
        cmwidth = kwargs.get('cmwidth', 500)
        spheight = kwargs.get('spheight', cmheight)
        spwidth = kwargs.get('spwidth', cmwidth)
        splab = kwargs.get('splab', 'Units')
        revz = kwargs.get('revz', False)
        hoverdisp = kwargs.get('hoverdisp', True)
        padleft = kwargs.get('padleft', 0)
        padabove = kwargs.get('padabove', 0)

        x0, x1 = x[0], x[-1]
        ymean = (y[0] + y[-1]) / 2
        y0, y1 = ymean, ymean
        self.sl_src = ColumnDataSource({'x': [x0, x1], 'y': [y0, y1]})

        self.cmap_params = ColumnDataSource({'palette': [palette], 'cfile': [cfile], 'revcols': [revcols],
                                             'xlab': [xlab], 'ylab': [ylab], 'zlab': [zlab], 'dmlab': [dmlab],
                                             'rmin': [rmin], 'rmax': [rmax], 'xran': [xran], 'yran': [yran],
                                             'alpha': [alpha], 'nan_colour': [nan_colour], 'splab': [splab],
                                             'cmheight': [cmheight], 'cmwidth': [cmwidth],
                                             'spheight': [spheight], 'spwidth': [spwidth],
                                             'padleft': [padleft], 'padabove': [padabove],
                                             'revz': [revz], 'hoverdisp': [hoverdisp]})

        self._is_selecting = False

    def get_interp_coords(self, datasrc: ColumnDataSource) -> tuple:

        """
        Get the interpolation coordinates and range values
        """

        x = datasrc.data['x'][0]
        y = datasrc.data['y'][0]

        dx = numpy.min(numpy.abs(numpy.diff(x)))
        dy = numpy.min(numpy.abs(numpy.diff(y)))

        x0, x1 = self.sl_src.data['x'][0], self.sl_src.data['x'][1]
        y0, y1 = self.sl_src.data['y'][0], self.sl_src.data['y'][1]

        nx = int(numpy.floor(numpy.abs(x1 - x0) / dx)) + 1
        ny = int(numpy.floor(numpy.abs(y1 - y0) / dy)) + 1
        nc = numpy.max([nx, ny])

        x_i = numpy.linspace(x0, x1, nc)
        y_i = numpy.linspace(y0, y1, nc)
        c_i = numpy.array(list(zip(y_i, x_i)))

        r_i = numpy.sqrt((x_i - x_i[0]) ** 2 + (y_i - y_i[0]) ** 2)

        return c_i, r_i

    def toggle_select(self, event: Tap) -> None:

        """
        Handle Tap events for slice change
        """

        if self._is_selecting:

            self._is_selecting = False
            self.sl_src.data['x'][1] = event.x
            self.sl_src.data['y'][1] = event.y
            self.sl_src.trigger('data', None, self.sl_src.data)

            if type(self.cmap) is ColourMap:  # Subclass is CMSlicer2D
                self.cmap.plot.renderers.remove(self.lr)
                self.lr = self.cmap.plot.add_glyph(self.sl_src, Line(x='x', y='y', line_color='white', line_width=5,
                                                                     line_dash='dashed', line_alpha=1))
            elif type(self.cmap) is ColourMapLPSlider:  # Subclass is CMSlicer3D
                self.cmap.cmaplp.cmplot.plot.renderers.remove(self.lr)
                self.lr = self.cmap.cmaplp.cmplot.plot.add_glyph(self.sl_src, Line(x='x', y='y', line_color='white', line_width=5,
                                                                                   line_dash='dashed', line_alpha=1))

            self._change_slice()

        else:

            self._is_selecting = True
            self.sl_src.data['x'][0] = event.x
            self.sl_src.data['y'][0] = event.y
