"""
ColourMapLP class definition
"""

import numpy

from bokeh.model import DataModel

from bokeh.models import ColumnDataSource, Plot, AdaptiveTicker, NumeralTickFormatter
from bokeh.models.widgets import Button
from bokeh.models.layouts import Column, Row
from bokeh.models.widgets import Div
from bokeh.models.callbacks import CustomJS
from bokeh.models.tools import HoverTool

from bokeh.core.properties import Instance, String

from bokeh.plotting import figure

from bokcolmaps.ColourMap import ColourMap

from bokcolmaps.get_common_kwargs import get_common_kwargs
from bokcolmaps.check_kwargs import check_kwargs


class ColourMapLP(Row, DataModel):

    """
    A ColourMap and a line plot of the data against z at the x and y
    coordinates linked to a custom hover tool.
    """

    cmplot = Instance(ColourMap)
    lpcon = Instance(Column)
    btn = Instance(Button)
    lplot = Instance(Plot)
    lpds = Instance(ColumnDataSource)
    _cmxlab = String
    _cmylab = String
    _js_hover = String

    def __init__(self, x: numpy.array, y: numpy.array, z: numpy.array, dm: numpy.ndarray, **kwargs) -> None:

        """
        All init arguments same as for ColourMap except for additional kwargs...
        cmheight: ColourMap height (pixels)
        cmwidth: ColourMap width (pixels)
        lpheight: line plot height (pixels)
        lpwidth: line plot width (pixels)
        revz: reverse z axis in line plot if True
        hoverdisp: display the hover tool readout if True
        scbutton: create a Snap to Centre button if True (set to False if
                  ColourMapLP not used with Bokeh Server)
        padleft: padding (pixels) to left of line plot (default 0)
        padabove: padding (pixels) above line plot (default 0)
        """

        check_kwargs(kwargs, extra_kwargs=['cmheight', 'cmwidth', 'lpheight', 'lpwidth', 'revz', 'hoverdisp', 'scbutton', 'padleft', 'padabove'])

        palette, cfile, revcols, xlab, ylab, zlab, dmlab, \
            rmin, rmax, xran, yran, alpha, nan_colour = get_common_kwargs(**kwargs)

        cmheight = kwargs.get('cmheight', 575)
        cmwidth = kwargs.get('cmwidth', 500)
        lpheight = kwargs.get('lpheight', 500)
        lpwidth = kwargs.get('lpwidth', 300)
        revz = kwargs.get('revz', False)
        hoverdisp = kwargs.get('hoverdisp', True)
        scbutton = kwargs.get('scbutton', False)
        padleft = kwargs.get('padleft', 0)
        padabove = kwargs.get('padabove', 0)
        hover = kwargs.get('hover', True)

        super().__init__()

        # Data source for the line plot
        xi = round(x.size / 2)
        yi = round(y.size / 2)
        self.lpds = ColumnDataSource(data={'x': dm[:, yi, xi], 'y': z})

        self.cmplot = ColourMap(x, y, z, dm,
                                palette=palette, cfile=cfile, revcols=revcols,
                                xlab=xlab, ylab=ylab, zlab=zlab, dmlab=dmlab,
                                height=cmheight, width=cmwidth, rmin=rmin,
                                rmax=rmax, xran=xran, yran=yran, hover=hover,
                                alpha=alpha, nan_colour=nan_colour)

        # Custom hover tool to render profile at cursor position in line plot

        self._js_hover = self.cmplot._js_hover + """
        var lpdata = lpsrc.data;
        var lx = lpdata['x'];

        if ((xind >= 0) && (xind < x.length) && (yind >= 0) && (yind < y.length)) {
            var dm = data['dm'][0];

            var skip = x.length*y.length;
            for (var i = 0; i < lx.length; i++) {
                lx[i] = dm[zind + i*skip];
            }
        lpsrc.change.emit();
        }
        """

        cjs = CustomJS(args={'datasrc': self.cmplot.datasrc,
                             'lpsrc': self.lpds},
                       code=self._js_hover)
        if hoverdisp:
            htool = HoverTool(tooltips=[(xlab, '@xp{0.00}'),
                                        (ylab, '@yp{0.00}'),
                                        (dmlab, '@dp{0.00}')],
                              callback=cjs, point_policy='follow_mouse')
        else:
            htool = HoverTool(tooltips=None, callback=cjs)

        self.cmplot.plot.add_tools(htool)

        self.lplot = figure(x_axis_label=dmlab, y_axis_label=zlab,
                            height=lpheight, width=lpwidth,
                            tools=['reset, pan, wheel_zoom, box_zoom, save'],
                            toolbar_location='right')

        if revz:
            self.lplot.y_range.start = z[-1]
            self.lplot.y_range.end = z[0]
        else:
            self.lplot.y_range.start = z[0]
            self.lplot.y_range.end = z[-1]
        if (rmin is not None) and (rmax is not None):
            self.lplot.x_range.start = rmin
            self.lplot.x_range.end = rmax

        self.lplot.line('x', 'y', source=self.lpds, line_color='blue',
                        line_width=2, line_alpha=1)

        self.lplot.title.text = 'Profile at cursor'

        self.lplot.title.text_font = 'garamond'
        self.lplot.title.text_font_size = '12pt'
        self.lplot.title.text_font_style = 'bold'
        self.lplot.title.align = 'center'

        self.lplot.xaxis.axis_label_text_font = 'garamond'
        self.lplot.xaxis.axis_label_text_font_size = '10pt'
        self.lplot.xaxis.axis_label_text_font_style = 'bold'

        self.lplot.xaxis[0].ticker = AdaptiveTicker(desired_num_ticks=5)
        self.lplot.xaxis[0].formatter = NumeralTickFormatter(format="0.00")

        self.lplot.yaxis.axis_label_text_font = 'garamond'
        self.lplot.yaxis.axis_label_text_font_size = '10pt'
        self.lplot.yaxis.axis_label_text_font_style = 'bold'

        self.lpcon = Column(Div(text='', width=lpwidth, height=padabove), self.lplot)

        if scbutton:
            self.btn = Button(label='Snap to centre', align='center')
            self.btn.on_click(self.centre_lp)
            self.lpcon.children.append(self.btn)
        else:
            self.btn = Button()

        self.children.append(self.cmplot)
        self.children.append(Div(text='', width=padleft, height=padabove + lpheight))
        self.children.append(self.lpcon)

        self._cmxlab = xlab
        self._cmylab = ylab

        self.centre_lp()

    def centre_lp(self) -> None:

        """
        When the button is clicked, update the line plot to correspond to the
        centre of the image.
        """

        # Get current colourmap axes centre points

        x = (self.cmplot.plot.x_range.start + self.cmplot.plot.x_range.end) / 2
        y = (self.cmplot.plot.y_range.start + self.cmplot.plot.y_range.end) / 2

        # Find closet x and y indexes to centre of ranges

        ds = self.cmplot.datasrc.data
        xa = ds['x'][0]
        ya = ds['y'][0]
        xi, = numpy.where(xa >= x)
        xind = yind = 0
        if xi.size > 0:
            xind = xi[0]
            if (xind > 0) and (abs(xa[xind - 1] - x) < abs(xa[xind] - x)):
                xind = xind - 1
        yi, = numpy.where(ya >= y)
        if yi.size > 0:
            yind = yi[0]
            if (yind > 0) and (abs(ya[yind - 1] - y) < abs(ya[yind] - y)):
                yind = yind - 1

        # Update line plot source

        if (xi.size > 0) and (yi.size > 0):
            skip = xa.size * ya.size
            self.lpds.data['x'] = ds['dm'][0][yind * xa.size + xind::skip]
