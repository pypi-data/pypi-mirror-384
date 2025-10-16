import json
import pandas as pd
import re
import xlsxwriter
from opsrampcli.opsrampenv import OpsRampEnv
from opsrampcli.DataSource import DataSource
import sys
import yaml
import logging
import importlib
import asyncio
import copy

logger = logging.getLogger(__name__)

SET_TAG_VALUE_MAX_DEVICES = 100
RESOURCE_FILE_REQUIRED_FIELDS = ['client.uniqueId', 'client.name','resourceName','resourceType']
ALL_RESOURCE_FIELDS = [
    "id",
    "name",
    "type",
    "aliasName",
    "resourceName",
    "hostName",
    "make",
    "model",
    "ipAddress",
    "alternateIpAddress",
    "os",
    "serialNumber",
    "clientId",
    "partnerId",
    "entityType",
    "nativeType",
    "dnsName",
    "moId",
    "internalId",
    "state",
    "macAddress",
    "agentInstalled",
    "monitorable",
    "tags",
    "timezone",
    "osType"
  ]

DEFAULT_RESOURCE_MAPPING_STRATEGY_OLD = {
    'name': 'Default (matching resourceType, resourceName)',
    'opsramp_fields': [
        {'fieldname': 'resourceType'},
        {'fieldname': 'resourceName'}
    ],
    'source_fields': [
        {'fieldname': 'resourceType'},
        {'fieldname': 'resourceName'}
    ]
}
    
DEFAULT_RESOURCE_MAPPING_STRATEGY_NEW = {
    'name': 'Default (matching type, name)',
    'opsramp_fields': [
        {'fieldname': 'type'},
        {'fieldname': 'name'}
    ],
    'source_fields': [
        {'fieldname': 'resourceType'},
        {'fieldname': 'resourceName'}
    ]
}

class MatchedDeleteExceptionSoWeWontDelete(Exception):
    pass

def assign_via_flattened_attribute_name(orig_object:dict, flatattr_name:str, value):
    """Given an existing dict, a flattened "dotted notation" attribute name, and a value,
       this function will update the dict with the new value in the correct location in the
       dict, including creating any missing intermediate keys.

       Args:
           orig_object: The dict to be modified
           flatattr_name: Attribute name in "flattended" dotted notation
           value: The value to be assigned
       
       Returns:
           The original dict, updated with the new value
    
    """
    if not orig_object:
        orig_object = {}

    if flatattr_name.startswith('tags.'):
        tagname = flatattr_name.split('.')[1]
        if 'tags' not in orig_object:
            orig_object['tags'] = []
        tag = {
                "name": tagname,
                "value": value,
                "metricLabel": False,
                "scope": "CLIENT"
        }
        orig_object['tags'].append(tag)
        return orig_object

    if flatattr_name.find('.') < 0:
        orig_object[flatattr_name] = value
        return orig_object
    
    attr_elements = flatattr_name.split('.')
    attrname = attr_elements.pop(0)
    if attrname in orig_object:
        subobject = orig_object[attrname]
    else:
        subobject = None
    orig_object[attrname] =  assign_via_flattened_attribute_name(subobject, ".".join(attr_elements), value)
    return orig_object


def check_if_updates(new, original):
    if type(new) == dict:
        for newkey, newvalue in new.items():
            if newkey == 'tags':
                continue
            if newkey == 'resourceName':
                continue
            if newkey not in original or type(newvalue) != type(original[newkey]):
                return True
            elif type(newvalue) == dict:
                if check_if_updates(newvalue, original[newkey]):
                    return True
            elif newvalue != original[newkey]:
                return True
    return False




def do_cmd_import_resources(ops: OpsRampEnv, args):
    filename = args.filename
    if not re.match(r".*\.xlsx$", filename):
        filename = filename + ".xlsx"
    df =  pd.read_excel(io=filename, engine="openpyxl", dtype=str)
    return import_resources_from_dataframe(ops, args, df)

async def get_match_strategies(job:dict, old_query_type:bool=True):
    match_strategies = []
    if job and 'match_strategy' in job and job['match_strategy']:
        # Match strategy from job file
        match_strategies = job['match_strategy']
    else:
        # Default match strategy
        if old_query_type:
            match_strategies = [DEFAULT_RESOURCE_MAPPING_STRATEGY_OLD]
        else:
            match_strategies = [DEFAULT_RESOURCE_MAPPING_STRATEGY_NEW]
    return match_strategies

