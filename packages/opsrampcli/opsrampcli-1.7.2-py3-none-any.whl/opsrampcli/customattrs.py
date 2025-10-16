import json
import csv
import pandas as pd
import numpy as np
import xlsxwriter
import time
import re
import sys
from opsrampcli.opsrampenv import OpsRampEnv
import logging

logger = logging.getLogger(__name__)

CUSTOM_ATTR_FILE_DEFAULT_RESOURCE_FIELDS = ['client.uniqueId', 'client.name','id','name','resourceType']

def do_cmd_customattrmetriclabel(ops:OpsRampEnv, args):
    ismetriclabel = False
    if args.ismetriclabel == "YES":
        ismetriclabel = True

    logger.info(f'Setting custom attribute "{args.attrname}" isMetricLabel to {ismetriclabel} for all values.')
    logger.info("Checking to see if a custom attribute with this name exists...")
    tags = ops.get_tags(f'name = "{args.attrname}"')
    if tags:
        tagid = tags[0]['id']
        logger.info(f'Custom attr name is valid, id is {tagid}')
    else:
        logger.error('There is no such custom attribute name for this tenant.  Please make sure the spelling and case is exactly correct and it is at the same level (partner or client) as the credential you are using.')
        sys.exit(1)

    values = ops.get_tag_values(tagid)
    if values:
        logger.info(f'Found {len(values)} values for this custom attribute, will change them all to isMetricLabel={ismetriclabel}')
    else:
        logger.warn('No values found for this custom attribute, no action has been taken.')
        sys.exit(0)

    set = 0
    skipped = 0
    for value in values:
        if value['metricLabel'] == ismetriclabel:
            logger.debug(f'Skipping value "{value["value"]}" with uniqueId {value["uniqueId"]} because isMetricLabel is already {ismetriclabel}')
            skipped += 1
        else:
            logger.debug(f'Setting isMatricLabel for value "{value["value"]}" with uniqueId {value["uniqueId"]} to {ismetriclabel}')
            ops.update_tag_value(tagid, value['uniqueId'], "", ismetriclabel)
            set += 1

    logger.info(f'Completed ensuring isMetricLabel setting to {ismetriclabel} for all {len(values)} values of this custom attribute.  {set} values were updated and {skipped} values did not need updating so were skipped.')

def do_cmd_get_custom_attributes(ops,args):
    result = ops.get_objects(obtype="customAttributes")
    return result

def do_cmd_make_custom_attr_file(ops, args):
    customattrs = ops.get_objects(obtype="customAttributes")

    if 'code' in customattrs:
        print("Error encountered retrieving custom attributes: %s" % customattrs)
        raise
    
    if args.attrs:
        includeattrs = args.attrs.split(',')
        customattrs = [ca for ca in customattrs if ca['name'] in includeattrs]
    else:
        customattrs = []


    resources = None
    if args.search:
        resources = ops.get_objects(obtype="resourcesNewSearch", searchQuery=args.search, countonly=False)
    else:
        resources = ops.get_objects(obtype="resources", queryString=args.query, countonly=False)

    included_resource_fields = CUSTOM_ATTR_FILE_DEFAULT_RESOURCE_FIELDS
    if args.props:
        included_resource_fields.append(args.props.split(","))
    resourcedf = pd.json_normalize(resources)[included_resource_fields]
    for attr in customattrs:
        resourcedf[attr['name']] = ''
        assigned_entities = ops.get_objects(obtype="assignedAttributeEntities", itemId=attr['id'])
        for ent in assigned_entities:
            if 'taggable' not in ent:
                continue
            resourcedf.loc[resourcedf['id'] == ent['taggable']['id'], attr['name']] = ent['customAttributeValue']['value']

    filename = args.filename
    if not filename:
        filename = 'customattrfile_' + args.env + '_' + time.strftime("%Y-%m-%d_%H%M%S")

    if not re.match(r".*\.xlsx$", filename):
        filename = filename + ".xlsx"

    print("Creating export file: %s" % (filename))

    writer = pd.ExcelWriter(filename, engine="xlsxwriter")
    resourcedf.to_excel(writer, index=False, sheet_name='Custom Attrs')
    workbook  = writer.book
    worksheet = writer.sheets['Custom Attrs']
    for i, col in enumerate(resourcedf.columns):
        column_len = max(resourcedf[col].astype(str).str.len().max(), len(col) + 2)
        worksheet.set_column(i, i, column_len)

    bold = workbook.add_format({'bold': True})
    valsheet = workbook.add_worksheet('values')
    for i, attr in enumerate(customattrs):
        maxwidth = len(attr['name'])
        valsheet.write(0,i,attr['name'], bold)
        for j, attrval in enumerate(attr['customAttributeValues']):
            valsheet.write(j+1,i,attrval['value'])
            maxwidth = max(maxwidth, len(attrval['value']))
        valsheet.set_column(i, i, maxwidth+2)



    writer.save()

    print("done")

