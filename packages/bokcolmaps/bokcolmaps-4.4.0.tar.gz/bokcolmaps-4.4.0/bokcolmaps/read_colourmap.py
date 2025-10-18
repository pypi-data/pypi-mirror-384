"""
read_colourmap function definition
"""

from bokeh.models import ColumnDataSource


def read_colourmap(fname: str) -> ColumnDataSource:

    """
    Read in the colour scale.
    args...
        fname: path to file containing comma separated RGBA floats
    """

    f = open(fname, 'rt')
    cmap = []
    for l in f:
        valstrs = l[:-1].split(',')
        vals = []
        for s in valstrs[:-1]:
            vals.append(round(255 * float(s)))
        vtup = tuple(vals)
        cmap.append('#%02x%02x%02x' % vtup)  # Format as hex triple
    f.close()
    cvals = ColumnDataSource(data={'colours': cmap})

    return cvals
