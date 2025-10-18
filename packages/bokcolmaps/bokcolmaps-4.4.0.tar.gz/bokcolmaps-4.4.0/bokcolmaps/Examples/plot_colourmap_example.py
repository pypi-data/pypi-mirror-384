"""
This demonstrates the quickest way to produce a colourmap. To run this example at the command line enter:
python plot_colourmap_example.py
"""

from bokcolmaps.plot_colourmap import plot_colourmap
from bokcolmaps.Examples import example_data

_, _, _, data = example_data()

plot_colourmap(data[0])  # 2D plot
plot_colourmap(data, fname='colourmap3D.html')  # 3D plot