def do_cmd_import_custom_attr_file(ops, args):
    filename = args.filename
    if not re.match(r'.*\.xlsx$', filename):
        filename = filename + ".xlsx"

    df =  pd.read_excel(io=filename, engine="openpyxl", dtype=str)

    customattrs = ops.get_objects(obtype="customAttributes")
    if 'code' in customattrs:
        print("Error encountered retrieving custom attributes: %s" % customattrs)
        raise    

    attrinfo = {}
    for attr in customattrs:
        attrname = attr['name']
        attrinfo[attrname] = {}
        attrinfo[attrname]['id'] = attr['id']
        attrinfo[attrname]['client_id'] = attr['organization']['uniqueId']
        attrinfo[attrname]['values'] = {}
        for value in attr['customAttributeValues']:
            attrinfo[attrname]['values'][value['value']] = value['id']

    resourcedict = {}
    resources = ops.get_objects(obtype="resources")
    for resource in resources:
        resourcedict[resource['id']] = resource


    errors = []
    vals_to_add = {}
    for required_col in CUSTOM_ATTR_FILE_DEFAULT_RESOURCE_FIELDS:
        if required_col not in set(df.columns):
            errors.append('Required column "' + required_col + '" is missing from the spreadsheet.')
            continue
        if (len(df[df[required_col] == '']) > 0) or (len(df[pd.isna(df[required_col])]) > 0):
            errors.append('Column "' + required_col + '" has blank values which is not permitted.')
        if required_col=='id' and df['id'].duplicated().any():
            errors.append('Column "id" has duplicate values which is not permitted.')

    if 'id' in set(df.columns):
        for idx,row in df.iterrows():
            if pd.isna(row['id']) or row['id'] == '' or pd.isnull(row['id']):
                pass
            elif row['id'] not in resourcedict:
                errors.append('Resource id "' + row['id'] + '" specified in spreadsheet does not exist for the specified client.')
            else:
                if row['name'] != resourcedict[row['id']]['name']:
                    errors.append('Resource "' + row['id'] + '" name "' + row['name'] + '" in spreadsheet is different from name "' + resourcedict[row['id']]['name'] + '" on platform.')
                if row['resourceType'] != resourcedict[row['id']]['resourceType']:
                    errors.append('Resource "' + row['id'] + '" resourceType "' + row['resourceType'] + '" in spreadsheet is different from resourceType "' + resourcedict[row['id']]['resourceType'] + '" on platform.')
                if row['client.uniqueId'] != resourcedict[row['id']]['client']['uniqueId']:
                    errors.append('Resource "' + row['id'] + '" client.uniqueId "' + row['client.uniqueId'] + '" in spreadsheet is different from client.uniqueId "' + resourcedict[row['id']]['client']['uniqueId'] + '" on platform.')
                if row['client.name'] != resourcedict[row['id']]['client']['name']:
                    errors.append('Resource "' + row['id'] + '" client.name "' + row['client.name'] + '" in spreadsheet is different from client.name "' + resourcedict[row['id']]['client']['name'] + '" on platform.')

    for column in df.columns:
        if column in set(CUSTOM_ATTR_FILE_DEFAULT_RESOURCE_FIELDS):
            continue
        if column not in attrinfo:
            errors.append('Column header "' + column + '" is not a valid custom attribute name for specified client.' )
        else:
            for val in df[column].unique():
                if pd.notna(val) and val != "" and str(val) not in attrinfo[column]['values']:
                    if args.addvalues:
                        strval = str(val)
                        if column not in vals_to_add:
                            vals_to_add[column] = []
                        vals_to_add[column].append(strval)
                    else:
                        errors.append('Value "' + str(val) + '" specified for custom attribute "' + column + '" is not a valid value.')
    if len(errors) > 0:
        print("\nErrors exist in the spreadsheet.  No updates to the platform have been made, please correct these errors before commiting:\n")
        for i,error in enumerate(errors):
            print("%s  %s" % (str(i+1).rjust(5),error))
        print("\nIf you want to auto-add new value definitions on the fly, use the --addvalues option otherwise undefined values will be treated as an error.\n")
        sys.exit(1)

    elif not args.commit:
        print("No errors were found in the spreadsheet.  To apply the changes to the platform, rerun the command with the --commit option added.")
        sys.exit(0)

    updateresults = {
        "updatesuccess": 0,
        "updatefail": 0,
        "updatenotneeded": 0,
        "clearskipped": 0,
        "clearsuccess": 0,
        "clearfail": 0,
        "rawresults": [],
        "errors": []
    }

    for column in vals_to_add:
        newvalsarray = []
        for val in vals_to_add[column]:
            newvalsarray.append(val)
        newvals = ops.add_custom_attr_value(attrinfo[column]['id'], newvalsarray)
        for i,valobj in enumerate(newvals['customAttributeValues']):
            attrinfo[column]['values'][valobj['value']] = valobj['id']
    for idx,resource in df.iterrows():
        for column in df.columns:
            if column in set(CUSTOM_ATTR_FILE_DEFAULT_RESOURCE_FIELDS):
                continue
            elif pd.isnull(resource[column]) or pd.isna(resource[column]) or resource[column]=='' :
                if args.writeblanks:
                    if "tags" in resourcedict[resource['id']] and any(attr['name']==column for attr in resourcedict[resource['id']]['tags']):
                        # There are one or more values and we need to remove it/them
                        remove_values = [obj['value'] for obj in resourcedict[resource['id']]['tags'] if obj['name'] == column]
                        for remove_value in remove_values:
                            ops.unset_custom_attr_on_devices(attrinfo[column]['id'], attrinfo[column]['values'][remove_value], resource['id'])
                        updateresults['clearsuccess'] +=1
                    else:
                        # There is already no value so nothing to remove
                        updateresults['clearskipped'] +=1
                else:
                    updateresults['clearskipped'] +=1
                    continue
            elif "tags" in resourcedict[resource['id']] and any(attr['name']==column and attr['value']==resource[column] for attr in resourcedict[resource['id']]['tags']):
                # It already has the same value for this attr, no need to update
                updateresults['rawresults'].append({
                    "rownum": idx+1,
                    "resourceid": resource['id'],
                    "attr_name": column,
                    "attr_value": resource[column],
                    "attr_id": attrinfo[column]['id'],
                    "attr_value_id": attrinfo[column]['values'][resource[column]],
                    "action": "update not needed"
                })
                updateresults['updatenotneeded'] +=1
                continue
            else:
                # It has no value or a different value for this attr so we need to update
                result = ops.set_custom_attr_on_devices(attrinfo[column]['id'], attrinfo[column]['values'][str(resource[column])], resource['id'])
                updateresults['rawresults'].append({
                    "rownum": idx+1,
                    "resourceid": resource['id'],
                    "attr_name": column,
                    "attr_value": resource[column],
                    "attr_id": attrinfo[column]['id'],
                    "attr_value_id": attrinfo[column]['values'][str(resource[column])],
                    "action": "updated"
                })
                if result['successCount'] == 1:
                    updateresults['updatesuccess'] +=1
                else:
                    updateresults['updatefail'] +=1
                    updateresults['errors'].append({
                        "rownum": idx+1,
                        "resourceid": resource['id'],
                        "attr_name": column,
                        "attr_value": resource[column],
                        "attr_id": attrinfo[column]['id'],
                        "attr_value_id": attrinfo[column]['values'][str(resource[column])],
                        "action": "updatefail",
                        "response": result
                    })                    
    
    
    print("done")

