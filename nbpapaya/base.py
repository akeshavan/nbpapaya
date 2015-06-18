import os
import shutil
import weakref
from json import dumps as json
from tempfile import mktemp, NamedTemporaryFile
from warnings import warn
from .brain_view import split_filename, _parse_options, open_brains

class BrainBase(object):

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
        
class Brain2(BrainBase):
        def __init__(self, fnames, port=8888, num=None, options=None, image_options=None,
                     width=600, height=450):
            super(Brain2,self).__init__(fnames, port=8888, num=None, options=None, image_options=None,
                     width=600, height=450)
                     
            #edit viewer.html to point to our files
            self._edit_html(options, image_options)
            open_brains[self.objid] = self
                     
            
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
        
#class Surface(BrainBase):

