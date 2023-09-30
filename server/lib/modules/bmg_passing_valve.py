import rdflib
import pandas as pd
from typing import Tuple, Dict, Callable
import uuid

from ..logic_master import classEnum
from ..helpers import flatten

# OPTIONS
class BMG_Passing_Valve_MATvsDAT(object):
    cType = classEnum.LOGIC_OPTION
    uuid = uuid.UUID("b04aaee1-4338-4a36-b389-12a68287f2d4")
    name = "BMG_Passing_Valve_MATvsDAT"

    description = """
        Passing Valve detection via comparison of Mixed Air Temperature vs. Discharge Air Temperature in parent entities
        """

    sparql_query = """
        WHERE {
            # General entity selection
            ?base brick:hasPart ?valve . # NOTE:rather than look at all subparts*, just get the direct part and pull the root parent.
            {
                ?valve rdf:type ?valve_class .
                ?valve_class rdfs:subClassOf* brick:Hot_Water_Valve .
                BIND("HHW" as ?valve_class_simple)
            }
            UNION {
                ?valve rdf:type ?valve_class .
                ?valve_class rdfs:subClassOf* brick:Chilled_Water_Valve .
                BIND("CHW" as ?valve_class_simple)
            }

            ?base rnd:hasRootParent ?target . # All components above are partOf* the target (rootParent)
            ?target rdf:type/rdfs:subClassOf* brick:Equipment .
            
            # point query
            ?valve brick:hasPoint ?v_pos .
            ?v_pos rdf:type ?v_pos_type .
            VALUES ?v_pos_type { brick:Position_Sensor brick:Position_Command }

            ?target brick:hasPoint ?m_b1 .
            ?m_b1 rdf:type brick:Discharge_Air_Temperature_Sensor .
            ?target brick:hasPoint ?m_b2 .
            ?m_b2 rdf:type brick:Mixed_Air_Temperature_Sensor .
        }
        """

    _sparql_return = {
        # This module does post-processing of match results to get into the right form;
        "SELECT": f"""
            SELECT ("{name}" as ?option) ?target ?m_b1 ?m_b2 ?valve ?valve_class ?v_pos ?valve_class_simple (strUUID() as ?row_id)            
            """,
        "CONSTRUCT": None
    }

    diagram_query = """
        CONSTRUCT {
            ?target rdf:type ?t_type ;
                rdfs:label ?t_label ;
                brick:hasPoint ?m_b1, ?m_b2 .
            
                ?m_b1 rdf:type brick:Discharge_Air_Temperature_Sensor .
                ?m_b2 rdf:type brick:Mixed_Air_Temperature_Sensor .
            
            ?part_1 rdf:type ?part_1_type ;
                brick:hasPart ?part_2 ;
                rdfs:label ?part_1_label .
            
            ?part_2 rdf:type ?part_2_type ;
                rdfs:label ?part_2_label .
            
            # valve definition is covered off by part_2, just need to add additional data
            ?valve brick:hasPoint ?v_pos .
            ?v_pos rdf:type ?v_pos_type .
            
        } WHERE {
            ?target brick:hasPoint ?m_b1 .
            ?m_b1 rdf:type brick:Discharge_Air_Temperature_Sensor .
            ?target brick:hasPoint ?m_b2 .
            ?m_b2 rdf:type brick:Mixed_Air_Temperature_Sensor .
            
            # PATH RESOLOVER
            ?target brick:hasPart* ?part_1 .
            ?part_1 brick:hasPart ?part_2 .
            ?part_2 brick:hasPart* ?valve .

            # PATH TERMINATION CONDITIONS
            ?valve rdf:type ?valve_class .
            ?valve_class rdfs:subClassOf* ?valve_allowed_classes .
            VALUES ?valve_allowed_classes { brick:Hot_Water_Valve brick:Chilled_Water_Valve } .
            ?valve brick:hasPoint ?v_pos .
            ?v_pos rdf:type ?v_pos_type .
            VALUES ?v_pos_type { brick:Position_Sensor brick:Position_Command }
            
            # METADATA
            ?target rdf:type ?t_type .
            OPTIONAL { ?target rdfs:label ?t_label } .
            ?part_1 rdf:type ?part_1_type .
            OPTIONAL { ?part_1 rdfs:label ?part_1_label } .
            ?part_2 rdf:type ?part_2_type .
            OPTIONAL { ?part_2 rdfs:label ?part_2_label } .
            # OPTIONAL { ?valve rdfs:label ?valve_label } .
        }
    """

    params = """
        m_b1: Discharge Air Temperature (DAT)
        m_b2: Mixed Air Temperature (MAT)
        m_b3{}: {[valve_type]: [ valve_valve_positions[] ]} ; For each valve type (CHW, HHW), a list of valve position points for each valve found.
        -
        valve_open_threshold = 5 %
        air_temp_diff_threshold = 0.5 degC
        optional = Include optional sensors, if available
    """

    @classmethod
    def find_matches(self, dataset:rdflib.Graph, return_type="SELECT") -> Tuple[rdflib.query.Result, pd.DataFrame]:
        # Initial SPARQL Query
        _query = self._sparql_return[return_type] + self.sparql_query
        res = dataset.query(_query)
        res_df = pd.DataFrame(res, columns=[v.toPython() for v in res.vars])

        # Process Results
        # 1. collapse valve pos into list[] per valve (by all other fields) -> L[v_pos]
        # 2. TODO: Redo this - group instead of pivot. Makes it cleaner
        #    Pivot valve by valve_class
        # 3. grouped by target with values list[m_b1], list[m_b2], list[valves], list[ L[v_pos] ]
        #
        # This give us a format for the values of -> ?valve: valve_type[ valves[] ], ?valve_class_simple: valve_type[], ?v_pos: valve_type[ valves[ valve_pos_points{} ] ]
        # in english: ?valve: list of valves for each valve simple type in same order as ?valve_class_simple. ?valve_class_simple: list of simple valve class names. ?v_pos: list of valve position points per valve, per valve type ?v_pos[valve_class_type][valve][valve_pos_point]

        res_grp = res_df.astype(str).groupby(by=['?row_id', '?option', '?target', '?m_b1', '?m_b2', '?valve', '?valve_class_simple'], group_keys=True)['?v_pos'].apply(set).reset_index()
        # process simple class to string
        res_grp['?valve_class_simple'] = res_grp['?valve_class_simple'].apply(lambda x: x.toPython())
        # group into row per valve type, per target
        res_vlv_pvt = res_grp.groupby(by=['?option', '?target', '?m_b1', '?m_b2', '?valve_class_simple'], group_keys=True).agg({'?valve':list, '?v_pos':list}).reset_index()

        # we take the set for target points m_b1 and m_b2 as these are repeated in many rows for each terminal unit match. We only need the unique points.
        # the terminal units are lists as these have already been grouped so are unique, and we want to preserve list order.
        final_res = res_vlv_pvt.groupby(by=['?option', '?target'], as_index=False).agg({'?m_b1': set, '?m_b2': set, '?valve': list, '?valve_class_simple': list, '?v_pos': list}).reset_index()
        
        return (res, final_res)
    
    @classmethod
    def prepare_match(self, match:pd.DataFrame, modelQueryFunc:Callable=None, modelQueryFuncArgs:dict={}) -> Tuple[Dict, Dict]:
        """
        modelQueryFunc: function(entities:list, **args) -> dict{ entity_subject:str, remote_telemetery_id_for_entity:str }
        RETURNS: Tuple( List of sensor entities, dict of module slots for logic usage )

        Notes:
        - Given multiple sensors options per named slot, the first entity will be chosen by default. Will update this function in future to provide more choice.
        """
        # Get just sensors needed for logic to run (remove alternates)
        # No method for user choice here yet, just going to take index 0 option.
        sensors_in_use = {
            'm_b1': list(match['?m_b1'])[0].toPython(),
            'm_b2': list(match['?m_b2'])[0].toPython(),
            'm_b3': {v_type: [list(v_pos)[0].toPython() for v_pos in match['?v_pos'][idx]] for idx, v_type in enumerate(match['?valve_class_simple'])}
        }

        # TODO: The below needs to be updated to handle the nested dict for m_b3
        # # Reduce to simple list of sensors
        # sensors = set()
        # for v in sensors_in_use.values():
        #     sensors.update(flatten(v))  # TODO: Need to update to flatten dict
        
        # module_sensors={}
        # # If the model query function has been provided, use it to get entity ids for telemetry
        # if modelQueryFunc:
        #     sensor_id_map = modelQueryFunc(**{"entities": list(sensors), **modelQueryFuncArgs})

        #     module_sensors = {
        #         'm_b1': sensor_id_map[ sensors_in_use['m_b1'] ],
        #         'm_b2': sensor_id_map[ sensors_in_use['m_b2'] ],
        #         'm_b3': {k: sensor_id_map[ s ] for s in sensors_in_use['m_b3'] }
        #     }
        # else:
        #     print("Model query function not provided; unable to fetch external store telemetry ids for provided entities.")
        
        # return ( sensor_id_map, module_sensors)
        pass

    @classmethod
    def run_module(self, data:pd.DataFrame, sensors:dict, options:dict={}):
        print("Method not defined")
        pass
    


