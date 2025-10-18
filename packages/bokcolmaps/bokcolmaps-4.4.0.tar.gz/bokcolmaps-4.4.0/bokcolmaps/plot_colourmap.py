"""
plot_colourmap function definition
"""

import numpy

from bokeh.palettes import Turbo256
from bokeh.plotting import show
from bokeh.io import output_file

from bokcolmaps.ColourMap import ColourMap
from bokcolmaps.ColourMapSlider import ColourMapSlider
from bokcolmaps.ColourMapLPSlider import ColourMapLPSlider


def plot_colourmap(data: numpy.ndarray, **kwargs) -> None:

    """
    A convenience function to quickly plot a colour map. The only required input is the data array,
    but keyword arguments can be used to customise the plot.

    args...
        data: 2D or 3D NumPy array
    kwargs...
        x: x axis values
        y: y axis values
        z: z axis values
        height: colour map height (pixels)
        width: colour map height (pixels)
        xlab: x axis label
        ylab: y axis label
        zlab: z axis label
        dmlab: data label
        line_plot: line plot on True for hover tool with 3D data
        rmin: minimum value for the colour scale (no autoscaling if neither this nor rmax is None)
        rmax: maximum value for the colour scale
        revz: reverse z axis in line plot if True
        palette: A Bokeh palette for the colour mapping
        revcols: reverse colour palette if True
        alpha: global image alpha
        nan_colour: NaN colour
        fname: output file name
    """

    # Inputs

    x = kwargs.get('x', None)
    y = kwargs.get('y', None)
    z = kwargs.get('z', None)

    height = kwargs.get('height', 575)
    width = kwargs.get('width', 500)

    xlab = kwargs.get('xlab', 'x')
    ylab = kwargs.get('ylab', 'y')
    zlab = kwargs.get('zlab', 'Index')
    dmlab = kwargs.get('dmlab', 'Data')

    lp = kwargs.get('line_plot', 'True')
    rmin = kwargs.get('rmin', None)
    rmax = kwargs.get('rmax', None)
    revz = kwargs.get('revz', False)

    palette = kwargs.get('palette', Turbo256)
    revcols = kwargs.get('revcols', False)
    alpha = kwargs.get('alpha', 1)
    nan_colour = kwargs.get('nan_colour', 'Grey')

    fname = kwargs.get('fname', 'colourmap.html')

    # Dimensions

    is3D = True if len(data.shape) == 3 else False

    if is3D:
        nz, ny, nx = data.shape
        if nz == 1:
            is3D = False
            data = data[0]
    else:
        ny, nx = data.shape
        nz = 1
        lp = False

    if x is None:
        x = numpy.arange(nx)
    if y is None:
        y = numpy.arange(ny)
    if is3D:
        if z is None:
            z = numpy.arange(nz)
    else:
        z = numpy.array([0])

    # Plots

    if is3D:
        if lp:
            cmap_class = ColourMapLPSlider
        else:
            cmap_class = ColourMapSlider
    else:
        cmap_class = ColourMap

    if lp:

        cmap = cmap_class(x, y, z, data, cmheight=height, cmwidth=width, lpheight=height,
                          xlab=xlab, ylab=ylab, zlab=zlab, dmlab=dmlab, rmin=rmin, rmax=rmax, revz=revz,
                          palette=palette, revcols=revcols, alpha=alpha, nan_colour=nan_colour)

    else:

        cmap = cmap_class(x, y, z, data, height=height, width=width,
                          xlab=xlab, ylab=ylab, zlab=zlab, dmlab=dmlab, rmin=rmin, rmax=rmax,
                          palette=palette, revcols=revcols, alpha=alpha, nan_colour=nan_colour)

    # Display and save

    output_file(fname, mode='inline')
    show(cmap)
