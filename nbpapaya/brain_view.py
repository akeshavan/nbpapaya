import os
import shutil
import weakref
from json import dumps as json
from tempfile import mktemp, NamedTemporaryFile
from warnings import warn
from nipype.utils.filemanip import split_filename

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
        for file, image_options in zip(file_names, image_options):
            line = "params['{}'] = {};".format(file, json(image_options))
            opt.append(line)
        image_options_json = "\n".join(opt)
    return options_json, image_options_json

class Brain(object):

    def _repr_html_(self):
        return """<iframe src="http://localhost:%d/files/papaya_data/%s.html"
                   width="%d"
                   height="%d"
                   scrolling="no"
                   frameBorder="0">
                   </iframe>"""%(self._port, self.objid, self.width, self.height)

    def _do_checks(self):
        if not os.path.exists(os.path.join(self.home_dir,"papaya.js")):
            shutil.copyfile(os.path.join(os.path.split(__file__)[0],"papaya.js"),os.path.join(self.home_dir,"papaya.js"))
        if not os.path.exists(os.path.join(self.home_dir,"papaya.css")):
            shutil.copyfile(os.path.join(os.path.split(__file__)[0],"papaya.css"),os.path.join(self.home_dir,"papaya.css"))
        if not os.path.exists(os.path.abspath("./papaya_data")):
            os.mkdir(os.path.abspath("./papaya_data"))

    def _symlink_files(self, fnames):
        for i,f in enumerate(fnames):
            path, name, ext = split_filename(f)
            link = mktemp(suffix=ext, dir="papaya_data")
            os.symlink(f, link)
            _, name, _ = split_filename(link)
            self.file_names[name + ext] = link

    def _edit_html(self, options, image_options):
        opt_json, imgopt_json = _parse_options(self.file_names, options, image_options)

        html = """
        <!DOCTYPE html>

<html xmlns="http://www.w3.org/1999/xhtml" lang="en">
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
    
        <!-- iOS meta tags -->
        <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no"/>
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    
        <link rel="stylesheet" type="text/css" href="/static/custom/papaya.css?version=0.6.2&build=512" />
        <script type="text/javascript" src="/static/custom/papaya.js?version=0.6.2&build=512"></script>
    
        <title>Papaya Viewer</title>
    
        <script type="text/javascript">
                var params = [];
                params["images"] = {images};
                {options}
                {image_options}
        </script>
</head>

    <body>
        <div id="papayaContainer">
            <div id="papayaToolbar"></div>
            <div id="papayaViewer" class="checkForJS" data-params="params"></div>
            <div id="papayaDisplay"></div>
        </div>
    </body>
</html> 
        """
        html = html.format(images=json(self.file_names.keys()),
                           options=opt_json,
                           image_options=imgopt_json)

        file = NamedTemporaryFile(suffix=".html", dir="papaya_data")
        file.write(html)
        # Do not close because it'll delete the file
        file.flush()
        self._html_file = file
        path, name, ext = split_filename(file.name)
        self.objid = name

        return html
    
    def __init__(self, fnames, port=8888, num=None, options=None, image_options=None,
                 width=600, height=450):
        self._html_file = None
        self.file_names = {}
        if not isinstance(fnames, list):
            fnames = [fnames]
        if isinstance(image_options, dict):
            image_options = [image_options] * len(fnames)
        elif image_options is not None:
            if len(image_options) != len(fnames):
                raise ValueError("If you specify image_options as a list, you "
                                 "specify image_options for each image.")
        self._port = port
        self.width = width
        self.height = height
        self.home_dir = os.path.join(os.path.expanduser("~"),".ipython/profile_default/static/custom/")
        # Check that the papaya_data exists and [temp].html, papaya.js and
        # papaya.css templates are in the right spot. papaya_data is used by
        # _symlink_files
        self._do_checks()

        # symlink our files to a place where the viewer can access it
        # Sets self.file_names for use by _edit_html
        self._symlink_files(fnames)

        #edit viewer.html to point to our files
        self._edit_html(options, image_options)
        open_brains[self.objid] = self

    def __del__(self):
        for name, link in self.file_names.items():
            try:
                os.remove(link)
            except OSError:
                warn("Could not delete %s @ %s" % (name, link))
            if self._html_file is not None:
                self._html_file.close()
                self._html_file = None


def clear_brain():
    """Remove all the files the Brain object made to show you things.
    You must re-run all cells to reload the data"""

    if os.path.exists(os.path.abspath("papaya_data")):
        shutil.rmtree(os.path.abspath("papaya_data"))



