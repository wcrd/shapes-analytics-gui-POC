import rdflib
import pandas as pd

class AnalyticsHelper(object):

    @classmethod
    def get_switch_sensor_ids(self, g:rdflib.Graph, module_match_record):

        # get all variable columns "m_"
        sensor_vars = module_match_record.filter(regex="^m_").fillna("")
        # get all sensors with URIs
        sensor_vars = sensor_vars.loc[lambda x: x.str.contains("http")]
        # print(sensor_vars)

        # process each sensor to get switch ID
        data = {}
        for idx, v in sensor_vars.items():
            id_res = list(g.objects(rdflib.URIRef(v), rdflib.URIRef("https://switchautomation.com/schemas/BrickExtension#hasObjectPropertyId")))[0].toPython()
            data[str(idx)] = id_res
        
        return data
    
    # SAME AS get_switch_sensor_ids, just a little better :)
    @staticmethod
    def rdfModelQueryFunc(
        entities:list,
        graph:rdflib.Graph, 
        predicate:rdflib.URIRef=rdflib.URIRef("https://switchautomation.com/schemas/BrickExtension#hasObjectPropertyId")
    ):
        output = {}
        for ent in entities:
            id_res = list(graph.objects(rdflib.URIRef(ent), predicate))[0].toPython()
            output[ent] = id_res
        
        return output

    @classmethod
    def _get_data_for_sensors(self, sensorIds:list, apiProjectId:str, queryEngine, ago='2d', startTs=None, endTs=None):
        str_format = [f'"{w}"' for w in sensorIds]
        query = f"Timeseries | where ObjectPropertyId in ({', '.join(str_format)}) | where TimestampLocal > ago({ago}) | project ObjectPropertyId, TimestampLocal, Value"


        return queryEngine.query(apiProjectId, query)
    
    @classmethod
    def get_ts_data(self, sensorIds:list, apiProjectId:str, queryEngine, ago="2d", startTs=None, endTs=None, resample="15T"):
        raw_df = self._get_data_for_sensors(sensorIds, apiProjectId, queryEngine, ago, startTs, endTs)
        # process
        raw_df.index = pd.to_datetime(raw_df['TimestampLocal'])
        raw_df['Value'].apply(pd.to_numeric)
        # pivot and resample
        df_pivot = raw_df.drop(['TimestampLocal'], axis=1).pivot_table(columns=['ObjectPropertyId'], values=['Value'], index=raw_df.index, aggfunc='mean')
        df_pivot.columns = df_pivot.columns.get_level_values(1)
        df_pivot = df_pivot.resample(resample).last()

        return {
            "raw": raw_df,
            "pivot": df_pivot
        }

    @staticmethod
    def resample_ts_data(ts_data:dict, resampleAt:str, **args):
        # need to reprocess the raw df into a new pivot and resample.
        df_pivot = ts_data['raw'].drop(['TimestampLocal'], axis=1).pivot_table(columns=['ObjectPropertyId'], values=['Value'], index=ts_data['raw'].index, aggfunc='mean')
        df_pivot.columns = df_pivot.columns.get_level_values(1)
        df_pivot.resample(resampleAt, **args).last()

        return {
            'raw': ts_data['raw'],
            'pivot': df_pivot
        }