import json
from  opsrampenv import OpsRampEnv
import monitoring
import yaml

def get_env_from_file(envname="", envfile=""):
    #print(f'Env is {envname} envfile is {envfile}')
    envstream = open(envfile, 'r')
    envs = yaml.safe_load(envstream)
    #print("Looking for environment named \"%s\" in %s." % (envname, envfile))
    filtered_envs = filter(lambda x: (x["name"] == envname), envs)
    env = next(filtered_envs)
    return env

ops = OpsRampEnv(get_env_from_file('tf-cis', 'environments.yml'))


templates = None
with open('/tmp/tf-overrides/templates.json') as tfile:
    templates = json.load(tfile)

for tidx,template in enumerate(templates):
    newtemp = {
        "monitors": []
    }
    path = f'/monitoring/api/v3/tenants/{ops.env["tenant"]}/templates/{template["uniqueId"]}'
    for midx, monitor in enumerate(template['monitors']):
        if 'metricName' in monitor and monitor['metricName'] == 'system.disk.usage.utilization':
            newmon = {
                "name": monitor["name"],
                "frequency": monitor["frequency"],
                "thresholdType": "Static",
                "metricName": monitor['metricName'],
                "operation": "UPDATE",
                "thresholds": [
                    {
                    "criticalThreshold": 500,
                    "warningThreshold": 500,
                    "criticalRepeatCount": 100,
                    "warningRepeatCount": 100,
                    "criticalOperator": "GREATER_THAN",
                    "warningOperator": "NONE",
                    "raiseAlert": True,
                    "availability": False,
                    "levelType": "TEMPLATE"
                    }
                ]
            }
            newtemp['monitors'].append(newmon)

        elif 'metricName' in monitor and monitor['metricName'] == "system.disk.usage.freespace":
            newmon = {
                "name": monitor["name"],
                "frequency": monitor["frequency"],
                "thresholdType": "Static",
                "metricName": monitor['metricName'],
                "operation": "UPDATE",
                "thresholds": [
                    {
                    "criticalThreshold": 0,
                    "warningThreshold": 0,
                    "criticalRepeatCount": 100,
                    "warningRepeatCount": 100,
                    "criticalOperator": "LESS_THAN",
                    "warningOperator": "NONE",
                    "raiseAlert": True,
                    "availability": False,
                    "levelType": "TEMPLATE"
                    }
                ]
            }
            newtemp['monitors'].append(newmon)   

    if newtemp['monitors']:
        result = ops.put_object(path, newtemp)
        print(f'Processed template {template["name"]}')
    else:
        print(f'Skipped template {template["name"]}') 


print("DONE")


