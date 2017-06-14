import os
import shutil
import weakref
from json import dumps as json
from tempfile import mktemp, NamedTemporaryFile
from warnings import warn
#from nipype.utils.filemanip import split_filename

def split_filename(fname):
    """Split a filename into parts: path, base filename and extension.

    Parameters
    ----------
    fname : str
        file or path name

    Returns
    -------
    pth : str
        base path from fname
    fname : str
        filename from fname, without extension
    ext : str
        file extension from fname

    Examples
    --------
    >>> from nipype.utils.filemanip import split_filename
    >>> pth, fname, ext = split_filename('/home/data/subject.nii.gz')
    >>> pth
    '/home/data'

    >>> fname
    'subject'

    >>> ext
    '.nii.gz'

    """

    special_extensions = [".nii.gz"]

    pth, fname = os.path.split(fname)

    ext = None
    for special_ext in special_extensions:
        ext_len = len(special_ext)
        if len(fname) > ext_len and fname[-ext_len:].lower() == special_ext.lower():
            ext = fname[-ext_len:]
            fname = fname[:-ext_len]
            break
    if not ext:
        fname, ext = os.path.splitext(fname)

    return pth, fname, ext


open_brains = weakref.WeakValueDictionary()

def _parse_options(file_names, options, image_options):
    if options is None:
        options_json = "";
    else:
        opt = []
        for option_name, value in options.items():
            line = "params['{}'] = {};".format(option_name, json(value))
            opt.append(line)
        options_json = "\n".join(opt)

    if image_options is None:
        image_options_json = ""
    else:
        opt = []
        for file, image_options in zip(sorted(file_names), image_options):
            line = "params['{}'] = {};".format(file, json(image_options))
            opt.append(line)
        image_options_json = "\n".join(opt)
    return options_json, image_options_json

def clear_brain():
    """Remove all the files the Brain object made to show you things.
    You must re-run all cells to reload the data"""

    if os.path.exists(os.path.abspath("papaya_data")):
        shutil.rmtree(os.path.abspath("papaya_data"))

def get_example_data():
    vtk = "http://roygbiv.mindboggle.info/data/mindboggled/Twins-2-1/labels/left_cortical_surface/freesurfer_cortex_labels.vtk"
    nifti = ""
    from subprocess import check_call
    import os

    folder = os.path.abspath("nppapaya_example_data")
    if not os.path.exists(folder):
        os.makedirs(folder)
    cmd = ["wget", vtk]
    check_call(cmd, cwd=folder)
