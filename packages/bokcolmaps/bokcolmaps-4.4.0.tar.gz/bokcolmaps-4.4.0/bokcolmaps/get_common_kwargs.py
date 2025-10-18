"""
get_common_kwargs function definition
"""

from bokeh.palettes import Turbo256

common_kwargs = ['palette', 'cfile', 'revcols', 'xlab', 'ylab', 'zlab', 'dmlab', 'rmin', 'rmax', 'xran', 'yran', 'alpha', 'nan_colour']


def get_common_kwargs(**kwargs: dict) -> tuple:

    """
    Get common kwargs for the ColourMap/ColourMap3, SpotPlot and derived classes
    kwargs...
        palette: A Bokeh palette for the colour mapping
        cfile: path to a file RGBA floats for palette (will be used instead of palette if not None)
        revcols: reverse colour palette if True
        xlab: x axis label
        ylab: y axis label
        zlab: z axis label
        dmlab: data label
        rmin: minimum value for the colour scale (no autoscaling if neither this nor rmax is None)
        rmax: maximum value for the colour scale
        xran: x axis range
        yran: y axis range
        alpha: global image alpha
        nan_colour: NaN colour
    """

    palette = kwargs.get('palette', Turbo256)
    cfile = kwargs.get('cfile', None)
    revcols = kwargs.get('revcols', False)
    xlab = kwargs.get('xlab', 'x')
    ylab = kwargs.get('ylab', 'y')
    zlab = kwargs.get('zlab', 'Index')
    dmlab = kwargs.get('dmlab', 'Data')
    rmin = kwargs.get('rmin', None)
    rmax = kwargs.get('rmax', None)
    xran = kwargs.get('xran', None)
    yran = kwargs.get('yran', None)
    alpha = kwargs.get('alpha', 1)
    nan_colour = kwargs.get('nan_colour', 'Grey')

    return palette, cfile, revcols, xlab, ylab, zlab, dmlab, \
        rmin, rmax, xran, yran, alpha, nan_colour