def do_cmd_add_prop_as_metric_label(ops, args):

    # Retrieve the existing custattr info and values and create a dict of values to value ids
    print('Getting custom attribute definitions for client...')
    customattrs = ops.get_objects(obtype="customAttributes")

    if 'code' in customattrs:
        print("Error encountered retrieving custom attributes: %s" % customattrs)
        raise

    attrinfo = {}
    attrinfo_arr = [ attr for attr in customattrs if attr['name'] == args.custattrname ]

    if len(attrinfo_arr) > 0:
        attrinfo = attrinfo_arr[0]
    else:
        print(f'No custom attribute named "{args.custattrname}" exists for this tenant.  It needs to be created for this client via the UI first.')
        raise

    taginfo = ops.get_tags(filter_criteria=f"name = '{args.custattrname}'")[0] # Need this to get tag uuid for new opsql/v3 api calls
    tagvalues = ops.get_tag_values(taginfo['id'])
    tag_value_to_uuid = {}
    for val in tagvalues:
        tag_value_to_uuid[val['value']] = val['uniqueId'] 

    existing_values = []
    value_to_value_id = {}
    need_metriclabel_set = []
    # Also make sure all of the existing values have metricLabel set to true
    try:
        existing_values = [ val['value'] for val in attrinfo['customAttributeValues'] ]
        for val in attrinfo['customAttributeValues']:
            value_to_value_id[val['value']] = val['id']
            if not val['metricLabel']:
                need_metriclabel_set.append(val)

    except KeyError as e:
        pass

    if need_metriclabel_set:
        print(f'{len(need_metriclabel_set)} existing attr values have metricLabel=false.  Now setting them to true..')
        for attrval in need_metriclabel_set:
            print(f'Setting metricLabel to true for attrval "{attrval["value"]}"')
            desc = attrval['description'] if 'description' in attrval else ''
            ops.update_tag_value(taginfo['id'], tag_value_to_uuid[attrval["value"]], desc, True)
    else:
        print('There are no existing attr values that have metricLabel=false, so nothing has to be to fixed there...')

    if not args.property:
        print('Since --property option was not specified, we are done here.')
        print('Done.')
        return


    # Get resources matching filter
    print('Getting resources and their existing property and custom attribute values...')
    resources = None
    resources = ops.get_objects(obtype="resources", queryString=args.query, countonly=False)

    # For the retrieved resources, generate a dict of custattr values to resource id
    existing_attr_values_by_resource_id = {}
    existing_resource_ids_by_attrval = {}
    for resource in resources:
        if "tags" in resource:
            attrvals = [ attr['value'] for attr in resource['tags'] if attr['name']==args.custattrname ]
            existing_attr_values_by_resource_id[resource['id']] = attrvals[0] if len(attrvals)>0 else None
            for attrval in attrvals:
                if attrval not in existing_resource_ids_by_attrval:
                    existing_resource_ids_by_attrval[attrval] = []
                ids = existing_resource_ids_by_attrval[attrval]
                ids.append(resource['id'])
                existing_resource_ids_by_attrval[attrval] = ids

    resourcedf = pd.json_normalize(resources)[['id', 'name', args.property]]
    prop_values = resourcedf[args.property].unique()

    #  See which custom attr values are missing and create them
    print('Creating values for this custom attribute that don\'t exist yet...')
    missing_attr_values = [ val for val in prop_values if val not in existing_values and not pd.isna(val) ]

    if missing_attr_values:
        print(f'Adding the following missing values for {args.custattrname}: {missing_attr_values}...')
        newvals = ops.add_custom_attr_value(attrinfo['id'], missing_attr_values, is_metric_label=True)

        # Add the value ids for the newly created values to the dict lookup
        for valobj in newvals['customAttributeValues']:
            value_to_value_id[valobj['value']] = valobj['id']

    else:
        print(f'No missing values for {args.custattrname} need to be added...')
    
    # Set the custattr values on the resources if they are missing or different
    resourcedf['attributes.accountName'] = resourcedf['attributes.accountName'].replace({np.nan: "", None: ""})
    for val in value_to_value_id.keys():
        if val not in existing_resource_ids_by_attrval:
            existing_resource_ids_by_attrval[val] = []
        resource_ids_with_value = list(resourcedf[resourcedf['attributes.accountName'].str.fullmatch(val)]['id'])
        resource_need_to_set = [ resid for resid in resource_ids_with_value if resid not in  existing_resource_ids_by_attrval[val] ]

        print(f'Value "{val}" needs to be set on {len(resource_need_to_set)} resources...')
        for resid in resource_need_to_set:
            print(f'Setting value "{val}" on resource id {resid}...')
            result = ops.set_custom_attr_on_devices(attrinfo['id'], value_to_value_id[val], resid)

    # Done!
    print('Done')
