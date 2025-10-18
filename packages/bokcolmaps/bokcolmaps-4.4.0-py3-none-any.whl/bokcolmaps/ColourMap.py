"""
ColourMap class definition
"""

import numpy

from bokeh.model import DataModel

from bokeh.models import ColumnDataSource, Plot, ColorBar, HoverTool
from bokeh.models.mappers import LinearColorMapper
from bokeh.models.ranges import Range1d
from bokeh.models.layouts import Column
from bokeh.models.callbacks import CustomJS

from bokeh.core.properties import Instance, String, Float, Bool, Int

from bokeh.plotting import figure

from bokcolmaps.get_common_kwargs import get_common_kwargs
from bokcolmaps.check_kwargs import check_kwargs
from bokcolmaps.generate_colourbar import generate_colourbar
from bokcolmaps.read_colourmap import read_colourmap
from bokcolmaps.get_min_max import get_min_max


class ColourMap(Column, DataModel):

    """
    Plots an image as a colour map with a user-defined colour scale and
    creates a hover readout. The image must be on a uniform grid to be
    rendered correctly and for the data cursor to provide correct readout.
    """

    plot = Instance(Plot)
    cbar = Instance(ColorBar)

    datasrc = Instance(ColumnDataSource)
    mmsrc = Instance(ColumnDataSource)
    cvals = Instance(ColumnDataSource)

    cmap = Instance(LinearColorMapper)

    _title_root = String
    _zlab = String

    _autoscale = Bool
    _revcols = Bool

    _xsize = Int
    _ysize = Int
    _zsize = Int

    _cbdelta = Float

    _js_hover = String

    cjs_slider = Instance(CustomJS)

    def __init__(self, x: numpy.array, y: numpy.array, z: numpy.array, dm: numpy.ndarray, **kwargs) -> None:

        """
        args...
            x: 1D NumPy array of x coordinates
            y: 1D NumPy array of y coordinates
            z: 1D NumPy array of z coordinates
            dm: 3D NumPy array of the data for display, dimensions z.size, y.size, x.size
        kwargs: all in get_common_kwargs plus...
            height: plot height (pixels)
            width: plot width (pixels)
            hover: Boolean to enable hover tool readout
        """

        check_kwargs(kwargs, extra_kwargs=['height', 'width', 'hover'])

        palette, cfile, revcols, xlab, ylab, zlab, dmlab, \
            rmin, rmax, xran, yran, alpha, nan_colour = get_common_kwargs(**kwargs)

        height = kwargs.get('height', 575)
        width = kwargs.get('width', 500)
        hover = kwargs.get('hover', True)

        super().__init__()

        self._cbdelta = 0.01  # Min colourbar range (used if values are equal)

        self._title_root = dmlab
        self._zlab = zlab

        is3D = True if len(dm.shape) == 3 else False

        self._autoscale = True
        if (rmin is not None) and (rmax is not None):
            self._autoscale = False
        else:
            if rmin is None:
                if is3D:
                    rmin = numpy.min(dm[0])
                else:
                    rmin = numpy.min(dm)
            if rmax is None:
                if is3D:
                    rmax = numpy.max(dm[0])
                else:
                    rmax = numpy.max(dm)

        if is3D:
            self._zsize, self._ysize, self._xsize = dm.shape
        else:
            self._ysize, self._xsize = dm.shape
            self._zsize = 1

        if (x.size != self._xsize) or (y.size != self._ysize):
            raise ValueError('x or y array size not consistent with dimensions of dm array')

        if is3D:  # Default to first slice
            d = dm[0]
        else:
            d = dm

        # Get minimum and maximum values for the colour mapping

        if self._autoscale:
            minvals = [None] * self._zsize
            maxvals = [None] * self._zsize
            for zind in range(self._zsize):
                minvals[zind], maxvals[zind] = get_min_max(dm[zind], self._cbdelta)
        else:
            minvals = [rmin] * self._zsize
            maxvals = [rmax] * self._zsize
        self.mmsrc = ColumnDataSource(data={'minvals': minvals, 'maxvals': maxvals})

        dm = dm.flatten()

        # All variables stored as single item lists in order to be the same
        # length (as required by ColumnDataSource)

        self.datasrc = ColumnDataSource(data={'x': [x], 'y': [y], 'z': [z],
                                              'image': [d], 'dm': [dm],
                                              'xp': [0], 'yp': [0], 'dp': [0]})

        # JS code for slider in classes ColourMapSlider
        # and ColourMapLPSlider

        js_slider = """
        var dind = cb_obj['value'];
        var data = datasrc.data;

        var x = data['x'][0];
        var y = data['y'][0];
        var d = data['image'][0];
        var dm = data['dm'][0];

        var nx = x.length;
        var ny = y.length;

        var sind = dind*nx*ny;
        for (var i = 0; i < nx*ny; i++) {
            d[i] = dm[sind+i];
        }

        datasrc.change.emit();

        var minval = mmsrc.data['minvals'][dind];
        var maxval = mmsrc.data['maxvals'][dind];

        cmap.low = minval;
        cmap.high = maxval;

        var z = data['z'][0];
        cmplot.title.text = title_root + ', ' + zlab + ' = ' + z[dind].toString();
        """

        # JS code defined whether or not hover tool used as may be needed in
        # class ColourMapLP

        self._js_hover = """
        var geom = cb_data['geometry'];
        var data = datasrc.data;

        var hx = geom.x;
        var hy = geom.y;

        var x = data['x'][0];
        var y = data['y'][0];
        var d = data['image'][0];

        var dx = x[1] - x[0];
        var dy = y[1] - y[0];
        var xind = Math.floor((hx + dx/2 - x[0])/dx);
        var yind = Math.floor((hy + dy/2 - y[0])/dy);

        if ((xind >= 0) && (xind < x.length) && (yind >= 0) && (yind < y.length)) {
            data['xp'] = [x[xind]];
            data['yp'] = [y[yind]];
            var zind = yind*x.length + xind;
            data['dp'] = [d[zind]];
        }
        """

        ptools = ['reset, pan, wheel_zoom, box_zoom, save']

        if hover:
            cjs_hover = CustomJS(args={'datasrc': self.datasrc},
                                 code=self._js_hover)
            htool = HoverTool(tooltips=[(xlab, '@xp{0.00}'),
                                        (ylab, '@yp{0.00}'),
                                        (dmlab, '@dp{0.00}')],
                              callback=cjs_hover, point_policy='follow_mouse')
            ptools.append(htool)

        # Default to whole range unless externally controlled

        xoffs = (x[0] - x[1]) / 2
        if xran is None:
            xran = Range1d(start=x[0], end=x[-1])
        else:
            xoffs += x[0] - xran.start
        yoffs = (y[0] - y[1]) / 2
        if yran is None:
            yran = Range1d(start=y[0], end=y[-1])
        else:
            yoffs += y[0] - yran.start

        # Get the colourmap

        self._revcols = revcols
        self._get_cmap(cfile, rmin, rmax, palette, nan_colour)

        # Create the plot

        self.plot = figure(x_axis_label=xlab, y_axis_label=ylab,
                           x_range=xran, y_range=yran,
                           height=height, width=width,
                           tools=ptools, toolbar_location='right')

        self.cjs_slider = CustomJS(args={'datasrc': self.datasrc, 'mmsrc': self.mmsrc,
                                         'cmap': self.cmap, 'cmplot': self.plot,
                                         'title_root': self._title_root, 'zlab': self._zlab},
                                   code=js_slider)

        # Set the title

        if len(self.datasrc.data['z'][0]) > 1:
            self.plot.title.text = self._title_root + ', ' + \
                self._zlab + ' = ' + str(self.datasrc.data['z'][0][0])
        else:
            self.plot.title.text = self._title_root

        self.plot.title.text_font = 'garamond'
        self.plot.title.text_font_size = '12pt'
        self.plot.title.text_font_style = 'bold'
        self.plot.title.align = 'center'

        # The image is displayed such that x and y coordinate values
        # correspond to the centres of rectangles

        pw = abs(x[-1] - x[0]) + abs(x[1] - x[0])
        ph = abs(y[-1] - y[0]) + abs(y[1] - y[0])

        xs = xran.start
        if xs is None:
            xs = 0
        else:
            xs += xoffs

        ys = yran.start
        if ys is None:
            ys = 0
        else:
            ys += yoffs

        orig_str_x = 'left'
        orig_str_y = 'bottom'

        if x[-1] < x[0]:
            orig_str_x = 'right'
        if y[-1] < y[0]:
            orig_str_y = 'top'

        origin = orig_str_y + '_' + orig_str_x

        self.plot.image('image', source=self.datasrc, x=xs, y=ys,
                        dw=pw, dh=ph, color_mapper=self.cmap, global_alpha=alpha,
                        origin=origin, anchor=origin)

        # Needed for HoverTool...

        self.plot.rect(x=(x[0] + x[-1]) / 2, y=(y[0] + y[-1]) / 2, width=pw, height=ph,
                       line_alpha=0, fill_alpha=0, source=self.datasrc)

        self.plot.xaxis.axis_label_text_font = 'garamond'
        self.plot.xaxis.axis_label_text_font_size = '10pt'
        self.plot.xaxis.axis_label_text_font_style = 'bold'

        self.plot.yaxis.axis_label_text_font = 'garamond'
        self.plot.yaxis.axis_label_text_font_size = '10pt'
        self.plot.yaxis.axis_label_text_font_style = 'bold'

        self.cbar = generate_colourbar(self.cmap, cbarwidth=round(height / 20))
        self.plot.add_layout(self.cbar, 'below')

        self.children.append(self.plot)

    def _get_cmap(self, cfile: str, rmin: float, rmax: float, palette: list, nan_colour: str) -> None:

        """
        Get the colour mapper
        """

        if self._autoscale:
            min_val, max_val = get_min_max(self.datasrc.data['image'][0], self._cbdelta)
        else:
            min_val = rmin
            max_val = rmax

        if cfile is not None:
            self._read_cmap(cfile)
            palette = self.cvals.data['colours']
        else:
            self.cvals = ColumnDataSource(data={'colours': []})

        if self._revcols:
            pal = list(palette)
            pal.reverse()
            palette = tuple(pal)

        self.cmap = LinearColorMapper(palette=palette, nan_color=nan_colour, low=min_val, high=max_val)

    def _read_cmap(self, fname: str) -> None:

        """
        Read in the colour scale.
        """

        self.cvals = read_colourmap(fname)

    def update_image(self, zind: int) -> None:

        """
        Updates the data for display without slider movement
        (e.g. for Bokeh Server applications)
        """

        d = self.datasrc.data['dm'][0][zind * self._xsize * self._ysize:
                                       (zind + 1) * self._xsize * self._ysize]
        self.datasrc.patch({'image': [(0, d.reshape((self._ysize, self._xsize)))]})

        if self._autoscale:
            self.update_cbar()

    def update_cbar(self) -> None:

        """
        Update the colour scale (needed when the data for display changes).
        """

        d = self.datasrc.data['image'][0]
        min_val, max_val = get_min_max(d, self._cbdelta)
        self.cmap.low = min_val
        self.cmap.high = max_val

    def set_autoscale(self, val: bool) -> None:

        """
        Switch autoscaling on or off
        """

        self._autoscale = val

    def get_autoscale(self) -> bool:

        """
        Return autoscaling setting
        """

        return self._autoscale
