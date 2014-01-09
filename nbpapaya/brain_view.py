import os
import shutil
from nipype.utils.filemanip import split_filename

class Brain(object):

    def _repr_html_(self):
        return """<iframe src="http://localhost:%d/files/papaya_data/viewer_%02d.html"
                   width="600" 
                   height="450" 
                   scrolling="no" 
                   frameBorder="0">
                   </iframe>"""%(self._port,self._num)
    
    def _do_checks(self):
        if not os.path.exists(os.path.join(self.home_dir,"papaya.js")):
            shutil.copyfile(os.path.join(os.path.split(__file__)[0],"papaya.js"),os.path.join(self.home_dir,"papaya.js"))
        if not os.path.exists(os.path.join(self.home_dir,"papaya.css")):
            shutil.copyfile(os.path.join(os.path.split(__file__)[0],"papaya.css"),os.path.join(self.home_dir,"papaya.css"))
        if not os.path.exists(os.path.abspath("./papaya_data")):
            os.mkdir(os.path.abspath("./papaya_data"))
        
    
    def _symlink_files(self,fnames):
        for i,f in enumerate(fnames):
            path, name, ext = split_filename(f)
            newname = '%s_%02d_%02d%s'%(name,self._num,i,ext)
            try:
                os.readlink(os.path.join('papaya_data',newname))
                os.remove(os.path.join('papaya_data',newname))
            except OSError:
                pass
            
            os.symlink(f,os.path.join('papaya_data',newname))
            self.file_names.append(newname)
            
            
    def _edit_html(self):
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
                params["images"] = %s;
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
        """%str(self.file_names)
        
        foo = open("papaya_data/viewer_%02d.html"%self._num,'w')
        foo.write(html)
        foo.close()
        
        return html
    
    def __init__(self,fnames,port=8888,num=0):
        self._num = num
        if not isinstance(fnames,list):
            fnames = [fnames]
        self._port = port
        self.home_dir = os.path.join(os.path.expanduser("~"),".ipython/profile_default/static/custom/")
        self.file_names = []
        #Check that the viewer.html, papaya.js and papaya.css templates are in the right spot
        self._do_checks()
        
        #symlink our files to a place where the viewer can access it
        self._symlink_files(fnames)
        
        #edit viewer.html to point to our files
        self._edit_html()
        
def clear_brain():
    """Remove all the files the Brain object made to show you things.
    You must re-run all cells to reload the data"""

    if os.path.exists(os.path.abspath("papaya_data")):
        shutil.rmtree(os.path.abspath("papaya_data"))



