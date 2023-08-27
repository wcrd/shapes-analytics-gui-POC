import rdflib
import pandas as pd
from typing import Tuple, Callable, Dict
import uuid
from types import SimpleNamespace
from enum import Enum
import math
from functools import reduce
from ..helpers import flatten

from ..logic_master import classEnum

class ASHRAE_Pressure_Trim_and_Respond(object):
    cType = classEnum.LOGIC_OPTION
    uuid = uuid.UUID("897bf465-a561-4f02-bac3-646b459cc246")
    name = "ASHRAE_Pressure_Trim_and_Respond"

    description = """
        ASHRAE G36 s5.1.14. Trim & Respond (T&R) logic resets a set point for pressure,
        temperature, or other variables at an air handler or plant. It
        reduces the set point at a fixed rate until a downstream zone is
        no longer satisfied and generates a request. When a sufficient
        number of requests are present, the set point is increased in
        response. The importance of each zone's requests can be
        adjusted to ensure that critical zones are always satisfied.
        When a sufficient number of requests no longer exist, the set
        point resumes decreasing at its fixed rate
        """

    sparql_query = """
        WHERE {
            ?target rdf:type/rdfs:subClassOf* brick:Equipment .
            
            # Target point requirement
            ?target brick:hasPoint ?p1 .
            ?target brick:hasPoint ?p2 .
            ?p1 rdf:type brick:Discharge_Air_Static_Pressure_Sensor .
            ?p2 rdf:type brick:Discharge_Air_Static_Pressure_Setpoint .
            
            # Target relationship requirements
            ?target brick:feeds* ?terminal_unit .
            ?terminal_unit rdf:type/rdfs:subClassOf* brick:Terminal_Unit .

            # Requirements on Property on that relationship
            ?terminal_unit brick:hasPart ?damper .
            ?damper rdf:type switch:Discharge_Damper .
            ?damper brick:hasPoint ?tu_damperPos .
            ?tu_damperPos rdf:type ?damperPosType .
            VALUES ?damperPosType { brick:Position_Sensor brick:Position_Command } .

            BIND(UUID() as ?match_id)
        }
        """
    
    _sparql_return = {
        # This module does post-processing of match results to get into the right form
        "SELECT": f"""
            SELECT ("{name}" as ?option) ?match_id ?target (?p1 as ?m_b1) (?p2 as ?m_b2) ?terminal_unit (?tu_damperPos as ?m_b3)
            """,
        "CONSTRUCT": None
    }

    # def _diagram_query(target):
    #     return f"""
    #         CONSTRUCT {{
    #             ?target rdf:type ?t_type ;
    #                 brick:hasPoint ?p1, ?p2 .
                
    #             ?p1 rdf:type brick:Discharge_Air_Static_Pressure_Sensor ;
    #                 brick:isPointOf ?target .
    #             ?p2 rdf:type brick:Discharge_Air_Static_Pressure_Setpoint ;
    #                 brick:isPointOf ?target .

    #             ?downstream_1 brick:feeds ?downstream_2 ;
    #                 rdf:type ?d1_type ;
    #                 rdfs:label ?d2_label .

    #             ?downstream_2 rdf:type ?d2_type ;
    #                 rdfs:label ?d2_label .
                
    #             # TU definition is covered off by downstream_2; just need to add additional parts
    #             ?tu brick:hasPart ?damper .
    #             ?damper rdf:type switch:Discharge_Damper ;
    #                 rdfs:label ?d_label ;
    #                 brick:hasPoint ?tu_damperPos ;
    #                 brick:isPartOf ?tu .
    #             ?tu_damperPos rdf:type ?damperPosType ;
    #                 brick:isPointOf ?damper .
    #         }}
    #          WHERE {{
                
    #             ?target brick:hasPoint ?p1 .
    #             ?target brick:hasPoint ?p2 .
    #             ?p1 rdf:type brick:Discharge_Air_Static_Pressure_Sensor .
    #             ?p2 rdf:type brick:Discharge_Air_Static_Pressure_Setpoint .

    #             # PATH RESOLVER
    #             ?target brick:feeds* ?downstream_1 .
    #             ?downstream_1 brick:feeds ?downstream_2 .
    #             ?downstream_2 brick:feeds* ?tu .
    #             ?tu rdf:type/rdfs:subClassOf* brick:Terminal_Unit .
                
    #             # PATH TERMINATION CONDITIONS
    #             ?tu brick:hasPart ?damper .
    #             ?damper rdf:type switch:Discharge_Damper .
    #             ?damper brick:hasPoint ?tu_damperPos .
    #             ?tu_damperPos rdf:type ?damperPosType .
    #             VALUES ?damperPosType {{ brick:Position_Sensor brick:Position_Command }}
                
    #             # get metadata to fill out model
    #             ?target rdf:type ?t_type .
    #             OPTIONAL {{ ?target rdfs:label ?t_label }} .
    #             ?downstream_1 rdf:type ?d1_type .
    #             OPTIONAL {{ ?downstream_1 rdfs:label ?d1_label }} .
    #             ?downstream_2 rdf:type ?d2_type .
    #             OPTIONAL {{ ?downstream_2 rdfs:label ?d2_label }} .
    #             OPTIONAL {{ ?damper rdfs:label ?d_label }} .
  
    #             # VALUES ?target {{{ target }}}
    #     }}
    # """

    diagram_query =  """
        CONSTRUCT {
            ?target rdf:type ?t_type ;
                brick:hasPoint ?p1, ?p2 .
            
            ?p1 rdf:type brick:Discharge_Air_Static_Pressure_Sensor ;
                brick:isPointOf ?target .
            ?p2 rdf:type brick:Discharge_Air_Static_Pressure_Setpoint ;
                brick:isPointOf ?target .

            ?downstream_1 brick:feeds ?downstream_2 ;
                rdf:type ?d1_type ;
                rdfs:label ?d2_label .

            ?downstream_2 rdf:type ?d2_type ;
                rdfs:label ?d2_label .
            
            # TU definition is covered off by downstream_2; just need to add additional parts
            ?tu brick:hasPart ?damper .
            ?damper rdf:type switch:Discharge_Damper ;
                rdfs:label ?d_label ;
                brick:hasPoint ?tu_damperPos ;
                brick:isPartOf ?tu .
            ?tu_damperPos rdf:type ?damperPosType ;
                brick:isPointOf ?damper .
        }
        WHERE {
            
            ?target brick:hasPoint ?p1 .
            ?target brick:hasPoint ?p2 .
            ?p1 rdf:type brick:Discharge_Air_Static_Pressure_Sensor .
            ?p2 rdf:type brick:Discharge_Air_Static_Pressure_Setpoint .

            # PATH RESOLVER
            ?target brick:feeds* ?downstream_1 .
            ?downstream_1 brick:feeds ?downstream_2 .
            ?downstream_2 brick:feeds* ?tu .
            ?tu rdf:type/rdfs:subClassOf* brick:Terminal_Unit .
            
            # PATH TERMINATION CONDITIONS
            ?tu brick:hasPart ?damper .
            ?damper rdf:type switch:Discharge_Damper .
            ?damper brick:hasPoint ?tu_damperPos .
            ?tu_damperPos rdf:type ?damperPosType .
            VALUES ?damperPosType { brick:Position_Sensor brick:Position_Command }
            
            # get metadata to fill out model
            ?target rdf:type ?t_type .
            OPTIONAL { ?target rdfs:label ?t_label } .
            ?downstream_1 rdf:type ?d1_type .
            OPTIONAL { ?downstream_1 rdfs:label ?d1_label } .
            ?downstream_2 rdf:type ?d2_type .
            OPTIONAL { ?downstream_2 rdfs:label ?d2_label } .
            OPTIONAL { ?damper rdfs:label ?d_label } .

        }"""

    params = """
        m_b1: Discharge Air Pressure Sensor
        m_b2: Discharge Air Pressure Setpoint
        m_b3[]: List of downstream terminal unit discharge damper position sensors
        -
        options:
            ashrae_params{}: G36 5.1.14.4 T&R control parameters
                sp0=120,        # Pa; Initial setpoint; entity metadata
                spmin=37,       # Pa; Minimum setpoint; entity metadata
                spmax=370,      # Pa; Maximum setpoint; entity metadata
                td=5,           # minutes; delay timer
                t=2,            # minutes; time step
                I=2,            # Number of ignored requests, i.e. minimum number of requests needed to activate sequence
                sptrim=-10,     # Pa; trim amount
                spres=15,       # Pa; Respond amount (opposite of trim; i.e. increase pressure step)
                spres_max=37,   # Pa; Maximum response per time interval
                damp_pos_pressure_request_threshold=95, # % ; position damper has to exceed to count as a 'pressure request'.
    """

    @classmethod
    def find_matches(self, dataset:rdflib.Graph, return_type="SELECT") -> Tuple[rdflib.query.Result, pd.DataFrame, pd.DataFrame]:
        # Initial SPARQL Query
        _query = self._sparql_return[return_type] + self.sparql_query
        res = dataset.query(_query)
        res_df = pd.DataFrame(res, columns=[v.toPython() for v in res.vars])

        # Process Results
        # 1. collapse terminal unit damper pos into list[] per terminal unit (by all other fields) -> L[tu_dmpr_pos]
        # 2. grouped by target with values list[target_p1], list[target_p2], list[ L[tu_dmpr_pos] ]
        #
        # This give us, for each target, a list of possible p1 & p2 points to pick, AND a list damper pos points for each terminal unit it feeds, with each list element being a list of all valid
        # points for that particular Terminal Unit!

        res_grp = res_df.astype(str).groupby(by=['?option', '?target', '?m_b1', '?m_b2', '?terminal_unit'], group_keys=True)['?m_b3'].apply(set).reset_index()
        final_res = res_grp.groupby(by=['?option', '?target']).agg({'?m_b1': set, '?m_b2': set, '?terminal_unit': list, '?m_b3': list}).reset_index()
        
        # query result, query result Dataframe, Processed Matched DataFrame
        return (res, final_res)

    @classmethod
    def prepare_match(self, match:pd.DataFrame, modelQueryFunc:Callable=None, modelQueryFuncArgs:dict={}) -> Tuple[dict, dict]:
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
                'm_b3': [ list(pnts)[0].toPython() for pnts in match['?m_b3'] ]
            }

        # Reduce to simple list of sensors
        sensors = set()
        for v in sensors_in_use.values():
            sensors.update(flatten(v))
        
        module_sensors={}
        # If the model query function has been provided, use it to get entity ids for telemetry
        if modelQueryFunc:
            sensor_id_map = modelQueryFunc(**{"entities": list(sensors), **modelQueryFuncArgs})

            module_sensors = {
                'm_b1': sensor_id_map[ sensors_in_use['m_b1'] ],
                'm_b2': sensor_id_map[ sensors_in_use['m_b2'] ],
                'm_b3': [ sensor_id_map[ s ] for s in sensors_in_use['m_b3'] ]
            }
        else:
            print("Model query function not provided; unable to fetch external store telemetry ids for provided entities.")
        
        return ( sensor_id_map, module_sensors)


    @classmethod
    def run_module(self, data:pd.DataFrame, sensors:dict, options:dict={}, debug=False):
        _sensors_default = {
            'm_b1': None,
            'm_b2': None,
            'm_b3': []
        }

        _options = {
            'ashrae_params': {}
        }

        # manually merge sensors dict
        _sensors = {k:v for d in (_sensors_default, sensors) for k,v in d.items()}
        
        # check for certain option
        if "ashrae_params" not in options:
            print("No ASHRAE parameters provided. Using defaults. It is highly recommended to provide these parameters")
            print("Defaults: \n", vars(ASHRAE_Pressure_Trim_and_Respond_ControlModule._ashrae_parameters))
        else:
            _options['ashrae_params'].update(options['ashrae_params'])

        # initialise logic module with state
        lm = ASHRAE_Pressure_Trim_and_Respond_ControlModule()
        
        temp_df = data.apply(lm, **{**_sensors, **_options, 'debug': debug}, axis=1)

        return temp_df



