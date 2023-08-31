from flask import Flask, request, jsonify
from flask_cors import CORS
import rdflib
import json

from helpers import msg, MsgType, data, MatchJSONEncoder
import lib.modules as LogicModules
from lib.diagram_generator import generate_tidy_tree

# Going to run simple server from a class so I can store state in memory across requests
class Server():

    def __init__(self):
        self.app = Flask(__name__, static_url_path="/static")
        CORS(self.app)
        self.db = {
            'modules': { str(getattr(LogicModules, m).MODULE.uuid): getattr(LogicModules, m).MODULE for m in LogicModules.__all__ },
            'matches': {},
            'diagrams': {}, # { module_uuid: { logic_uuid: { match_uuid: diagram_data } } } 
        }
        
        
        print("Loading graph frame with Brick and Switch ontologies.")
        (self.ds, self.g_ns) = self.init_graph_model() 


        # Define routes (need to do it here as don't have access to @app decorator. Could use flask_classful instead)
        self.app.route("/hello-world", methods=['GET'])(self.hello_world)
        self.app.route("/graph-size", methods=['GET'])(self.graph_size)
        self.app.route("/upload-model", methods=['POST'])(self.upload_model)
        self.app.route("/get-modules", methods=['GET'])(self.get_modules)
        self.app.route("/get-module-matches", methods=['POST'])(self.get_module_matches)
        self.app.route("/get-match-diagram", methods=['POST'])(self.get_match_diagram)
    
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
    
    def get_modules(self):
        return_data = []
        for mod in self.db['modules'].values():
            return_data.append({
                'uuid': mod.uuid,
                'name': mod.name,
                'type': mod.cType.name,
                'options': [{'type': opt.cType.name, 'uuid': opt.uuid, 'name': opt.name, 'desc': opt.description} for opt in mod.logic_modules]
            })
        
        return data(return_data)
    
    def get_module_matches(self):

        # Get required values from request body
        jsonData = request.get_json()
        module_uuid = jsonData.get('module_uuid')
        force_rematch = jsonData.get('force_rematch')

        if not module_uuid: return msg(MsgType.ERROR, "No module_id provided")

        # Run the matching process
        # Check module exists
        if not (m:=self.db['modules'].get(module_uuid)):
            return msg(MsgType.ERROR, "No module exists for that uuid", uuid=module_uuid)

        if not force_rematch:
            # check if we already have matches!
            matches = self.db['matches'].get(module_uuid)
            if matches: 
                return data( matches, meta={"from_cache": True})
        
        (raw_match, df_match) = m.match(self.ds)

        # let sort the df by target
        df_match.sort_values(by="?target", inplace=True)

        self.db['matches'][module_uuid] = json.loads(json.dumps(df_match.to_dict(orient='records'), cls=MatchJSONEncoder))


        return data( self.db['matches'][module_uuid] , meta={"from_cache": False} )

    def get_match_diagram(self):
        # Get required values from request body
        jsonData = request.get_json()
        match = jsonData['match']
        force_regen = jsonData.get('force_regen')

        # Get logic module and run the diagram method
        # Check module exists
        if not (m:=self.db['modules'].get(match['_module'])):
            return msg(MsgType.ERROR, "No module exists for that uuid", uuid=match['_module'])
        
        if not force_regen:
            # check if we already have diagram!
            matches = self.db['diagrams'].get(match['_module'], {}).get(match['_logic'], {}).get(match['_match_id'])
            if matches: 
                return data( matches, meta={"from_cache": True})
        
        # get diagram graph
        diagram_g = m.get_match_diagram_graph(self.ds, match)

        # generate match diagram data
        diagram_data = generate_tidy_tree(diagram_g.graph, match)

        # save to db
        self.db['diagrams'].setdefault(match['_module'], {}).setdefault(match['_logic'], {})[match['_match_id']] = diagram_data

        return data( diagram_data )

    #   NON ROUTE METHODS
    #

    def init_graph_model(self):
        brick_path = "./server/static/brick.ttl"
        switch_path = "./server/static/Brick-SwitchExtension.ttl"
        rnd_path = "./server/static/rnd.ttl"

        ds = rdflib.Dataset(default_union=True, store="Oxigraph")
        g_ns = rdflib.Namespace("https://_graph_.com#")

        # Load brick
        ds.add_graph(g_ns['brick']).parse(brick_path, format="turtle")
        # # load RND ontology (this is what contains the relationships we will use to define enrichment)
        ds.add_graph(g_ns['rnd']).parse(rnd_path, format='turtle')
        # load Switch Extension
        ds.add_graph(g_ns['switch']).parse(switch_path, format='turtle')

        return (ds, g_ns)

    def parse_model_file(self, modelfile):
        # dump old model
        self.ds.remove_graph(self.g_ns['building'])
        # load building model
        self.ds.add_graph(self.g_ns['building']).parse(file=modelfile, format="turtle")





# Run this bad boy
app = Server()

if __name__=="__main__":
    app.start(debug=True)