async def build_resource_match_lookup(resources:list, match_strategies:list):
    resource_maps = []
    for strategy in match_strategies:
        map_approach:dict = {}
        duplicates:set = set()
        duplicates_of:dict = {}
        for resource in resources:
            try:
                match_string_pieces = []
                for opsramp_field in strategy['opsramp_fields']:
                    fieldval:str = resource[opsramp_field['fieldname']]
                    fieldval = fieldval.lower().strip()
                    if 'normalize' in opsramp_field and 'regex' in opsramp_field['normalize'] and 'replace' in opsramp_field['normalize']:
                        regex = opsramp_field['normalize']['regex']
                        replace = opsramp_field['normalize']['replace']
                        fieldval = re.sub(regex, replace, fieldval)
                        fieldval = fieldval.lower().strip()
                        if not fieldval:
                            logger.warn(f'When building match map of resources with approach "{strategy["name"]}": resource id {resource["id"]}, field {opsramp_field["fieldname"]} is blank so skipping the resource.')
                            raise Exception("Blank field value")
                    match_string_pieces.append(fieldval.lower().strip())
                match_string = "|".join(match_string_pieces)
                if match_string in map_approach:
                    logger.debug(f'When building match map of resources with approach "{strategy["name"]}": resource id {resource["id"]} duplicates already used string "{match_string}" from resource id {map_approach[match_string]}.')
                    if map_approach[match_string] not in duplicates_of:
                        duplicates_of[map_approach[match_string]] = set()
                    duplicates_of[map_approach[match_string]].add(resource["id"])
                    duplicates.add(resource["id"])
                else:
                    map_approach[match_string] = resource['id']
            except:
                pass
        
        map_approach["__duplicates__"] = duplicates
        map_approach["__duplicates_of__"] = duplicates_of
        resource_maps.append(map_approach)
    with open("resource_maps.json", "w") as f:
        json.dump(list(resource_maps), f, default=list, indent=2)
    return resource_maps

def build_source_match_strings(resource, match_strategies:list):
    match_strings = []
    for strategy in match_strategies:
        match_string_pieces = []
        for source_field in strategy['source_fields']:
            fieldval:str = resource[source_field['fieldname']]
            fieldval = fieldval.lower().strip()
            if 'normalize' in source_field and 'regex' in source_field['normalize'] and 'replace' in source_field['normalize']:
                regex = source_field['normalize']['regex']
                replace = source_field['normalize']['replace']
                fieldval = re.sub(regex, replace, fieldval)
                fieldval = fieldval.lower().strip()
            match_string_pieces.append(fieldval.lower().strip())
        match_string = "|".join(match_string_pieces)
        match_strings.append(match_string)
    return match_strings

def find_matching_resource(source_strings:list, resource_map:list, strategies:list, ridx:int):
    matching_resource_id = None
    if not (len(resource_map) == len(source_strings) and len(strategies) == len(source_strings)):
        logger.error(f'Length of source strings ({len(source_strings)}), resource_map ({len(resource_map)}), and strategies ({len(strategies)}) lists are not the same for saome reason - please check your job\' match_strategy section.')
        raise
    for idx,match_string in enumerate(source_strings):
        if match_string in resource_map[idx]:
            matching_resource_id = resource_map[idx][match_string]
            logger.debug(f'Source record #{ridx+1}: found matching resource id {matching_resource_id} for match string "{match_string}" using strategy #{idx+1}: {strategies[idx]["name"]}')
            break
    return matching_resource_id


async def send_missing_resource_alert(ops, args, resource):
    alert = {}
    alert['serviceName'] = "opcli_opsramp_missing_resource"
    alert['device'] = {'hostName': resource['resourceName'].lower()}
    alert['subject'] = f'Missing resource "{resource["resourceName"].lower()}" of type "{resource["resourceType"]}" detected by CMDB integration'
    alert['currentState'] = args.alertonmissing
    alert['component'] = resource["resourceType"]
    alert['description'] = f'The resource "{resource["resourceName"].lower()}" of type "{resource["resourceType"]}" exists in the CMDB but is not in OpsRamp.\nThe --nocreate option is set to {args.nocreate} and the --native_attrs_update option is set to {args.native_attrs_update}.'
    await ops.post_alert_bearer_async(alert)