class ASHRAE_Pressure_Trim_and_Respond_ControlModule(object):
    cType = classEnum.CONTROL_MODULE
    uuid = uuid.UUID('cc2ed7c6-0420-4a66-ae64-002adf99466f')
    name = "ASHRAE G36 s5.1.14.4 T&R Control Sequence"

    ControlMode = Enum("ControlMode", ['FLOAT', 'ACTIVE', 'INACTIVE'])

    description = """
        Every timestamp after delay trim pressure SP by STrim .
        If R - I > 0, Respond to SP by max( (R-I)*SPres, 37)
        So NET change to SP is { RESPOND - TRIM }
        """
    
    # ASHRAE parameters: Guideline 36 s5.1.14.3
    # These should be updated by the function caller by providing an ashrae_params arg when this class is called
    _ashrae_parameters = SimpleNamespace(
        sp0=120,        # Pa; Initial setpoint; entity metadata
        spmin=37,       # Pa; Minimum setpoint; entity metadata
        spmax=370,      # Pa; Maximum setpoint; entity metadata
        td=5,           # minutes; delay timer
        t=2,            # minutes; time step
        I=2,            # Number of ignored requests, i.e. minimum number of requests needed to activate sequence
        sptrim=-10,     # Pa; trim amount
        spres=15,       # Pa; Respond amount (opposite of trim; i.e. increase pressure step)
        spres_max=37,   # Pa; Maximum response per time interval
        damp_pos_pressure_request_threshold=95, # % ; position damper has to exceed to count as a 'pressure request'.
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.state = SimpleNamespace(
            timestamp_entityActive = None,                  # timestamp when entity became active; None if entity not active.
            flag_entityActive_GT_td = False,                # time since entity became active > td variable?
            t_sinceLastCommand = 0,                         # time since last control change was made
            control_sequence = self.ControlMode.INACTIVE,   # Float, Active, Inactive
            control_command = None,                         # Pa ; current pressure setpoint command as per this module
        )

    def __call__(self, row, m_b1=None, m_b2=None, m_b3:list=[], ashrae_params={}, debug=False):
        """
        m_b1: DAP
        m_b2: DAP SP
        m_b3: DAD{Position}[] ; list downstream terminal unit discharge damper position points
        -
        ashrae_params: parameters for the T&R sequence as defined in section s5.1.14.3. Defaults are provided but these should be updated per target based on metadata.
        """

        # ABOUT
        # This module works by continuously reducing the pressure setpoint by strim after some runtime delay conditions are met (td) [ mode = trim ]
        # If the number of requests R exceeds the threshold I, then the module will increase the pressure by spres*(R-I) until all but 2 dampers are satisfied (damp_pos_pressure_request_satisfied),
        # up to the maximum limit spres_max [ mode = respond ]
        # The module makes changes every timestep T

        # ASHRAE parameters: Defaults & User provided
        _ashrae_params = SimpleNamespace(**{**vars(self._ashrae_parameters), **ashrae_params})

        # INITIALISE calc variables
        var_I, var_R, var_S, rogue_zones = None, None, None, None
        _response_delta = None

        # 1. Check target entity is active & update state
        # I don't have active points yet; skip for now.
        # TEMP: If DAP==0 use this as standin for active, just for now.
        entity_active = bool(row[m_b1] > 5 ) # lt 5 Pa

        # if not active, reset vars and set setpoint to sp0, return.
        if not entity_active:
            self.state.timestamp_entityActive = None
            self.state.flag_entityActive_GT_td = False
            self.state.control_sequence = self.ControlMode.INACTIVE
            self.state.control_command = _ashrae_params.sp0
            ## EXIT FUNCTION

        # else if active && entity was not previously active
        elif entity_active and self.state.timestamp_entityActive == None:
            self.state.timestamp_entityActive = row.name
            ## EXIT FUNCTION; control action = None

        # else if active, and has not been active longer than time delay, check to see if timedelay has been exceeded
        elif entity_active and not self.state.flag_entityActive_GT_td:
            # calc time since active
            t_diff = (row.name - self.state.timestamp_entityActive).seconds/60
            if (t_diff > _ashrae_params.td):
                self.state.flag_entityActive_GT_td = True
                # CONTINUE INTO CONTROL CALC BELOW
            else:
                self.state.flag_entityActive_GT_td = False
                ## EXIT FUNCTION; delay has not been met yet.
        
        if entity_active and self.state.flag_entityActive_GT_td:
            # Run CONTROL function!
            self.state.control_sequence = self.ControlMode.ACTIVE

            # 2. Count Rogue Zones
            rogue_zones = 0 # implement this logic later; for now I am just going to count NaN reported positions as rogue zones!
            rogue_zones = sum(math.isnan(x) for x in row[m_b3])
            var_I = rogue_zones + _ashrae_params.I

            # 3. Count pressure requests and pressure satisfied dampers
            var_R = 0 # R (pressure request count)
            var_S = 0 # S (pressure satisfied count)
            for tu_pos in m_b3:
                # get importance multiplier from entity metadata
                # for now we don't have so use 1 for all
                var_IM = 1

                if row[tu_pos] >= _ashrae_params.damp_pos_pressure_request_threshold: var_R+=1
                elif row[tu_pos] < _ashrae_params.damp_pos_pressure_request_threshold: var_S+=1
            

            # 4. Control Logic
            control_command = None

            # 5. Calculate Adjustment
            # Net = Trim + Response -> range [spmin, spmax]
            _response_delta = min(_ashrae_params.spres * max(var_R - var_I, 0), _ashrae_params.spres_max)
            _command_raw = row[m_b2] + _response_delta + _ashrae_params.sptrim
            self.state.control_command = max(min(_command_raw, _ashrae_params.spmax), _ashrae_params.spmin)

        ## RETURN
        # DEBUG
        if debug:
            downstream_dampers = row[m_b3].agg(["min", "max", "mean"])
            downstream_dampers['state'] = f"{self.state}"
            downstream_dampers['_state_sequence'] = self.state.control_sequence
            downstream_dampers['var_R'] = var_R
            downstream_dampers['var_S'] = var_S
            downstream_dampers['var_I'] = var_I
            downstream_dampers['entity_active'] = entity_active
            downstream_dampers['_response_delta'] = _response_delta
            downstream_dampers['control_command'] = self.state.control_command
            downstream_dampers['DAPSP'] = row[m_b2]
            downstream_dampers['DAP'] = row[m_b1]
            return downstream_dampers
        else:
            return pd.Series(self.state.control_command, index=["control_command"])

# MODULE
class MODULE_ASHRAE_Pressure_Trim_and_Respond(object):
    cType = classEnum.MODULE
    uuid = uuid.UUID("2f1cae16-0fb0-4ae7-9edb-b7c44a8357f5")
    name = "MODULE_Pressure_Trim_and_Respond_per_ASHRAE_G36"

    # Ranked tuple of logic options for this module
    # TODO: change this to dict comprehension; key=uuid, rank as field.
    logic_modules = (
        ASHRAE_Pressure_Trim_and_Respond,
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

    

MODULE = MODULE_ASHRAE_Pressure_Trim_and_Respond