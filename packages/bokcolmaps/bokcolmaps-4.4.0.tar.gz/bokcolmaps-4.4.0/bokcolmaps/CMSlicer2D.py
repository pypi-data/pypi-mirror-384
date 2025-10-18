"""
CMSlicer2D class definition
"""

import numpy

from bokeh.model import DataModel
from bokeh.models.layouts import Column, Row
from bokeh.models.widgets import Div
from bokeh.events import Tap
from bokeh.core.properties import Instance
from bokeh.plotting import figure
from bokeh.models.glyphs import Line

from interpg.interp_2d_line import interp_2d_line

from bokcolmaps.CMSlicer import CMSlicer
from bokcolmaps.ColourMap import ColourMap


class CMSlicer2D(CMSlicer, DataModel):

    """
    A ColourMap with the ability to slice the plot with a line through the x-y plane to give a separate line plot.
    """

    cmap = Instance(ColourMap)

    def __init__(self, x: numpy.array, y: numpy.array, z: numpy.array, dm: numpy.ndarray, **kwargs) -> None:

        """
        All init arguments same as for CMSlicer with additional args...
            z: 1D NumPy array of z coordinates
            dm: 2D NumPy array of the data for display, y.size, x.size
        """

        super().__init__(x, y, **kwargs)

        params = self.cmap_params.data

        self.cmap = ColourMap(x, y, z, dm, palette=params['palette'][0], cfile=params['cfile'][0],
                              revcols=params['revcols'][0], xlab=params['xlab'][0],
                              ylab=params['ylab'][0], zlab=params['zlab'][0], dmlab=params['dmlab'][0],
                              height=params['cmheight'][0], width=params['cmwidth'][0],
                              rmin=params['rmin'][0], rmax=params['rmax'][0],
                              xran=params['xran'][0], yran=params['yran'][0],
                              hover=params['hoverdisp'][0],
                              alpha=params['alpha'][0], nan_colour=params['nan_colour'][0])

        self.cmap.plot.on_event(Tap, self.toggle_select)

        self.lr = self.cmap.plot.add_glyph(self.sl_src, Line(x='x', y='y', line_color='white',
                                                             line_width=5, line_dash='dashed', line_alpha=1))

        self.children.append(self.cmap)

        self.children.append(Column(children=[Div(text='',
                                                  width=params['spwidth'][0] + params['padleft'][0],
                                                  height=params['padabove'][0]),
                                              Row(children=[Div(text='',
                                                                width=params['padleft'][0],
                                                                height=params['spheight'][0]),
                                                            figure(toolbar_location=None)])]))

        self._change_slice()

    def _change_slice(self) -> None:

        """
        Change the slice displayed in the separate figure
        """

        c_i, r_i = self.get_interp_coords(self.cmap.datasrc)

        x = self.cmap.datasrc.data['x'][0]
        y = self.cmap.datasrc.data['y'][0]

        dm = self.cmap.datasrc.data['dm'][0]
        dm = numpy.reshape(dm, [y.size, x.size])

        dm_i, z_i = interp_2d_line(y, x, dm, c_i)

        iplot = figure(x_axis_label=self.cmap_params.data['splab'][0], y_axis_label=self.cmap_params.data['dmlab'][0],
                       height=self.cmap_params.data['spheight'][0], width=self.cmap_params.data['spwidth'][0],
                       x_range=[r_i[0], r_i[-1]], toolbar_location='right')

        iplot.line(r_i, dm_i, line_color='blue', line_width=2, line_alpha=1)

        iplot.y_range.start = numpy.min(dm_i[numpy.isfinite(dm_i)])
        iplot.y_range.end = numpy.max(dm_i[numpy.isfinite(dm_i)])

        if self.cmap_params.data['revz'][0]:
            iplot.y_range.start, iplot.y_range.end = iplot.y_range.end, iplot.y_range.start

        iplot.title.text = self.cmap_params.data['dmlab'][0] + ' along track'

        iplot.title.text_font = 'garamond'
        iplot.title.text_font_size = '12pt'
        iplot.title.text_font_style = 'bold'
        iplot.title.align = 'center'

        iplot.xaxis.axis_label_text_font = 'garamond'
        iplot.xaxis.axis_label_text_font_size = '10pt'
        iplot.xaxis.axis_label_text_font_style = 'bold'
        iplot.yaxis.axis_label_text_font = 'garamond'
        iplot.yaxis.axis_label_text_font_size = '10pt'
        iplot.yaxis.axis_label_text_font_style = 'bold'

        self.children[1].children[1].children[1] = iplot
