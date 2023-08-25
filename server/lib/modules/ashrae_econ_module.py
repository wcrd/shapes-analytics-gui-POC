import rdflib
import pandas as pd
from typing import Tuple, Dict
import uuid

from ..logic_master import classEnum

# LOGIC OPTIONS

class ASHRAE_Econ_HL_Shutoff_Diff_Enthalpy(object):
    cType = classEnum.LOGIC_OPTION
    uuid = uuid.UUID("d09c3a85-ebef-4ee4-b664-ec6777a2f344")
    name = "ASHRAE_Econ_HL_Shutoff_Diff_Enthalpy"

    description = """
        Air Economizer High-Limit Shutoff Exceeding ASHRAE Standards: Differential enthalpy with fixed drybulb temperature control
        """
    sparql_query = """
        WHERE {
            # META
            OPTIONAL {
                ?this rdfs:label ?label .
            }

            # BLOCK 1 - ACTIVE POINT
            OPTIONAL {
                {
                    ?this brick:hasPoint ?m_b1 .
                    ?m_b1 rdf:type ?point_type1 .
                    VALUES ?point_type1 { brick:On_Off_Status brick:On_Off_Command brick:Enable_Status brick:Enable_Command brick:Operating_Mode_Status switch:Operating_Mode_Command }
                    BIND("Primary" as ?m_b1_mode)
                } UNION {
                    # Fall back active point; DAF Run
                    ?this brick:hasPart ?part_run .
                    ?part_run rdf:type brick:Discharge_Fan .
                    ?part_run brick:hasPoint ?m_b1 .
                    ?m_b1 rdf:type ?run_status .
                    VALUES ?run_status { brick:On_Off_Status brick:On_Off_Command }
                    BIND("Alt:DAF" as ?m_b1_mode)
                }
            }

            # BLOCK 2 - ECON MODE
            OPTIONAL {
                ?this brick:hasPoint ?m_b2 .
                ?m_b2 rdf:type ?point_type2 .
                VALUES ?point_type2 { switch:Economy_Operating_Mode_Status switch:Economy_Operating_Mode_Enable_Status switch:Economy_Operating_Mode_Enable_Command }
            }

            # BLOCK 3 - OAT OR ENTHALPY
            OPTIONAL {
                {
                    # BLOCK 3_1
                    ?this brick:hasPoint ?m_b3_1 .
                    ?m_b3_1 rdf:type ?point_type3 .
                    VALUES ?point_type3 { brick:Outside_Air_Temperature_Sensor } .
                    BIND("OAT" as ?m_b3_mode) .
                } UNION {
                    # BLOCK 3_2
                    ?this brick:hasPoint ?m_b3_2_1 .
                    ?this brick:hasPoint ?m_b3_2_2 .
                    ?m_b3_2_1 rdf:type brick:Outside_Air_Enthalpy_Sensor .
                    ?m_b3_2_2 rdf:type brick:Return_Air_Enthalpy_Sensor .
                    BIND("Enthalpy" as ?m_b3_mode)
                }
            }

            # BLOCK 4 - OPTIONAL
            OPTIONAL {
                ?this brick:hasPoint ?m_ob_1 .
                ?m_ob_1 rdf:type brick:Outside_Air_Lockout_Temperature_Setpoint .
            }
            
            {
                SELECT ?this
                WHERE {
                    ?this rdf:type ?eT .
                    VALUES ?eT { brick:RTU brick:AHU } .
                }
            }
            
            # FILTER OUT ENTITIES THAT HAVE NO MATCHES
            # Turn On/Off depending if you want to see what failed.

            FILTER( bound( ?m_b1 ) )
            FILTER( bound( ?m_b2 ) )
            FILTER( bound( ?m_b3_1) || ( bound( ?m_b3_2_1 ) && bound( ?m_b3_2_2 ) ) )

            BIND(UUID() as ?match_id)
        }

        """
    
    _sparql_return = {
        "SELECT": """
            SELECT ("{name}" as ?option) ?match_id (?this as ?entity) ?label ?m_b1_mode ?m_b1 ?m_b2 ?m_b3_mode ?m_b3_1 ?m_b3_2_1 ?m_b3_2_2 ?m_ob_1
            """,
        "CONSTRUCT": f"""
            CONSTRUCT {{
                ?match_id rdf:type rnd:moduleTarget ;
                    rnd:entityTarget ?this ;
                    rnd:entityTargetLabel ?label ;
                    rnd:logic_option rnd:{name} .  
            }}
        """
    }

    params = """
        m_b1: Entity is Active
        m_b2: Econ Mode is Active
        m_b3_1: OAT
        m_b3_2_1: OA Enthalpy
        m_b3_2_2: RA Enthalpy
        m_ob_1: OA Lockout Temperature Setpoint
        -
        oat_lim_F = OAT threshold in Farenheit
        optional = Include optional sensors, if available
    """

    @classmethod
    def find_matches(self, dataset:rdflib.Graph, return_type="SELECT") -> Tuple[rdflib.query.Result, pd.DataFrame]:
        _query = self._sparql_return[return_type] + self.sparql_query
        res = dataset.query(_query)
        res_df = pd.DataFrame(res, columns=res.vars)
        return (res, res_df)
    
    @classmethod
    def run_module(self, data:pd.DataFrame, sensors:dict, options:dict={}):
        # params for this module
        _sensors_default = {
            'm_b1': None,
            'm_b2': None,
            'm_b3_1': None,
            'm_b3_2_1': None,
            'm_b3_2_2': None,
            'm_ob_1': None
        }
        _options = {
            "oat_lim_F": 75
        }
        # manually merge sensors dict
        _sensors = {k:v for d in (_sensors_default, sensors) for k,v in d.items()}
        # auto merge options
        _options.update(options)

        # print(_sensors, _options)
        # run module in PANDAS (this will come from class, for now pass as arg: data)
        temp_df = data.apply(self._module, **{**_sensors, **_options}, axis=1)

        return temp_df

    @classmethod
    def _module(self, row, m_b1=None, m_b2=None, m_b3_1=None, m_b3_2_1=None, m_b3_2_2=None, m_ob_1=None, oat_lim_F = 75, optional=True):
        """
        # MODULE
        # Air Economizer High-Limit Shutoff Exceeding ASHRAE Standards: Differential enthalpy with fixed drybulb temperature control
        #
        m_b1: Entity is Active
        m_b2: Econ Mode is Active
        m_b3_1: OAT
        m_b3_2_1: OA Enthalpy
        m_b3_2_2: RA Enthalpy
        m_ob_1: OA Lockout Temperature Setpoint
        -
        oat_lim_F = OAT threshold in Farenheit
        optional = Include optional sensors, if available
        """
        # DEBUG
        # print("ROW: ", row)
        # print(locals())

        # CORE
        p1 = bool(row[m_b1]) and bool(row[m_b2])
        if m_b3_2_1 and m_b3_2_2:
            p2 = row[m_b3_2_1] > row[m_b3_2_2]
        elif m_b3_1:
            p2 = row[m_b3_1] > oat_lim_F
        else:
            raise ValueError("Missing variable m_b2_x")

        core = p1 and p2

        # OPTIONAL
        if m_ob_1:
            o1 = row[m_ob_1] > oat_lim_F
        else:
            o1 = False

        optional = o1

        # FINAL
        output = core or optional

        return output
    