def build_resource_payload(resource:pd.Series, spec:dict):
    # Build the resource create/update payload
    resource_dict = {}
    for attrname in spec['native_attrs']:
        resource_dict = assign_via_flattened_attribute_name(resource_dict, attrname, resource[attrname])
    return resource_dict


async def update_existing_resource_native_attrs(ops:OpsRampEnv, resourceId, resource:pd.Series, job:dict, existing_resources_by_id:dict, resource_map):
    spec:dict = job['update_existing_resources']
    existing_resource:dict = existing_resources_by_id[resourceId]
    payload:dict = build_resource_payload(resource, spec)
    has_updated_values = check_if_updates(payload, existing_resource)
    if has_updated_values:
        response = ops.update_resource(resourceId, payload)
        if 'success' in response and response['success']:
            logger.info(f'Updated resource main attributes for name:{payload["resourceName"]} with id:{resourceId}')
        else:
            logger.error(f'Unable to update resource {payload["resourceName"]} - {response["message"]}.  Please check the data for this item.')
            return
    else:
        logger.debug(f'No updates to resource main attributes name:{payload["resourceName"]} with id:{resourceId}')

    #
    # The below complicates things because setting alias the same on dups would be bad, so let's skip it
    #

    # dups:set = await get_all_dups_of_resource(ops, resourceId, job['match_strategy'], resource_map)
    # for dup in dups:
    #     logger.info(f'Setting same per-resource native attributes on dup resource id {dup}')
    #     await update_existing_resource_native_attrs(ops, dup, resource, job, existing_resources_by_id, resource_map)

def create_missing_resource_native_attrs(ops:OpsRampEnv, resource:pd.Series, spec:dict):
    payload:dict = build_resource_payload(resource, spec)
    response = ops.create_resource(payload)
    if 'resourceUUID' in response:
        resourceId = response['resourceUUID']
        logger.info(f'Created resource name:{payload["resourceName"]} with id:{resourceId}')
        return resourceId
    else:
        logger.error(f'Unable to create resource {payload["resourceName"]}.  Please check the data for this item.')
        return None
    
async def bulk_update_static_attributes(ops, job, df:pd.DataFrame, resource_map, existing_resources_by_id, attrinfo):
    match_strategies = job['match_strategy']
    for static_attr_name, static_attr_val in job[DataSource.FIELD_STATIC_VALUE].items():
        if static_attr_name.startswith("tags."):
            cleaned_static_attr_name = static_attr_name.replace("tags.","")
            resource_ids = []
            for idx,resource in df.iterrows():
                source_match_strings = build_source_match_strings(resource, match_strategies)
                resource_id = find_matching_resource(source_match_strings, resource_map, match_strategies, idx)
                if resource_id:
                    if "tags" in existing_resources_by_id[resource_id] and any(attr['name']==cleaned_static_attr_name and attr['value']==df[static_attr_name][0] for attr in existing_resources_by_id[resource_id]['tags']):
                        pass
                    else:
                        resource_ids.append(resource_id)
                dups:set = await get_all_dups_of_resource(ops, resource_id, job['match_strategy'], resource_map)
                for dup in dups:
                    if "tags" in existing_resources_by_id[dup] and any(attr['name']==cleaned_static_attr_name and attr['value']==df[static_attr_name][0] for attr in existing_resources_by_id[dup]['tags']):
                        pass
                    else:
                        resource_ids.append(dup)                 
            number_set = 0
            number_unset = 0
            unset_coroutines = []
            set_coroutines = []
            for i in range(0, len(resource_ids), SET_TAG_VALUE_MAX_DEVICES):
                batch = resource_ids[i:i + SET_TAG_VALUE_MAX_DEVICES]
                unset_coroutines.append(ops.unset_custom_attr_on_devices_async(attrinfo[cleaned_static_attr_name]['id'], batch))
                number_unset += len(batch)
            await asyncio.gather(*unset_coroutines)
            logger.info(f'Bulk unset static attribute "{cleaned_static_attr_name}" for {number_unset} resources.')

            for i in range(0, len(resource_ids), SET_TAG_VALUE_MAX_DEVICES):
                batch = resource_ids[i:i + SET_TAG_VALUE_MAX_DEVICES]
                set_coroutines.append(ops.set_custom_attr_on_devices_async(attrinfo[cleaned_static_attr_name]['id'], attrinfo[cleaned_static_attr_name]['values'][str(df[static_attr_name][0])], batch, False))
                number_set += len(batch)
            await asyncio.gather(*set_coroutines)
            logger.info(f'Bulk set static attribute "{cleaned_static_attr_name}" to value "{str(df[static_attr_name][0])}" for {number_set} resources.')

            df = df.drop(columns=[static_attr_name])


