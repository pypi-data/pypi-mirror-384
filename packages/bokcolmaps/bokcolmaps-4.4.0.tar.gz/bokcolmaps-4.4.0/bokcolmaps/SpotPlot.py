"""
SpotPlot class definition
"""

import numpy

from bokeh.model import DataModel

from bokeh.models import ColumnDataSource, Plot, ColorBar
from bokeh.models.mappers import LinearColorMapper
from bokeh.models.layouts import Column

from bokeh.core.properties import Instance, String, Int, Float, Bool

from bokeh.plotting import figure

from bokcolmaps.get_common_kwargs import get_common_kwargs
from bokcolmaps.check_kwargs import check_kwargs
from bokcolmaps.generate_colourbar import generate_colourbar
from bokcolmaps.read_colourmap import read_colourmap
from bokcolmaps.get_min_max import get_min_max


class SpotPlot(Column, DataModel):

    """
    Like a scatter plot but with the points colour mapped with a
    user-defined colour scale.
    """

    plot = Instance(Plot)
    cbar = Instance(ColorBar)

    datasrc = Instance(ColumnDataSource)
    coldatasrc = Instance(ColumnDataSource)
    cvals = Instance(ColumnDataSource)
    cmap = Instance(LinearColorMapper)

    _title_root = String
    _zlab = String
    _bg_col = String
    _nan_col = String
    _sp_size_i = Int
    _sp_size_f = Float
    _marker = String
    _autoscale = Bool
    _cbdelta = Float

    def __init__(self, x: numpy.array, y: numpy.array, z: numpy.array, dm: numpy.ndarray, **kwargs) -> None:

        """
        args...
            x: 1D NumPy array of x coordinates for the spot locations
            y: 1D NumPy array of y coordinates for the spot locations, same size as x
            z: 1D NumPy array of (common) z coordinates
            dm: 2D NumPy array of the data for display, dimensions z.size by x.size
        kwargs: all in get_common_kwargs plus...
            height: plot height (pixels)
            width: plot width (pixels)
            size: spot size (pixels as int or data units as float)
            marker: data marker (string)
        """

        check_kwargs(kwargs, extra_kwargs=['height', 'width', 'size', 'marker'])

        palette, cfile, revcols, xlab, ylab, zlab, dmlab, \
            rmin, rmax, xran, yran, alpha, nan_colour = get_common_kwargs(**kwargs)

        height = kwargs.get('height', 575)
        width = kwargs.get('width', 500)

        size = kwargs.get('size', 10)
        if type(size) is int:
            self._sp_size_i = size
        else:
            self._sp_size_f = size

        self._marker = kwargs.get('marker', 'circle')

        super().__init__()

        self._cbdelta = 0.01  # Min colourbar range (used if values are equal)

        self._title_root = dmlab
        self._zlab = zlab

        is3D = True if z.size > 1 else False

        self._autoscale = True
        if (rmin is not None) and (rmax is not None):
            self._autoscale = False
        else:
            if rmin is not None:
                self._rmin = rmin
            elif is3D:
                self._rmin = numpy.min(dm[0])
            else:
                self._rmin = numpy.min(dm)
            if rmax is not None:
                self._rmax = rmax
            elif is3D:
                self._rmax = numpy.max(dm[0])
            else:
                self._rmax = numpy.max(dm)

        if is3D:  # Default to first 'slice'
            d = dm[0]
        else:
            d = dm

        if self._autoscale:
            min_val, max_val = get_min_max(d, self._cbdelta)
        else:
            min_val = rmin
            max_val = rmax

        if cfile is not None:
            self._read_cmap(cfile)
            palette = self.cvals.data['colours']
            if revcols:
                self.cvals.data['colours'].reverse()

        self.cmap = LinearColorMapper(palette=palette, nan_color=nan_colour, low=min_val, high=max_val)

        if revcols and (cfile is None):
            pal = list(self.cmap.palette)
            pal.reverse()
            self.cmap.palette = tuple(pal)

        if cfile is None:
            self.cvals = ColumnDataSource(data={'colours': self.cmap.palette})

        self._bg_col = 'black'
        self._nan_col = nan_colour

        cols = [self._nan_col] * d.size  # Initially empty
        self.datasrc = ColumnDataSource(data={'z': [z], 'd': [d], 'dm': [dm]})
        self.coldatasrc = ColumnDataSource(data={'x': x, 'y': y, 'cols': cols})

        ptools = ['reset, pan, wheel_zoom, box_zoom, save']

        # Default to entire range unless externally controlled
        if xran is None:
            xran = [x.min(), x.max()]
        if yran is None:
            yran = [y.min(), y.max()]

        self.plot = figure(x_axis_label=xlab, y_axis_label=ylab, x_range=xran, y_range=yran, height=height, width=width,
                           background_fill_color=self._bg_col, tools=ptools, toolbar_location='right')

        if type(size) is int:
            self.plot.scatter('x', 'y', marker=self._marker, size=self._sp_size_i, color='cols', source=self.coldatasrc,
                              nonselection_fill_color='cols', selection_fill_color='cols', fill_alpha=alpha, line_alpha=alpha,
                              nonselection_fill_alpha=alpha, selection_fill_alpha=alpha, nonselection_line_alpha=0, selection_line_alpha=alpha,
                              nonselection_line_color='cols', selection_line_color='white', line_width=5)
        else:
            self.plot.circle('x', 'y', radius=self._sp_size_f / 2, color='cols', source=self.coldatasrc,
                             nonselection_fill_color='cols', selection_fill_color='cols', fill_alpha=alpha, line_alpha=alpha,
                             nonselection_fill_alpha=alpha, selection_fill_alpha=alpha, nonselection_line_alpha=0, selection_line_alpha=alpha,
                             nonselection_line_color='cols', selection_line_color='white', line_width=5)

        self.plot.grid.grid_line_color = 'grey'

        self.update_title(0)

        self.plot.title.text_font = 'garamond'
        self.plot.title.text_font_size = '12pt'
        self.plot.title.text_font_style = 'bold'
        self.plot.title.align = 'center'

        self.plot.xaxis.axis_label_text_font = 'garamond'
        self.plot.xaxis.axis_label_text_font_size = '10pt'
        self.plot.xaxis.axis_label_text_font_style = 'bold'

        self.plot.yaxis.axis_label_text_font = 'garamond'
        self.plot.yaxis.axis_label_text_font_size = '10pt'
        self.plot.yaxis.axis_label_text_font_style = 'bold'

        self.update_colours()

        self.cbar = generate_colourbar(self.cmap, cbarwidth=round(height / 20))
        self.plot.add_layout(self.cbar, 'below')

        self.children.append(self.plot)

    def _read_cmap(self, fname: str) -> None:

        """
        Read in the colour scale
        """

        self.cvals = read_colourmap(fname)

    def changed(self, zind: int) -> None:

        """
        Change the row of dm being displayed
        (i.e. a different value of z)
        """

        if (len(self.datasrc.data['dm'][0].shape) > 1) and \
           (zind >= 0) and (zind < self.datasrc.data['dm'][0].shape[0]):

            data = self.datasrc.data
            newdata = data
            d = data['dm'][0][zind]
            newdata['d'] = [d]

            self.datasrc.trigger('data', data, newdata)

    def update_cbar(self) -> None:

        """
        Update the colour scale (needed when the data for display changes)
        """

        if self._autoscale:

            d = self.datasrc.data['d'][0]
            min_val, max_val = get_min_max(d, self._cbdelta)

            self.cmap.low = min_val
            self.cmap.high = max_val

    def update_colours(self) -> None:

        """
        Update the spot colours (needed when the data for display changes)
        """

        colset = self.cvals.data['colours']
        ncols = len(colset)

        d = self.datasrc.data['d'][0]

        data = self.coldatasrc.data
        newdata = data
        cols = data['cols']

        min_val = self.cmap.low
        max_val = self.cmap.high

        for s in range(d.size):

            if numpy.isfinite(d[s]):

                cind = int(round(ncols * (d[s] - min_val) / (max_val - min_val)))
                if cind < 0:
                    cind = 0
                if cind >= ncols:
                    cind = ncols - 1

                cols[s] = colset[cind]

            else:

                cols[s] = self._nan_col

        newdata['cols'] = cols

        self.coldatasrc.trigger('data', data, newdata)

    def update_title(self, zind: int) -> None:

        """
        Update the plot title (needed when the z index changes)
        """

        if self.datasrc.data['z'][0].size > 1:
            self.plot.title.text = self._title_root + ', ' + \
                self._zlab + ' = ' + str(self.datasrc.data['z'][0][zind])
        else:
            self.plot.title.text = self._title_root

    def input_change(self, attrname: str, old: int, new: int) -> None:

        """
        Callback for use with e.g. sliders
        """

        self.changed(new)
        self.update_cbar()
        self.update_colours()
        self.update_title(new)