class ASHRAE_Econ_HL_Shutoff_Fixed_DB(object):
    cType = classEnum.LOGIC_OPTION
    uuid = uuid.UUID("f64e4dfe-b106-4ad8-86f4-0ffa792f7bb9")
    name = "ASHRAE_Econ_HL_Shutoff_Fixed_DB"

    description = """
        Air Economizer High-Limit Shutoff Exceeding ASHRAE Standards: Fixed drybulb temperature control
        """

    sparql_query = """
        WHERE {
            # META
            OPTIONAL {
                ?this rdfs:label ?label .
            }

            # BLOCK 1 - ACTIVE POINT
            OPTIONAL {
                {
                    ?this brick:hasPoint ?m_b1 .
                    ?m_b1 rdf:type ?point_type1 .
                    VALUES ?point_type1 { brick:On_Off_Status brick:On_Off_Command brick:Enable_Status brick:Enable_Command brick:Operating_Mode_Status switch:Operating_Mode_Command }
                    BIND("Primary" as ?m_b1_mode)
                } UNION {
                    # Fall back active point; DAF Run
                    ?this brick:hasPart ?part_run .
                    ?part_run rdf:type brick:Discharge_Fan .
                    ?part_run brick:hasPoint ?m_b1 .
                    ?m_b1 rdf:type ?run_status .
                    VALUES ?run_status { brick:On_Off_Status brick:On_Off_Command }
                    BIND("Alt:DAF" as ?m_b1_mode)
                }
            }

            # BLOCK 2 - ECON MODE
            OPTIONAL {
                ?this brick:hasPoint ?m_b2 .
                ?m_b2 rdf:type ?point_type2 .
                VALUES ?point_type2 { switch:Economy_Operating_Mode_Status switch:Economy_Operating_Mode_Enable_Status switch:Economy_Operating_Mode_Enable_Command }
            }

            # BLOCK 3 - OAT
            OPTIONAL {
                ?this brick:hasPoint ?m_b3 .
                ?m_b3 rdf:type ?point_type3 .
                VALUES ?point_type3 { brick:Outside_Air_Temperature_Sensor } .
            }

            # BLOCK 4 - OPTIONAL
            OPTIONAL {
                ?this brick:hasPoint ?m_ob_1 .
                ?m_ob_1 rdf:type brick:Outside_Air_Lockout_Temperature_Setpoint .
            }

            {
                SELECT ?this
                WHERE {
                    ?this rdf:type ?eT .
                    VALUES ?eT { brick:RTU brick:AHU } .
                }
            }
            
            # FILTER OUT ENTITIES THAT HAVE NO MATCHES
            # Turn On/Off depending if you want to see what failed.

            FILTER( bound( ?m_b1 ) )
            FILTER( bound( ?m_b2 ) )
            FILTER( bound( ?m_b3 ) )

            BIND(UUID() as ?match_id)
        }
        """

    _sparql_return = {
        "SELECT": """
            SELECT ("{name}" as ?option) ?match_id (?this as ?entity) ?label ?m_b1_mode ?m_b1 ?m_b2 ?m_b3 ?m_ob_1
        """,
        "CONSTRUCT": f"""
            CONSTRUCT {{
                ?match_id rdf:type rnd:moduleTarget ;
                    rnd:entityTarget ?this ;
                    rnd:entityTargetLabel ?label ;
                    rnd:logic_option rnd:{name} .  
            }}
        """
    }

    params = """
        m_b1: Entity is Active
        m_b2: Econ Mode is Active
        m_b3: OAT
        m_ob_1: OA Lockout Temperature Setpoint
        -
        ashrae_econ_temp_HL: ASHRAE Economizer Temperature High-Limit
        -
        oat_lim_F = OAT threshold in Farenheit
        optional = Include optional sensors, if available
    """

    @classmethod
    def find_matches(self, dataset:rdflib.Graph, return_type="SELECT") -> Tuple[rdflib.query.Result, pd.DataFrame]:
        _query = self._sparql_return[return_type] + self.sparql_query
        res = dataset.query(_query)
        res_df = pd.DataFrame(res, columns=res.vars)
        return (res, res_df)
    
    @classmethod
    def run_module(self, data:pd.DataFrame, sensors:dict, options:dict={}):
        print("Method not defined")
        pass
    
    @classmethod
    def _module(self, row, m_b1=None, m_b2=None, m_b3=None, m_ob_1=None, ashrae_econ_temp_HL=None, optional=True):
        """
        # MODULE
        # Air Economizer High-Limit Shutoff Exceeding ASHRAE Standards: Differential enthalpy with fixed drybulb temperature control
        #
        m_b1: Entity is Active
        m_b2: Econ Mode is Active
        m_b3: OAT
        m_ob_1: OA Lockout Temperature Setpoint
        ashrae_econ_temp_HL: ASHRAE Economizer Temperature High-Limit
        -
        optional = Include optional sensors, if available
        """

        pass

