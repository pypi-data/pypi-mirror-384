import requests
import json
from opsrampcli.DataSource import DataSource
import yaml
import importlib
import logging

logger = logging.getLogger(__name__)

def do_cmd_getincidents(ops, args):
    if args.count:
            print("Matched %i incidents." % (ops.get_incidents_count(args.query)))
    else:
        incidents = ops.get_incidents(args.query, 1, args.brief, args.details, args.filter)
        print(json.dumps(incidents, indent=2, sort_keys=False))
        if args.resolve:
            update = {"status": "Resolved"}
            for incident in incidents:
                try:
                    print(ops.post_incident_update(incident['id'], update))
                except requests.exceptions.RequestException as e:
                    print(e)

async def do_cmd_sync_incidents_with_datasource(ops, args):

    with open(args.job, 'r') as jobfile:
        job = yaml.safe_load(jobfile)
    sourcename:str = list(job['source'])[0]
    if sourcename.lower() == 'servicenow':
        modulename = 'opsrampcli.ServiceNowDataSource'
        classname = 'ServiceNowDataSource'
    elif sourcename.lower() == 'urlsource':
        modulename = 'opsrampcli.URLDataSource'
        classname = 'URLDataSource'
    elif sourcename.lower() == 'jsonsource':
        modulename = 'opsrampcli.JSONDataSource'
        classname = 'JSONDataSource'

    sourcemodule = importlib.import_module(modulename)
    sourceclass = getattr(sourcemodule, classname)

    source:DataSource = sourceclass(job)

    logger.info(f'Querying  records from datasource: {classname}')
    df = source.get_data_from_source()
    logger.info(f'Retrieved {len(df.index)} records from datasource: {classname}')

    for index, row in df.iterrows():
        logger.info(ops.post_incident_update(row['x_opra_opsramp_int_opsramp_incident_id'],{"status": "Resolved"}));
    logger.info("Done")
    #return await import_resources_from_dataframe(ops, args, df, job)