async def get_all_dups_of_resource(ops:OpsRampEnv, resource_id, match_strategies, resource_map):
    dups = set()
    for sidx, strategy in enumerate(match_strategies):
        if 'duplicate_handling' in strategy and strategy['duplicate_handling'] == 'update_all' and '__duplicates_of__' in resource_map[sidx] and resource_id in resource_map[sidx]['__duplicates_of__']:
            dups = dups.union(resource_map[sidx]['__duplicates_of__'][resource_id])
    return dups

async def set_non_static_attributes_on_resource(ops:OpsRampEnv, args, job:dict, non_static_attr_names_in_file, is_new, resourceId, resource:pd.Series, existing_resources_by_id, resource_map, attrinfo):
    for attrname in non_static_attr_names_in_file:
        columnhead = f'tags.{attrname}'
        column = attrname
        if pd.isnull(resource[columnhead]) or pd.isna(resource[columnhead]) or resource[columnhead]=='' :
            if args.writeblanks:
                if is_new:
                    continue
                if "tags" in existing_resources_by_id[resourceId] and any(attr['name']==column for attr in existing_resources_by_id[resourceId]['tags']):
                    # There are one or more values and we need to remove it/them
                    remove_values = [obj['value'] for obj in existing_resources_by_id[resourceId]['tags'] if obj['name'] == column]
                    for remove_value in remove_values:
                        await ops.unset_custom_attr_on_devices_async(attrinfo[attrname]['id'], resourceId)


            else:
                continue
        elif not is_new and "tags" in existing_resources_by_id[resourceId] and any(attr['name']==column and attr['value']==resource[columnhead] for attr in existing_resources_by_id[resourceId]['tags']):
            # It already has the same value for this attr, no need to update
            continue
        else:
            # It has no value or a different value for this attr so we need to update

            # If it has a different value we need to remove it first
            if not is_new and "tags" in existing_resources_by_id[resourceId] and any(attr['name']==column for attr in existing_resources_by_id[resourceId]['tags']):
                await ops.unset_custom_attr_on_devices_async(attrinfo[attrname]['id'], resourceId)

            logger.info(f'Setting tag {attrname} = {resource[columnhead]} on resource "{resource["resourceName"]}"')
            result = await ops.set_custom_attr_on_devices_async(attrinfo[attrname]['id'], attrinfo[attrname]['values'][str(resource[columnhead])], resourceId)
    dups:set = await get_all_dups_of_resource(ops, resourceId, job['match_strategy'], resource_map)
    for dup in dups:
        logger.info(f'Setting same per-resource tags on dup resource id {dup} as {resourceId}')
        await set_non_static_attributes_on_resource(ops, args, job, non_static_attr_names_in_file, False, dup, resource, existing_resources_by_id, resource_map, attrinfo)

async def process_resource_data(ops:OpsRampEnv, args, job:dict, df:pd.DataFrame, idx, resource:pd.Series, resource_map, match_strategies, non_static_attr_names_in_file, existing_resources_by_id, attrinfo, matched_resource_ids:set):
        # See if it is a new resource or already existing
        source_match_strings = build_source_match_strings(resource, match_strategies)
        resourceId = find_matching_resource(source_match_strings, resource_map, match_strategies, idx)

        if resourceId: # Existing resource
            is_new = False
            matched_resource_ids.add(resourceId)
            logger.debug(f'Source record #{idx+1} {resource["resourceName"]} matches existing resource with id {resourceId} in OpsRamp')

            # Handle delete if specified
            if 'Processing Action' in resource and resource['Processing Action'] == 'Delete':
                response = ops.delete_resource(resourceId)
                logger.info(f'Deleted resource name:{resource["resourceName"]} with id:{resourceId} as its Processing Action was set to Delete')
                return
            
            # Handle native attrs update if specified
            if 'update_existing_resources' in job and job['update_existing_resources']:
                await update_existing_resource_native_attrs(ops, resourceId, resource, job, existing_resources_by_id, resource_map)


        else: # New resource
            is_new = True
            logger.info(f'Source record #{idx+1}: {resource["resourceName"]} does not match any exiting resource in OpsRamp')

            if 'Processing Action' in resource and resource['Processing Action'] == 'Delete':
                    logger.warn(f'Delete action specified but there is no such resource name:{resource["resourceName"]} of specified type.')
                    return
            
            if args.alertonmisssing:
                logger.info(f"Sending a missing resource alert for source record #{idx+1}")
                send_missing_resource_alert(ops, args, resource)

            if 'create_missing_resources' in job and job['create_missing_resources']:
                resourceId = create_missing_resource_native_attrs(ops, resource, job['create_missing_resources'])
                if not resourceId:
                    return
                matched_resource_ids.add(resourceId)
            else:
                return

        logger.debug(f'Processing resource-specific tags')
        await set_non_static_attributes_on_resource(ops, args, job, non_static_attr_names_in_file, is_new, resourceId, resource, existing_resources_by_id, resource_map, attrinfo)
          
