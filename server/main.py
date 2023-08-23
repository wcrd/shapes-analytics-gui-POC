from flask import Flask, request, jsonify
import rdflib

from helpers import msg, MsgType, data

# Going to run simple server from a class so I can store state in memory across requests
class Server():

    def __init__(self):
        self.app = Flask(__name__, static_url_path="/static")
        
        print("Loading graph frame with Brick and Switch ontologies.")
        (self.ds, self.g_ns) = self.init_graph_model() 


        # Define routes (need to do it here as don't have access to @app decorator. Could use flask_classful instead)
        self.app.route("/hello-world", methods=['GET'])(self.hello_world)
        self.app.route("/graph-size", methods=['GET'])(self.graph_size)
        self.app.route("/upload-model", methods=['POST'])(self.upload_model)
    
    #   FLASK STUFF
    #

    def start(self, address="localhost:8080", debug=False):
        assert len(address.split(":")) == 2
        host, port = address.split(":")
        self.app.run(host=host, port=port, debug=debug)
    
    # ROUTES AND METHODS
    #

    def hello_world(self):
        return data("Hello, world!")
    
    def upload_model(self):
        if request.method == 'POST':

            # check if the post request has the model
            if 'model' not in request.files:
                return msg(MsgType.ERROR, "No model data provided")
            
            file = request.files['model']
            # If the user does not select a file, the browser submits an
            # empty file without a filename.
            if file.filename == '':
                return msg(MsgType.ERROR, "No file provided")
            if file:
                # try and process as a model
                try:
                    res = self.parse_model_file(file)
                    # return { "msg_type": "success", "msg": "File successfully loaded into graph", "meta": { "filename": file.filename, "triples": len(self.ds.graph(self.g_ns['building'])) }}
                    return msg(MsgType.SUCCESS, "File successfully loaded into graph", filename=file.filename, triples=len(self.ds.graph(self.g_ns['building'])) )

                
                except Exception as e:
                    return msg(MsgType.ERROR, "Failed to parse model", error=str(e))

    def graph_size(self):
        return data(len(self.ds))
    

    #   NON ROUTE METHODS
    #

    def init_graph_model(self):
        brick_path = "./server/static/brick.ttl"
        switch_path = "./server/static/Brick-SwitchExtension.ttl"
        rnd_path = "./server/static/rnd.ttl"

        ds = rdflib.Dataset(default_union=True)
        g_ns = rdflib.Namespace("https://_graph_.com#")

        # Load brick
        ds.add_graph(g_ns['brick']).parse(brick_path, format="turtle")
        # # load RND ontology (this is what contains the relationships we will use to define enrichment)
        ds.add_graph(g_ns['rnd']).parse(rnd_path, format='turtle')
        # load Switch Extension
        ds.add_graph(g_ns['switch']).parse(switch_path, format='turtle')

        return (ds, g_ns)

    def parse_model_file(self, modelfile):
        # load building model
        self.ds.add_graph(self.g_ns['building']).parse(file=modelfile, format="turtle")





# Run this bad boy
app = Server()

if __name__=="__main__":
    app.start(debug=True)