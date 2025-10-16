import json
import sys
import re

def do_cmd_get_templates(ops, args):
    templates = ops.get_templates(args.query)
    if args.brief:
        [print(template['name']) for template in templates]
    else:
        print(json.dumps(templates, indent=2, sort_keys=False))
    
def do_cmd_clone_templates(ops, args):
    originals = []
    if args.name:
        originals = [args.name]
    elif args.infile:
        with open(args.infile, 'r') as f:
            for line in f:
                line = re.match('^[^#]*', line)[0]
                line = line.strip()
                if line != '':
                    originals.append(line)
    for original in originals:
        copyname = ""
        if args.copyname:
            copyname = args.copyname
        elif args.prefix:
            copyname = args.prefix + original
        do_cmd_clone_template(ops, original, copyname)

def do_cmd_clone_template(ops, name, copyname):
    matches = ops.get_templates(queryString=f'name:{name}')
    original = False
    for match in matches:
        if match['name'] == name:
            original = match
            break
    if not original:
        print(f'\nMonitoring template named {name} could not be found... skipping.\n')
    else:
        resp = ops.clone_template(original, copyname, original['description'])
        if 'templateId' not in resp:
            print(f'Clone of template {name} failed:\n{json.dumps(resp, indent=2, sort_keys=False)}')
        else:
            print(f'Successfully created new template {copyname} with uniqueId {resp["templateId"]}')


def do_cmd_set_baseline_threshold(ops, args):
    # Get template
    templates = ops.get_templates(queryString=f'scope:Client+name:{args.template}')
    if type(templates) != list:
        print(f'Error in template name - please check it and try again.')
        sys.exit(-1)
    if len(templates) < 1:
        print(f'No template found with this name - please check it and try again.')
        sys.exit(-1)
    if len(templates) > 1:
        print(f'Multiple templates found with this name - please check it and try again.')
        sys.exit(-1)

    template = templates[0]
    template_uniqueId = template['uniqueId']
    template_id = template['id']
    # Look for metric in template and get monitor name
    monitor_name = None
    template_monitor_defn = None
    for monitor in template['monitors']:
        if monitor['metricName'] == args.metric:
            template_monitor_defn = monitor
            monitor_name = monitor['name']
            break

    if monitor_name is None:
        print(f'The metric name specified is not in this tamplete - please check it and try again.')
        sys.exit(-1)
    """      
    print(f'Template Name: {args.template}')
    print(f'Template ID: {template_id}')
    print(f'Monitor Name: {monitor_name}')
    print(f'Monitor Definition:')
    print(json.dumps(template_monitor_defn, indent=2, sort_keys=False))
    """

    # Get baseline metric data from last 24 hrs
    promql_metric_name = args.metric.replace('.', '_')
    metric_query = args.instant_query or f'max_over_time({promql_metric_name}[24h])'
    metrics_result = ops.do_instant_metric_query(metric_query)
    #print(json.dumps(metrics_result[0], indent=2, sort_keys=False))
    #print(len(metrics_result))

    metric_value_lookup = {}
    for metric_result_row in metrics_result:
        resource_id = metric_result_row['metric']['uuid']
        component = metric_result_row['metric']['instance']
        metric_value = metric_result_row['value'][1]
        if resource_id not in metric_value_lookup:
            metric_value_lookup[resource_id] = {}
            metric_value_lookup[resource_id]['name'] = metric_result_row['metric']['name']
        if component not in metric_value_lookup[resource_id]:
            metric_value_lookup[resource_id][component] = metric_value


    # Get resources with this template assigned to it
    resources = ops.get_objects(obtype="resources", queryString=f'template:{template_id}')
    for resource in resources:
        if resource['id'] in metric_value_lookup:
            template_thresholds = [
                {
                    "templateId": template_uniqueId,
                    "monitors": [
                        {
                            "name": monitor_name,
                            "frequency": 5,
                            "thresholdType": "Static",
                            "metricName": args.metric,
                            "thresholds": []
                        }
                    ]
                }
            ]
            for component in metric_value_lookup[resource['id']]:
                if component == 'name':
                    continue
                threshold = {
                                "warningOperator": args.warnop or template_monitor_defn['warningOperator'],
                                "warningThreshold": args.warnthresh if type(args.warnthresh)==float else template_monitor_defn['warningThreshHold'],
                                "warningRepeatCount": args.warnrepeat if type(args.warnrepeat)==int else template_monitor_defn['warningRepeatCount'],
                                "criticalOperator": args.critop or template_monitor_defn['criticalOperator'],
                                "criticalThreshold": args.critthresh if type(args.critthresh)==float else template_monitor_defn['criticalThreshHold'],
                                "criticalRepeatCount": args.critrepeat if type(args.critrepeat)==int else template_monitor_defn['criticalRepeatCount'],
                                "compName": component,
                                "raiseAlert": args.raisealert == 'on',
                                "levelType": "COMPONENT",
                                "availability": args.availability,
                                "operation": "UPDATE"
                }
                template_thresholds[0]['monitors'][0]['thresholds'].append(threshold)
                #print(f'Disable alerting for resource {resource["name"]} component {component}')
            num_components = len(template_thresholds[0]['monitors'][0]['thresholds'])
            if num_components > 0:
                response = ops.do_resource_threshold_assign_multi(resource['id'], template_thresholds)
                print(f'Updated threshold settings for {num_components}  components on resource {resource["name"]}')



    print("Done")


