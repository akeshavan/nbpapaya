import os
import shutil
import weakref
from json import dumps as json
from tempfile import mktemp, NamedTemporaryFile
from warnings import warn
from .brain_view import split_filename, _parse_options, open_brains

class ViewerBase(object):

    def _repr_html_(self):
        return """<iframe src="http://%s:%d/files/papaya_data/%s.html"
                   width="%d"
                   height="%d"
                   scrolling="no"
                   frameBorder="0">
                   </iframe>"""%(self._host, self._port, self.objid, self.width, self.height)

    def _do_checks(self):
        print "doing checks", self.home_dir
        if not os.path.exists(self.home_dir):
            os.makedirs(self.home_dir)
        if not os.path.exists(os.path.join(self.home_dir,"papaya.js")):
            shutil.copyfile(os.path.join(os.path.split(__file__)[0],"Papaya/release/current/standard/papaya.js"),
            os.path.join(self.home_dir,"papaya.js"))
            
        if not os.path.exists(os.path.join(self.home_dir,"papaya.css")):
            shutil.copyfile(os.path.join(os.path.split(__file__)[0],"Papaya/release/current/standard/papaya.css"),
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
        tmp_files = {}
        mapper = {}
        for i,f in enumerate(fnames):
            path, name, ext = split_filename(f)
            link = mktemp(suffix=ext, dir="papaya_data")
            os.symlink(f, link)
            _, name, _ = split_filename(link)
            #self.file_names[name + ext] = link
            tmp_files[name+ext] = link
            mapper[f] = link
        #print tmp_files
        return tmp_files, mapper    
            
    def __init__(self, fnames, port=8888, num=None, options=None, image_options=None,
                 width=600, height=450, host="localhost"):
        self._html_file = None
        self.file_names = {}
        if not isinstance(fnames, list):
            fnames = [fnames]

        self._port = port
        self._host = host
        self.width = width
        self.height = height
        self.home_dir = os.path.join(os.path.expanduser("~"),".jupyter/custom/")
        # Check that the papaya_data exists and [temp].html, papaya.js and
        # papaya.css templates are in the right spot. papaya_data is used by
        # _symlink_files
        self._do_checks()

        # symlink our files to a place where the viewer can access it
        # Sets self.file_names for use by _edit_html
        self.file_names, self._mapper = self._symlink_files(fnames)
        
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
                     width=600, height=450, host="localhost"):
            super(Brain,self).__init__(fnames, port, num, options, image_options,
                     width=600, height=450, host=host)
                     
            #edit viewer.html to point to our files
            
            if isinstance(image_options, dict):
                image_options = [image_options] * len(fnames)
            elif image_options is not None:
                if len(image_options) != len(fnames):
                    raise ValueError("If you specify image_options as a list, you "
                                 "specify image_options for each image.")
            
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
            <script src="https://code.jquery.com/jquery-2.2.2.min.js" integrity="sha256-36cp2Co+/62rEAAYHLmRCPIych47CvdM+uTBJwSzWjI=" crossorigin="anonymous"></script>
            <link rel="stylesheet" type="text/css" href="/custom/papaya.css?version=0.6.2&build=51212345" />
            <script type="text/javascript" src="/custom/papaya.js?version=0.6.2&build=51212345"></script>
    
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
                 width=600, height=450, host="localhost"):
        super(Surface, self).__init__(fnames, port, num, options, image_options,
                 width, height, host)
                 
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

             <script src="/custom/three.min.js"></script>
             <script src="/custom/VTKLoader.js"></script>
             <script src="/custom/TrackballControls.js"></script>

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

class Overlay(ViewerBase):
    def __init__(self, image_options, port=8888, num=None, options=None, 
                        width=600, height=450, host="localhost"):
                            
        fnames = image_options.keys()
                           
        super(Overlay, self).__init__(fnames, port, num, options, image_options,
                 width, height, host)
        
        new_mapper = {}
        for key, value in self._mapper.iteritems():
            newkey = "http://{}:{}/files/{}".format(self._host,self._port,value)
            new_mapper[newkey] = image_options[key]
            new_mapper[newkey]["filename"] = "http://{}:{}/files/{}".format(self._host, 
                                                                            self._port, 
                                                                            self._symlink_files([image_options[key]["filename"]])[1].values()[0])
        
        self._javascript_object = new_mapper    
        
        #print image_options, new_mapper
        
                 
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
     		html, body {
     		  background-color:#000;
     		  margin: 0;
     		  padding: 0;
     		  overflow: hidden !important;  
     		}
     		
     		div{
         		width: 100%;
     		}
	
     	</style>   
         
         <body ng-app="visApp">

            

             <script src="/custom/three.min.js"></script>
             <script src="/custom/VTKLoader.js"></script>
             <script src="/custom/TrackballControls.js"></script>
             <script src="https://cdnjs.cloudflare.com/ajax/libs/d3/3.5.17/d3.js"></script>
             <script src="https://rawgit.com/dataarts/dat.gui/master/build/dat.gui.min.js"></script>