class ASHRAE_Econ_HL_Shutoff_Diff_DB(object):
    cType = classEnum.LOGIC_OPTION
    uuid = uuid.UUID("a626bab6-937d-4027-904a-c5b22611cd77")
    name = "ASHRAE_Econ_HL_Shutoff_Diff_DB"

    description = """
        Air Economizer High-Limit Shutoff Exceeding ASHRAE Standards: Differential drybulb temperature control
        """

    sparql_query = """
        WHERE {
            # META
            OPTIONAL {
                ?this rdfs:label ?label .
            }

            # BLOCK 1 - ACTIVE POINT
            OPTIONAL {
                {
                    ?this brick:hasPoint ?m_b1 .
                    ?m_b1 rdf:type ?point_type1 .
                    VALUES ?point_type1 { brick:On_Off_Status brick:On_Off_Command brick:Enable_Status brick:Enable_Command brick:Operating_Mode_Status switch:Operating_Mode_Command }
                    BIND("Primary" as ?m_b1_mode)
                } UNION {
                    # Fall back active point; DAF Run
                    ?this brick:hasPart ?part_run .
                    ?part_run rdf:type brick:Discharge_Fan .
                    ?part_run brick:hasPoint ?m_b1 .
                    ?m_b1 rdf:type ?run_status .
                    VALUES ?run_status { brick:On_Off_Status brick:On_Off_Command }
                    BIND("Alt:DAF" as ?m_b1_mode)
                }
            }

            # BLOCK 2 - ECON MODE
            OPTIONAL {
                ?this brick:hasPoint ?m_b2 .
                ?m_b2 rdf:type ?point_type2 .
                VALUES ?point_type2 { switch:Economy_Operating_Mode_Status switch:Economy_Operating_Mode_Enable_Status switch:Economy_Operating_Mode_Enable_Command }
            }

            # BLOCK 3 - OAT
            OPTIONAL {
                ?this brick:hasPoint ?m_b3 .
                ?m_b3 rdf:type ?point_type3 .
                VALUES ?point_type3 { brick:Outside_Air_Temperature_Sensor } .
            }

            # BLOCK 4 - RAT
            OPTIONAL {
                ?this brick:hasPoint ?m_b4 .
                ?m_b4 rdf:type ?point_type4 .
                VALUES ?point_type4 { brick:Return_Air_Temperature_Sensor } .
            }

            {
                SELECT ?this
                WHERE {
                    ?this rdf:type ?eT .
                    VALUES ?eT { brick:RTU brick:AHU } .
                }
            }
            
            # FILTER OUT ENTITIES THAT HAVE NO MATCHES
            # Turn On/Off depending if you want to see what failed.

            FILTER( bound( ?m_b1 ) )
            FILTER( bound( ?m_b2 ) )
            FILTER( bound( ?m_b3 ) )
            FILTER( bound( ?m_b4 ) )

            BIND(UUID() as ?match_id)
        }
        """

    _sparql_return = {
        "SELECT": """
            SELECT ("{name}" as ?option) ?match_id (?this as ?entity) ?label ?m_b1_mode ?m_b1 ?m_b2 ?m_b3 ?m_b4            
            """,
        "CONSTRUCT": f"""
            CONSTRUCT {{
                ?match_id rdf:type rnd:moduleTarget ;
                    rnd:entityTarget ?this ;
                    rnd:entityTargetLabel ?label ;
                    rnd:logic_option rnd:{name} .  
            }}
        """
    }

    params = """
        m_b1: Entity is Active
        m_b2: Econ Mode is Active
        m_b3: OAT
        m_b4: RAT
        -
        optional = Include optional sensors, if available
    """

    @classmethod
    def find_matches(self, dataset:rdflib.Graph, return_type="SELECT") -> Tuple[rdflib.query.Result, pd.DataFrame]:
        # Check ASHRAE Climate Zone first
        # find_climate_zone()
        # guard if not in (0B, 1B, 2B, 3B, 3C, 4B, 4C, 5A, 5B, 5C, 6A, 6B, 7, 8)
        # TODO: Write this

        # Query match
        _query = self._sparql_return[return_type] + self.sparql_query
        res = dataset.query(_query)
        res_df = pd.DataFrame(res, columns=res.vars)
        
        return (res, res_df)
    
    @classmethod
    def run_module(self, data:pd.DataFrame, sensors:dict, options:dict={}):
        print("Method not defined")
        pass
    
    @classmethod
    def _module(self, row, m_b1=None, m_b2=None, m_b3=None, m_ob_1=None, ashrae_econ_temp_HL=None, optional=True):
        """
        # MODULE
        # Air Economizer High-Limit Shutoff Exceeding ASHRAE Standards: Differential enthalpy with fixed drybulb temperature control
        #
        m_b1: Entity is Active
        m_b2: Econ Mode is Active
        m_b3: OAT
        m_ob_1: OA Lockout Temperature Setpoint
        ashrae_econ_temp_HL: ASHRAE Economizer Temperature High-Limit
        -
        optional = Include optional sensors, if available
        """

        pass

