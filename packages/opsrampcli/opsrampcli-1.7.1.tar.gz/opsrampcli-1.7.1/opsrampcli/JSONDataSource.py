import json
from requests_ntlm import HttpNtlmAuth
import pandas as pd
import os
import logging
from opsrampcli.DataSource import DataSource

logger = logging.getLogger(__name__)

URLSOURCE_DISPLAY_VALUE = 'display_value'


class JSONDataSource(DataSource):

    class JSONDataSourceException(DataSource.DataSourceException):
        pass

    def get_resources_df(self):
        job = self.job
        filename = os.getenv("JSONSOURCE_FILENAME") or job['source']['jsonsource']['filename']
        result_key = os.getenv("JSONSOURCE_RESULT_KEY") or job['source']['jsonsource']['result_key'] or 'result'
        logger.info(f'Getting records from JSON file {filename}...')
        try:
            with open(filename, 'r') as f:
                responsedict = json.load(f)
        except Exception as e:
            msg = f'Failed to retrieve records from JSON file {filename}: {e}'
            raise JSONDataSource.JSONDataSourceException(msg)
        records = responsedict.get(result_key, [])
        processed_recs = []
        for record in records:
            newrec = {}
            for key,value in record.items():
                if isinstance(value, dict) and URLSOURCE_DISPLAY_VALUE in value:
                    newrec[key] = value[URLSOURCE_DISPLAY_VALUE]
                else:
                    newrec[key] = value
            processed_recs.append(newrec)

        self.df = pd.DataFrame(processed_recs)
        self.df.fillna("", inplace=True)
