from setuptools import setup, find_packages

setup(name='bokcolmaps',
      version='4.4.0',
      description='Colour map plots based on the Bokeh visualisation library',
      long_description="""
# bokcolmaps

### Colour map plots based on the Bokeh visualisation library

----------

Get started with:

import numpy  
from bokcolmaps.plot_colourmap import plot_colourmap  
data = numpy.random.rand(3, 4, 5)  
plot_colourmap(data)

or see bokcolmaps.Examples.plot_colourmap_example
      """,
      long_description_content_type='text/markdown',
      author='Marcus Donnelly',
      author_email='marcus.k.donnelly@gmail.com',
      url='https://github.com/marcuskd/bokcolmaps',
      license='BSD 3-Clause',
      classifiers=['Development Status :: 5 - Production/Stable',
                   'Intended Audience :: Science/Research',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: MIT License',
                   'Programming Language :: Python :: 3',
                   'Topic :: Scientific/Engineering'
                   ],
      keywords=['Bokeh',
                '2D Plot',
                '3D Plot'
                ],
      packages=find_packages(),
      install_requires=['numpy >= 1.26',
                        'bokeh >= 3.6',
                        'interpg >= 1'
                        ],
      include_package_data=True,
      )
