from distutils.core import setup

setup(name='nbpapaya',
      version='1.0',
      description='Papaya viewer in the IPython notebook',
      author='Anisha',
      author_email='akeshavan@ucla.edu',
      url=None,
      packages=['nbpapaya'],
      package_data={"nbpapaya":["papaya.js",
                               "papaya.css",
                               "three.js/build/*",
                               "three.js/libs/stats.min.js"
                               "three.js/examples/js/loaders/*/*/*",
                               "three.js/examples/js/controls/TrackballControls.js"]}
     )