async def import_resources_from_dataframe(ops:OpsRampEnv, args, df:pd.DataFrame, job:dict=None):
    logger.info(f'Getting custom attribute definitions from OpsRamp')
    customattrs = ops.get_objects(obtype="customAttributes")
    if 'code' in customattrs:
        logger.error("Error encountered retrieving custom attributes: %s" % customattrs)
        raise    

    attrinfo = {}
    for attr in customattrs:
        attrname = attr['name']
        attrinfo[attrname] = {}
        attrinfo[attrname]['id'] = attr['id']
        attrinfo[attrname]['values'] = {}

    errors = []
    logger.info('Checking source data for errors')
    for required_col in RESOURCE_FILE_REQUIRED_FIELDS:
        if required_col not in set(df.columns):
            errors.append('Required column "' + required_col + '" is missing from the spreadsheet.')
            continue
        if (len(df[df[required_col] == '']) > 0) or (len(df[pd.isna(df[required_col])]) > 0):
            errors.append('Column "' + required_col + '" has blank values which is not permitted.')
        if required_col=='name' and df['name'].duplicated().any():
            errors.append('Column "name" has duplicate values which is not permitted.')

    logger.info(f'Getting existing devices/resources from OpsRamp')
    if 'resource_opsql' in job and job['resource_opsql']:
        old_query_type = False
        opsql = job['resource_opsql']
        if 'filter' not in opsql:
            opsql['filter'] = ''
        if 'fields' not in opsql or not opsql['fields']:
            opsql['fields'] = ['id', 'name', 'resourceName', 'type', 'tags', 'os', 'ipAddress', 'serialNumber' ]
        if 'pageSize' not in opsql:
            opsql['pageSize'] = 1000
        if 'sortBy' not in opsql:
            opsql['sortBy'] = "name"

        logger.info(f'Using opsql resource search, opsql filter is \'{opsql["filter"]}\'')
        resources = await ops.do_opsql_query_async('resource',opsql['fields'], opsql['filter'],page_size=opsql['pageSize'], sort_by=opsql['sortBy'])
    else:
        old_query_type = True
        queryString = None
        if 'resourceType' in df:
            if len(df['resourceType'].unique()) == 1:
                rtype = df['resourceType'].unique()[0]
                queryString = f'resourceType:{rtype}'
            logger.warn(f'Using DEPRECATED old device query API, queryString is "{queryString}"')
        resources = await ops.get_objects_async(obtype="resources", queryString=queryString, countonly=False)
        if 'code' in resources:
            logger.error("Error encountered retrieving resources: %s" % resources)
            raise    
    logger.info(f'Retrieved {len(resources)} resources from OpsRamp')
    existing_resources_by_id = {}
    matched_resource_ids = set()

#    with open("/tmp/existingbefore.json", "w") as f3:
#        json.dump(resources, f3, indent=2)

    with open("existing.txt", "w") as f:
        for idx, resource in enumerate(resources):
            if 'resourceName' not in resource:
                resource['resourceName'] = resource['name']
            if 'resourceType' not in resource:
                resource['resourceType'] = resource['type']
            if 'name' not in resource:
                resource['name'] = resource['resourceName']
            if 'type' not in resource:
                resource['type'] = resource['resourceType']         
            existing_resources_by_id[resource['id']] = resource
            f.write(f'{idx}\t{resource["id"]}\t{resource["name"]}\n')

