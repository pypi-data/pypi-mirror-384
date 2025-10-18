"""
CMSlicer3D class definition
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
from bokcolmaps.ColourMapLPSlider import ColourMapLPSlider
from bokcolmaps.ColourMap import ColourMap


class CMSlicer3D(CMSlicer, DataModel):

    """
    A ColourMapLPSlider with the ability to slice the plot with a line through the x-y plane which gives the
    profile against z along the line as a separate ColourMap.
    """

    cmap = Instance(ColourMapLPSlider)

    def __init__(self, x: numpy.array, y: numpy.array, z: numpy.array, dm: numpy.ndarray, **kwargs) -> None:

        """
        All init arguments same as for CMSlicer with additional args...
            z: 1D NumPy array of z coordinates
            dm: 3D NumPy array of the data for display, dimensions z.size, y.size, x.size
        and additional kwargs...
            lpheight: line plot height (pixels) for ColourMapLP
            lpwidth: line plot width (pixels) for ColourMapLP
            sphoverdisp: display the hover tool readout in the slice plot if True
            padleftlp: padding (pixels) to left of ColourMapLP line plot (default 0)
            padabovelp: padding (pixels) above ColourMapLP line plot (default 0)
        """

        super().__init__(x, y, **kwargs)

        params = self.cmap_params.data

        params['lpheight'] = [kwargs.get('lpheight', 500)]
        params['lpwidth'] = [kwargs.get('lpwidth', 300)]
        params['sphoverdisp'] = [kwargs.get('sphoverdisp', True)]
        params['padleftlp'] = [kwargs.get('padleftlp', 0)]
        params['padabovelp'] = [kwargs.get('padabovelp', 0)]
        params['scbutton'] = [True]

        self.cmap = ColourMapLPSlider(x, y, z, dm, palette=params['palette'][0], cfile=params['cfile'][0],
                                      revcols=params['revcols'][0], xlab=params['xlab'][0],
                                      ylab=params['ylab'][0], zlab=params['zlab'][0], dmlab=params['dmlab'][0],
                                      cmheight=params['cmheight'][0], cmwidth=params['cmwidth'][0],
                                      lpheight=params['lpheight'][0], lpwidth=params['lpwidth'][0],
                                      rmin=params['rmin'][0], rmax=params['rmax'][0],
                                      xran=params['xran'][0], yran=params['yran'][0],
                                      revz=params['revz'][0], hoverdisp=params['hoverdisp'][0],
                                      scbutton=params['scbutton'][0],
                                      alpha=params['alpha'][0], nan_colour=params['nan_colour'][0],
                                      padleft=params['padleftlp'][0], padabove=params['padabovelp'][0])

        self.cmap.cmaplp.cmplot.plot.on_event(Tap, self.toggle_select)

        self.lr = self.cmap.cmaplp.cmplot.plot.add_glyph(self.sl_src, glyph=Line(x='x', y='y', line_color='white',
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
        Change the slice displayed in the separate line plot
        """

        c_i, r_i = self.get_interp_coords(self.cmap.cmaplp.cmplot.datasrc)

        x = self.cmap.cmaplp.cmplot.datasrc.data['x'][0]
        y = self.cmap.cmaplp.cmplot.datasrc.data['y'][0]
        z = self.cmap.cmaplp.cmplot.datasrc.data['z'][0]

        dm = self.cmap.cmaplp.cmplot.datasrc.data['dm'][0]
        dm = numpy.reshape(dm, [z.size, y.size, x.size])

        dm_i, z_i = interp_2d_line(y, x, dm, c_i, z=z)

        if self.cmap_params.data['revz'][0]:
            z_i = numpy.flipud(z_i)
            dm_i = numpy.flipud(dm_i)

        iplot = ColourMap(r_i, z_i, [0], dm_i, palette=self.cmap_params.data['palette'][0],
                          cfile=self.cmap_params.data['cfile'][0], revcols=self.cmap_params.data['revcols'][0],
                          xlab=self.cmap_params.data['splab'][0], ylab=self.cmap_params.data['zlab'][0],
                          dmlab=self.cmap_params.data['dmlab'][0] + ' along track',
                          height=self.cmap_params.data['spheight'][0], width=self.cmap_params.data['spwidth'][0],
                          rmin=self.cmap_params.data['rmin'][0], rmax=self.cmap_params.data['rmax'][0],
                          alpha=self.cmap_params.data['alpha'][0], nan_colour=self.cmap_params.data['nan_colour'][0],
                          hover=self.cmap_params.data['sphoverdisp'])

        self.children[1].children[1].children[1] = iplot
