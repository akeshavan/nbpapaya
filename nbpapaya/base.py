import os
import shutil
import weakref
from json import dumps as json
from tempfile import mktemp, NamedTemporaryFile
from warnings import warn
from .brain_view import split_filename, _parse_options, open_brains

class ViewerBase(object):

    def _repr_html_(self):
        return """<iframe src="http://localhost:%d/files/papaya_data/%s.html"
                   width="%d"
                   height="%d"
                   scrolling="no"
                   frameBorder="0">
                   </iframe>"""%(self._port, self.objid, self.width, self.height)

    def _do_checks(self):
        print "doing checks", self.home_dir
        if not os.path.exists(os.path.join(self.home_dir,"papaya.js")):
            shutil.copyfile(os.path.join(os.path.split(__file__)[0],"papaya.js"),
            os.path.join(self.home_dir,"papaya.js"))
            
        if not os.path.exists(os.path.join(self.home_dir,"papaya.css")):
            shutil.copyfile(os.path.join(os.path.split(__file__)[0],"papaya.css"),
            os.path.join(self.home_dir,"papaya.css"))
            
        if not os.path.exists(os.path.abspath("./papaya_data")):
            os.mkdir(os.path.abspath("./papaya_data"))
            
        if not os.path.exists(os.path.join(self.home_dir,"three.min.js")):
            shutil.copyfile(os.path.join(os.path.split(__file__)[0],"three.js/build/three.min.js"),
            os.path.join(self.home_dir,"three.min.js"))
            
        if not os.path.exists(os.path.join(self.home_dir,"VTKLoader.js")):
            shutil.copyfile(os.path.join(os.path.split(__file__)[0],
            "three.js/examples/js/loaders/VTKLoader.js"),
            os.path.join(self.home_dir,"VTKLoader.js"))
            
        if not os.path.exists(os.path.join(self.home_dir,"TrackballControls.js")):
            shutil.copyfile(os.path.join(os.path.split(__file__)[0],
            "three.js/examples/js/controls/TrackballControls.js"),
            os.path.join(self.home_dir,"TrackballControls.js"))
            

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
        
    def __del__(self):
        for name, link in self.file_names.items():
            try:
                os.remove(link)
            except OSError:
                warn("Could not delete %s @ %s" % (name, link))
            if self._html_file is not None:
                self._html_file.close()
                self._html_file = None
        
class Brain(ViewerBase):
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
        
class Surface(ViewerBase):
    def __init__(self, fnames, port=8888, num=None, options=None, image_options=None,
                 width=600, height=450):
        super(Surface, self).__init__(fnames, port=8888, num=None, options=None, image_options=None,
                 width=600, height=450)
                 
        self._edit_html(options, image_options)
        open_brains[self.objid] = self
         
    def _edit_html(self,options,image_options):
        
        html = """
        

     
     <html lang="en">
       <head>
         <title>three.js webgl - loaders - vtk loader</title>
 
         <meta charset="utf-8">
         <meta name="viewport" content="width=device-width, user-scalable=no, minimum-scale=1.0, maximum-scale=1.0">
 
         <style>
     		html, body {{
     		  background-color:#000;
     		  margin: 0;
     		  padding: 0;
     		  overflow: hidden !important;  
     		}}
	
     	</style>   
         
         <body ng-app="visApp">

             <script src="/static/custom/three.min.js"></script>
             <script src="/static/custom/VTKLoader.js"></script>
             <script src="/static/custom/TrackballControls.js"></script>

             <script>
             //if ( ! Detector.webgl ) Detector.addGetWebGLMessage();

                 var stats;

                 var camera, controls, scene, renderer;

                 var cross;

                 var objects = [];

                 var meshes = [];
				
				container = document.createElement( 'div' );
				document.body.appendChild( container );
				
				
   			  	function init(){{
     	        console.log(window.innerWidth,window.innerHeight);
     	        camera = new THREE.PerspectiveCamera( 60, window.innerWidth / window.innerHeight, 0.01, 1e10 );
     	        camera.position.z = 120;

     	        controls = new THREE.TrackballControls( camera );

     	        controls.rotateSpeed = 5.0;
     	        controls.zoomSpeed = 5;
     	        controls.panSpeed = 2;

     	        controls.noZoom = false;
     	        controls.noPan = false;

     	        controls.staticMoving = true;
     	        controls.dynamicDampingFactor = 0.3;

     	        scene = new THREE.Scene();

     	        scene.add( camera );

     	        // light

     	        var dirLight = new THREE.DirectionalLight( 0xffffff );
     	        dirLight.position.set( 200, 200, 1000 ).normalize();

     	        camera.add( dirLight );
     	        camera.add( dirLight.target );

     	        var material = new THREE.MeshLambertMaterial( {{ color:0xffffff, side: THREE.DoubleSide }} );

     	        var loader = new THREE.VTKLoader();
                 
                 var loadMesh = function(name) {{
                 					var oReq = new XMLHttpRequest();
                 					oReq.open("GET", name, true);
                 					oReq.onload = function(oEvent) {{
                 						var buffergeometry=new THREE.VTKLoader().parse(this.response);
					
                 						geometry=new THREE.Geometry().fromBufferGeometry(buffergeometry);
                 						geometry.computeFaceNormals();
                 						geometry.computeVertexNormals();
                 						geometry.__dirtyColors = true;
							
                 						material=new THREE.MeshLambertMaterial()//{{vertexColors: THREE.FaceColors}});
                 						var color = [Math.random(), Math.random(), Math.random()]
						    			console.log("hello")
                 						/*for (i=0;i<geometry.faces.length;i++){{
                 							var face = geometry.faces[i];
                 							face.color.setHex( Math.random() * 0xffffff );
                 							//face.color.setRGB(color[0],color[1],color[2]);
						
                 							//face.materials = [ new THREE.MeshBasicMaterial( {{ color: Math.random() * 0xffffff }} ) ];
                 						}}
                 						geometry.colorsNeedUpdate = true*/
                 						mesh=new THREE.Mesh(geometry,material);
                 						mesh.dynamic=true
                 						//mesh.name = name
										
                 				        mesh.rotation.y = Math.PI * 1.1;
 		                                mesh.rotation.x = Math.PI * 0.5;
 		                                mesh.rotation.z = Math.PI * 1.5;
	
                 						console.log(mesh)
                 						scene.add(mesh);
                 						meshes.push(mesh)
					
                 					}}
                 					oReq.send();
                 				}}
                 
                 console.log("loading meshes")
                 files_to_load = {images}
                 for (i=0;i<files_to_load.length;i++){{
                     loadMesh(files_to_load[i])	
					console.log("loaded mesh",i)
                 }}
     					
        
     	        // renderer

     			renderer = new THREE.WebGLRenderer();
     			 
     	        renderer.setPixelRatio( window.devicePixelRatio );
     	        renderer.setSize( window.innerWidth, window.innerHeight);
				container.appendChild( renderer.domElement );
			    }}
     	        //window.addEventListener( 'resize', onWindowResize, false );
          
             	var animate = function() {{

             	        requestAnimationFrame( animate );

             	        controls.update();
             	        renderer.render( scene, camera );
						//console.log("rendered")
	
             	      }}
                       
				init();

                 animate();
             
             //}}
             </script>

           </body>
         </html>

     
  
        """
        
        html = html.format(images=json(self.file_names.keys()))
        file = NamedTemporaryFile(suffix=".html", dir="papaya_data")
        file.write(html)
        # Do not close because it'll delete the file
        file.flush()
        self._html_file = file
        path, name, ext = split_filename(file.name)
        self.objid = name

        return html