<script>
             //if ( ! Detector.webgl ) Detector.addGetWebGLMessage();

                 var stats;

                 var camera, controls, scene, renderer;

                 var cross;

                 var objects = [];

                 meshes = [];
                 gui = new dat.GUI()
                 var screenshot = { "Capture Image":function(){ window.open(renderer.domElement.toDataURL("image/png", "final")) }};

                 gui.add(screenshot,'Capture Image');
                 
				
				container = document.createElement( 'div' );
				document.body.appendChild( container );
				
				var MeshOpts = IPYTHON_NOTEBOOK_DICTIONARY;
                
                var initialize_gui = function(mesh){
                    //var gui = new dat.GUI();
                    var meshgui = gui.addFolder(mesh.name);
                    var tmp = mesh.anisha_opts
                    var colormin = gui.addColor(tmp, 'colormin');
                    var colormax = gui.addColor(tmp, 'colormax');
                    var vmin = gui.add(tmp, 'vmin');
                    var vmax = gui.add(tmp, 'vmax');
                    var threshold = gui.add(tmp, 'threshold', 0, 5);
                    var key = gui.add(tmp, "key", tmp.key_options)
                    var mesh_transparency = gui.add(tmp, "mesh_transparency", 0, 1)
                    var mesh_visible = gui.add(tmp, "mesh_visible")
                    
                    var changer = function(value){
                        // console.log("this is", this)
                        // console.log("mesh is", mesh)
                        
                        mesh.anisha_opts = this.object   
                        // console.log(mesh.anisha_opts)
                        color_brain(mesh)
                    }
                    
                    colormin.onChange(changer)
                    colormax.onChange(changer)
                    vmin.onChange(changer)
                    vmax.onChange(changer)
                    key.onChange(changer)
                    threshold.onChange(changer)
                    mesh_transparency.onChange(changer)
                    mesh_visible.onChange(changer)
                    gui.open();

                    
                
                }
				

                // Use CSV is a function that will remember csvs by filenames.  This will only
                // go and get the file if the data for that particular filename has not yet been loaded.
                var useCSV = (function(){
                    var collectionOfCSVs = {};
                    // Cache CSVs by their filename as they are loaded and call the callback function on
                    // the csv data if/once loaded.

                    return function(filename, callback){

                        // if the csv data by this filename already exists...
                        if (collectionOfCSVs[filename]){

                            // use it
                            callback(collectionOfCSVs[filename]);

                        } else {
                            d3.csv(filename, function(csv){
                                // remember the data for this new csv
                                collectionOfCSVs[filename] = csv;

                                // use the csv data
                                callback(csv)
                            })
                        }
                    }

                })();


                // use mesh data and csv data to calculate and cache face_metrics for all possible
                // keys on the faceMetrics argument.
                var calculateFaceMetrics = function(mesh, callback){
                    var mesh_options = mesh.anisha_opts
                    var csv_filename = mesh_options["filename"]
                    var keys = mesh_options.key_options;

                    if(!mesh.face_metrics){
                        mesh.face_metrics = {}
                    }

                    useCSV(csv_filename, function(csv){
                        keys.forEach(function(key, index){
                            if(mesh.face_metrics[key]){
                                return;
                            }

                            mesh.face_metrics[key] = mesh.geometry.faces.map(function(element, index){
                                var vals = parseFloat(csv[element["a"]][key]) + parseFloat(csv[element["b"]][key]) + parseFloat(csv[element["c"]][key])
                                //vals is the average value of the "key"(travel depth, geodesic depth, etc) for the 3 vertices of the face
                                // anisha: I have no idea if this is the right thing to do
                                return vals/3;
                            });

                        });

                        if(typeof callback === 'function'){
                            callback(mesh);
                        }
                    });
                }


                // Color brain depends on face_metrics being calculated once on initialization.
                // This means that on change from the gui, color brain will only be going over each
                // of the faces in the geometry and looking up what color it should set that face to.
                // 
                // Before, the csv was being reloaded each time and the face_metrics was recalculated each time.
				var color_brain = function(mesh){
                    var mesh_options = mesh.anisha_opts
                    var key = mesh_options.key
                    var face_metrics = mesh.face_metrics[key]

                    mesh.material.transparent = true
                    mesh.material.opacity = mesh_options.mesh_transparency
                    mesh.visible = mesh_options.mesh_visible

                    var colorgrad = d3.scale.linear()
                        .domain([mesh_options.vmin, mesh_options.vmax])//[_.min(face_metrics), _.max(face_metrics)])
                        .range([mesh_options.colormin, mesh_options.colormax]);

                    mesh.geometry.faces.forEach(function(element, index){

                        if (face_metrics[index] > mesh_options.threshold){
                            var col = new THREE.Color(colorgrad(face_metrics[index]))
                            element.color.setRGB(col.r, col.g, col.b)
                        } else {
                            // Undo the color setting by setting it back to white.
                            element.color.setRGB(1, 1, 1)
                        }

                    })
                    mesh.geometry.colorsNeedUpdate = true
                }

   			  	function init(){
     	        console.log(window.innerWidth,window.innerHeight);
     	        camera = new THREE.PerspectiveCamera( 60, window.innerWidth / window.innerHeight, 0.01, 1e10 );
     	        camera.position.z = 120;

     	        controls = new THREE.TrackballControls( camera, container );

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

     	        var material = new THREE.MeshLambertMaterial( { color:0xffffff, side: THREE.DoubleSide } );

     	        var loader = new THREE.VTKLoader();
                 
                var loadMesh = function(name) {
                 					var oReq = new XMLHttpRequest();
                 					oReq.open("GET", name, true);
                 					oReq.onload = function(oEvent) {
                 						var buffergeometry=new THREE.VTKLoader().parse(this.response);
					
                 						geometry=new THREE.Geometry().fromBufferGeometry(buffergeometry);
                 						geometry.computeFaceNormals();
                 						geometry.computeVertexNormals();
                 						geometry.__dirtyColors = true;
							
                 						material=new THREE.MeshLambertMaterial({vertexColors: THREE.FaceColors});
                 						// var color = [Math.random(), Math.random(), Math.random()]
						    			//console.log("hello")
                 						/*for (i=0;i<geometry.faces.length;i++){
                 							var face = geometry.faces[i];
                 							face.color.setHex( Math.random() * 0xffffff );
                 							//face.color.setRGB(color[0],color[1],color[2]);
						
                 							//face.materials = [ new THREE.MeshBasicMaterial( { color: Math.random() * 0xffffff } ) ];
                 						}
                 						geometry.colorsNeedUpdate = true*/
                 						mesh=new THREE.Mesh(geometry,material);
                 						mesh.dynamic=true
                 						mesh.name = name
                 						//mesh.name = name
										
                 				        mesh.rotation.y = Math.PI * 1.1;
 		                                mesh.rotation.x = Math.PI * 0.5;
 		                                mesh.rotation.z = Math.PI * 1.5;
 		                                mesh.anisha_opts = MeshOpts[mesh.name]
	
                                        // calculate face_metrics once, and after calculations for all
                                        // keys are done, color brain.
                                        calculateFaceMetrics(mesh, color_brain)
                                        initialize_gui(mesh)
                                        
                 						
                 						scene.add(mesh);
                 						meshes.push(mesh)
					
                 					}
                 					oReq.send();
                 			}
                 				
                 
                console.log("loading meshes")
                files_to_load = Object.keys(MeshOpts)
                
                 for (i=0;i<files_to_load.length;i++){
                    loadMesh(files_to_load[i])	
					console.log("loaded mesh",i)
					                 }

        
     	        // renderer

     			renderer = new THREE.WebGLRenderer({preserveDrawingBuffer: true});
     			 
     	        renderer.setPixelRatio( window.devicePixelRatio );
     	        renderer.setSize( window.innerWidth, window.innerHeight);
				container.appendChild( renderer.domElement );
				}
				
			    
     	        //window.addEventListener( 'resize', onWindowResize, false );
          
             	var animate = function() {

             	        requestAnimationFrame( animate );

             	        controls.update();
             	        renderer.render( scene, camera );
						//console.log("rendered")
	
             	      }
                       
				init();

                 
                console.log("finished init")
                 
                
                //var meshgui = gui.addFolder('Mesh');
                

                
                
                
                
             animate();
             
             </script>


           </body>
         </html>

     
  
                """
        
        html = html.replace("IPYTHON_NOTEBOOK_DICTIONARY", json(self._javascript_object))
        file = NamedTemporaryFile(suffix=".html", dir="papaya_data")
        file.write(html)
        # Do not close because it'll delete the file
        file.flush()
        self._html_file = file
        path, name, ext = split_filename(file.name)
        self.objid = name

        return html