#    with open("/tmp/existingafter.json", "w") as f4:
#        json.dump(resources, f4, indent=2)

    match_strategies = await get_match_strategies(job, old_query_type)
    assert isinstance(resources, list)
    resource_map:list = await build_resource_match_lookup(resources, match_strategies)

    logger.info('Getting existing tag value definitions and determining any new value definitions needing to be added')
    tag_names_to_add = []
    vals_to_add = {}
    non_static_attr_names_in_file = []
    for columnhead in df.columns:
        df[columnhead] = df[columnhead].str.strip()
        if columnhead.startswith('tags.'):
            column = columnhead.split('.')[1]
            if columnhead not in job[DataSource.FIELD_STATIC_VALUE]:
                non_static_attr_names_in_file.append(column)
        else:
            continue

        if column in attrinfo:
            attrvalues = ops.get_tag_values(attrinfo[column]['id'])
            for value in attrvalues:
                attrinfo[column]['values'][value['value']] = value['uniqueId']
            attrvalues_values = [obj['value'] for obj in attrvalues]
        else:
            attrvalues_values = []
            if args.addnames:
                tag_names_to_add.append(column)
            else:
                errors.append(f'Column header tags.{column} indicates a non-existent custom attribute name of {column} for the specified client.  Please create this custom attribute name in the OpsRamp UI first, or set the --addnames option to auto-add it.' )

        for val in df[columnhead].unique():
            if pd.notna(val) and val != "" and str(val) not in attrvalues_values:
                if args.addvalues:
                    strval = str(val)
                    if column not in vals_to_add:
                        vals_to_add[column] = []
                    vals_to_add[column].append(strval)
                else:
                    errors.append('Value "' + str(val) + '" specified for custom attribute "' + column + '" is not a valid value.')

    if len(errors) > 0:
        logger.error("Errors exist in the spreadsheet.  No updates to the platform have been made, please correct these errors before commiting:\n")
        for i,error in enumerate(errors):
            logger.error("%s  %s" % (str(i+1).rjust(5),error))
        #logger.error("If you want to auto-add new custom attr value definitions on the fly, use the --addvalues option otherwise undefined values will be treated as an error.\n")
        sys.exit(1)

    elif not args.commit:
        logger.info("No errors were found in the spreadsheet.  To apply the changes to the platform, rerun the command with the --commit option added.")
        sys.exit(0)

    logger.info('Preflight checks completed')

    logger.info(f'Adding {len(tag_names_to_add)} missing tag / custom attribute name definitions')
    for tag_name in tag_names_to_add:
        new_tag_id = ops.create_tag(tag_name)
        attrinfo[tag_name] = {}
        attrinfo[tag_name]['id'] = new_tag_id
        attrinfo[tag_name]['values'] = {}    
    
    logger.info('Adding missing tag / custom attribute value definitions')
    for column in vals_to_add.keys():
        newvalsarray = []
        for val in vals_to_add[column]:
            newvalsarray.append(val)
        ismetriclabel = False
        if job and 'tag_as_metric_label' in job and column in job['tag_as_metric_label'] and job['tag_as_metric_label'][column]:
            ismetriclabel = True
        newvals = ops.add_custom_attr_value(attrinfo[column]['id'], newvalsarray, is_metric_label=ismetriclabel)
        for value in newvals:
            attrinfo[column]['values'][value['value']] = value['id']

    # Use bulk calls for static custom attribute values
    if job and DataSource.FIELD_STATIC_VALUE in job and isinstance(job[DataSource.FIELD_STATIC_VALUE], dict):
        logger.info('Consolidating static custom attribute updates to speed things up!')
        await bulk_update_static_attributes(ops, job, df, resource_map, existing_resources_by_id, attrinfo)      
        logger.info(f'Finished consolidated bulk update of static custom attribute values!')

    # Iterate through source records for processing
    logger.info('Processing per-resource values')
    numsourcerecs = len(df)
    for idx,resource in df.iterrows():
        logger.debug(f'Processing per-resource values for source record #{idx+1} of {numsourcerecs} named {resource["resourceName"]} of type {resource["resourceType"]}')
        await process_resource_data(ops, args, job, df, idx, resource, resource_map, match_strategies, non_static_attr_names_in_file, existing_resources_by_id, attrinfo, matched_resource_ids)

    # Delete dups if configured and they exist
    # TODO - Fix this section to use duplicate_handling instead of delete_duplicates 
    dups_to_delete = set()
    for sidx, strategy in enumerate(match_strategies):
        if 'duplicate_handling' in strategy and strategy['duplicate_handling'] == 'delete_duplicates' and '__duplicates__' in resource_map[sidx] and resource_map[sidx]['__duplicates__']:
            dups_to_delete = dups_to_delete.union(resource_map[sidx]['__duplicates__'])
    if dups_to_delete:
        numdups = len(dups_to_delete)
        logger.info(f'There are {numdups} duplicate resources that will be deleted from OpsRamp')
        for didx, did in enumerate(dups_to_delete):
            logger.info(f'Deleting duplicate resource #{didx+1} of {numdups} - {existing_resources_by_id[did]["name"]}')
            ops.delete_resource(did)

    # Delete unmatched resources if configured
    if 'delete_existing_resources_if_not_in_source' in job:
        logger.info('Deleting existing resources that  don\'t appear in the data source...')
        deleted_count = 0
        delete_spec:dict = job['delete_existing_resources_if_not_in_source']
        for idx, resource in enumerate(resources):
            try:
                resource_id = resource['id']
                if resource_id not in matched_resource_ids:
                    if type(delete_spec) == dict:
                        if 'except_for_matching' in delete_spec:
                            exceptions:dict = delete_spec['except_for_matching']
                            for fieldname, values in exceptions.items():
                                for value in values:
                                    if resource[fieldname] != None and value != None and value.lower() == resource[fieldname].lower():
                                        raise MatchedDeleteExceptionSoWeWontDelete()
                    logger.info(f'Deleting existing OpsRamp resource id {resource_id} - {resource["name"]} since it is not in the source data.')
                    ops.delete_resource(resource_id)
                    deleted_count += 1
                                    
            except MatchedDeleteExceptionSoWeWontDelete:
                logger.info(f'NOT deleting existing OpsRamp resource id {resource_id} - {resource["name"]} even though it is not in the source data since it has {fieldname}="{value}".')
            except Exception as e:
                logger.error(f'Unexpected exception encountered when checking deletion elegibility for resource {resource_id}: {e}')
        logger.info(f'Deleted {deleted_count} resources that were not in the source data.')

    # All done
    logger.info("Completed processing all resources.") 

