======
README
======

Want to see 3D brain data in the IPython_ notebook? Now you can by using Papaya_, a Javascript library for viewing medical images in the browser, and this little bit of code.

Install
-------

Clone this repository to your computer, and run the setup script.

>>> python setup.py


Use
---

Open a new IPython_ notebook

    from nbpapaya import Brain, clear_brain

Then show a brain:

    Brain("/path/to/your/brain.nii",port=<your ipython notebook port. Default is 8888>)

Or show overlaid brains

    Brain(["/path/to/brain1.nii","/path/to/brain2.nii"],8888)

You can play around with the color maps and intensity ranges on the Papaya_ javascript interface.

Also, some files are created in the directory of your notebook to make it work. When you're done, clean up:

    clear_brain()

The file papaya_viewer.html and the papaya_data folder are deleted.


Troubleshoot
------------

Things might go wrong because I wrote this quickly. If you don't see anything, make sure you called Brain with the correct port. If you did, make sure that papaya.js and papaya.css exist in ~/.ipython/profile_default/static/custom/. If nothing is there, move the files in there. Also email me: akeshavan@ucla.edu. 



.. _IPython: http://ipython.org/notebook.html
.. _Papaya: https://github.com/rii-mango/Papaya/