# MODULE
class MODULE_BMG_Passing_Valve(object):
    cType = classEnum.MODULE
    uuid = uuid.UUID("c6a3e65d-816f-475d-a0a0-9191d3ab556a")
    name = "MODULE_BMG_Passing_Valve"

    # Ranked tuple of logic options for this module
    logic_modules = (
        BMG_Passing_Valve_MATvsDAT,
    )

    @classmethod
    def match(self, dataset:rdflib.Graph, return_type="SELECT") -> Tuple[ Dict[str, rdflib.query.Result], pd.DataFrame ]:
        df_output = pd.DataFrame()
        res_output = {}

        for rank, logic_option in enumerate(self.logic_modules):
            # get matches
            res_option, df_option = logic_option.find_matches(dataset, return_type)
            if(return_type=="SELECT"):
            # add rank index, link to class
                df_option['_rank'] = rank
                df_option['_module'] = self.uuid or None
                df_option['_logic'] = logic_option.uuid
                df_option['_logic_name'] = logic_option.__name__
                df_option['_match_id'] = [uuid.uuid4() for _ in range(len(df_option.index))]

            if(return_type=="CONSTRUCT"):
                # add the module relationship and entity
                res_option.graph.add((rdflib.URIRef(f"http://switch.com/rnd#{self.name}"), rdflib.RDF.type, rdflib.URIRef("http://switch.com/rnd#logicModule")))
                res_option.graph.add((rdflib.URIRef(f"http://switch.com/rnd#{self.name}"), rdflib.URIRef(f"http://switch.com/rnd#hasLogicOption"), rdflib.URIRef(f"http://switch.com/rnd#{logic_option.name}")))
                # inverse
                res_option.graph.add((rdflib.URIRef(f"http://switch.com/rnd#{logic_option.name}"), rdflib.URIRef(f"http://switch.com/rnd#isLogicOptionOf"), rdflib.URIRef(f"http://switch.com/rnd#{self.name}")))


            # add to outputs
            res_output[logic_option.__name__] = res_option
            df_output = pd.concat([df_output, df_option], ignore_index=True)
            df_output.fillna(0, inplace=True) # some NaNs are being returned; need to address this earlier.
        
        return (res_output, df_output)

    @classmethod
    def get_match_diagram_graph(self, dataset:rdflib.Graph, match_record):
        """
        match_record = { ... , ?target: str(URIRef), _match_id: str(uuid), _logic: str(uuid), _module: str(uuid) }
        """

        # lookup logic option (should only be 1, hence we take first element of list)
        logic_option = next( iter(filter(lambda x: str(x.uuid) == match_record['_logic'], self.logic_modules)), None)
        # run diagram graph creator
        diagram_g = dataset.query(logic_option.diagram_query, initBindings={'target': rdflib.URIRef(match_record['?target'])})
        # process graph in 

        return diagram_g
    

MODULE = MODULE_BMG_Passing_Valve