def do_cmd_get_resources(ops,args):
    if args.search:
        if args.count:
            aggregate="count"
            groupBy = []
            fields = None
        else:
            aggregate=None
            groupBy=None
            fields = ALL_RESOURCE_FIELDS

        result = ops.do_opsql_query("resource", fields, args.search, aggregate, groupBy)
        if args.count:
            result = result[0]["count"]
    else:
        result = ops.get_objects(obtype="resources", queryString=args.query, countonly=args.count)

    if args.delete:
        confirm_delete = 'NO'
        confirm_delete = input(f'This will result in the deletion of {len(result)} resources.  Enter YES (upper case) to confirm deletion or enter anything else to just print a list of the resources that would be deleted: ')
    
        if confirm_delete == 'YES':
            for (idx, resource) in enumerate(result):
                if "resourceType" not in resource:
                    if "type" in resource:
                        resource["resourceType"] = resource["type"]
                    else:
                        resource["resourceType"] = "NONE"
                logger.info(f'Deleting resource #{idx+1} - {resource["name"]} ({resource["resourceType"]}) with uniqueId {resource["id"]}')
                try:
                    logger.info(ops.delete_resource(resource['id']))
                except Exception as e:
                    logger.error(f'Error ocurred deleting ressource with id {resource["id"]}', exc_info=e)
        else:
            return result

    elif args.manage:
        confirm_manage = 'NO'
        confirm_manage = input(f'This will result in managing {len(result)} resources.  Enter YES (upper case) to confirm or enter anything else to just print a list of the resources that would be managed: ')
    
        if confirm_manage == 'YES':
            for (idx, resource) in enumerate(result):
                logger.info(f'Managing resource #{idx+1} - {resource["name"]}')
                try:
                    logger.info(ops.do_resource_action("manage", resource['id']))
                except Exception as e:
                    logger.error(f'Exception occurred attempting to manage resource {resource["name"]} with id {resource["id"]}', exc_info=e)

        else:
            return result      


    else:
         return result

async def do_cmd_importfromdatasource(ops, args):

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

    logger.info(f'Querying resources from datasource: {classname}')
    df = source.get_data_from_source()
    logger.info(f'Retrieved {len(df.index)} resources from datasource: {classname}')
    return await import_resources_from_dataframe(ops, args, df, job)