class ASHRAE_Econ_HL_Shutoff_Fixed_Enthalpy(object):
    cType = classEnum.LOGIC_OPTION
    uuid = uuid.UUID("f1770119-b670-471a-a7aa-00e9f88c9e8e")
    name = "ASHRAE_Econ_HL_Shutoff_Fixed_Enthalpy"

    description = """
        Air Economizer High-Limit Shutoff Exceeding ASHRAE Standards: Fixed enthalpy with fixed drybulb temperature control
        """

    sparql_query = """
        WHERE {
            # META
            OPTIONAL {
                ?this rdfs:label ?label .
            }

            # BLOCK 1 - ACTIVE POINT
            OPTIONAL {
                {
                    ?this brick:hasPoint ?m_b1 .
                    ?m_b1 rdf:type ?point_type1 .
                    VALUES ?point_type1 { brick:On_Off_Status brick:On_Off_Command brick:Enable_Status brick:Enable_Command brick:Operating_Mode_Status switch:Operating_Mode_Command }
                    BIND("Primary" as ?m_b1_mode)
                } UNION {
                    # Fall back active point; DAF Run
                    ?this brick:hasPart ?part_run .
                    ?part_run rdf:type brick:Discharge_Fan .
                    ?part_run brick:hasPoint ?m_b1 .
                    ?m_b1 rdf:type ?run_status .
                    VALUES ?run_status { brick:On_Off_Status brick:On_Off_Command }
                    BIND("Alt:DAF" as ?m_b1_mode)
                }
            }

            # BLOCK 2 - ECON MODE
            OPTIONAL {
                ?this brick:hasPoint ?m_b2 .
                ?m_b2 rdf:type ?point_type2 .
                VALUES ?point_type2 { switch:Economy_Operating_Mode_Status switch:Economy_Operating_Mode_Enable_Status switch:Economy_Operating_Mode_Enable_Command }
            }

            # BLOCK 3 - OAT
            OPTIONAL {
                ?this brick:hasPoint ?m_b3 .
                ?m_b3 rdf:type ?point_type3 .
                VALUES ?point_type3 { brick:Outside_Air_Temperature_Sensor } .
            }

            # BLOCK 4 - OA Enthalpy
            OPTIONAL {
                ?this brick:hasPoint ?m_b4 .
                ?m_b4 rdf:type ?point_type4 .
                VALUES ?point_type4 { brick:Outside_Air_Enthaply_Sensor } .
            }

            # BLOCK 5 - OPTIONAL
            OPTIONAL {
                ?this brick:hasPoint ?m_ob_1 .
                ?m_ob_1 rdf:type brick:Outside_Air_Lockout_Temperature_Setpoint .
            }

            {
                SELECT ?this
                WHERE {
                    ?this rdf:type ?eT .
                    VALUES ?eT { brick:RTU brick:AHU } .
                }
            }
            
            # FILTER OUT ENTITIES THAT HAVE NO MATCHES
            # Turn On/Off depending if you want to see what failed.

            FILTER( bound( ?m_b1 ) )
            FILTER( bound( ?m_b2 ) )
            FILTER( bound( ?m_b3 ) )
            FILTER( bound( ?m_b4 ) )

            BIND(UUID() as ?match_id)
        }
        """

    _sparql_return = {
        "SELECT": f"""
            SELECT ("{name}" as ?option) ?match_id (?this as ?entity) ?label ?m_b1_mode ?m_b1 ?m_b2 ?m_b3 ?m_b4 ?m_ob_1            
            """,
        "CONSTRUCT": f"""
            CONSTRUCT {{
                ?match_id rdf:type rnd:moduleTarget ;
                    rnd:entityTarget ?this ;
                    rnd:entityTargetLabel ?label ;
                    rnd:logic_option rnd:{name} .  
            }}
        """
    }

    params = """
        m_b1: Entity is Active
        m_b2: Econ Mode is Active
        m_b3: OAT
        m_b4: OA Enthalpy
        m_ob_1: OA Lockout Temperature Setpoint
        ashrae_econ_enth_HL_elev_adj: Elevation Adjusted ASHRAE Economizer Enthalpy High-Limit
        -
        oat_lim_F = OAT threshold in Farenheit
        optional = Include optional sensors, if available
    """

    @classmethod
    def find_matches(self, dataset:rdflib.Graph, return_type="SELECT") -> Tuple[rdflib.query.Result, pd.DataFrame]:
        # Query match
        _query = self._sparql_return[return_type] + self.sparql_query
        res = dataset.query(_query)
        res_df = pd.DataFrame(res, columns=res.vars)
        
        return (res, res_df)
    
    @classmethod
    def run_module(self, data:pd.DataFrame, sensors:dict, options:dict={}):
        print("Method not defined")
        pass
    
    @classmethod
    def _module(self, row, m_b1=None, m_b2=None, m_b3=None, m_ob_1=None, ashrae_econ_enth_HL_elev_adj=None, oat_lim_F = 75, optional=True):
        """
        # MODULE
        # Air Economizer High-Limit Shutoff Exceeding ASHRAE Standards: Fixed enthalpy with fixed drybulb temperature control
        #
        m_b1: Entity is Active
        m_b2: Econ Mode is Active
        m_b3: OAT
        m_b4: OA Enthalpy
        m_ob_1: OA Lockout Temperature Setpoint
        ashrae_econ_enth_HL_elev_adj: Elevation Adjusted ASHRAE Economizer Enthalpy High-Limit
        -
        oat_lim_F = OAT threshold in Farenheit
        optional = Include optional sensors, if available
        """

        pass


# MODULE
class MODULE_Air_Economizer_High_Limit_Shutoff_Exceeding_ASHRAE_Standards(object):
    cType = classEnum.MODULE
    uuid = uuid.UUID("3d5cae16-0fb0-4ae7-9edb-b7c44a8357f5")
    name = "MODULE_Air_Economizer_High_Limit_Shutoff_Exceeding_ASHRAE_Standards"

    # Ranked tuple of logic options for this module
    logic_modules = (
        ASHRAE_Econ_HL_Shutoff_Diff_Enthalpy,
        ASHRAE_Econ_HL_Shutoff_Fixed_Enthalpy,
        ASHRAE_Econ_HL_Shutoff_Diff_DB,
        ASHRAE_Econ_HL_Shutoff_Fixed_DB
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
    

MODULE = MODULE_Air_Economizer_High_Limit_Shutoff_Exceeding_ASHRAE_Standards