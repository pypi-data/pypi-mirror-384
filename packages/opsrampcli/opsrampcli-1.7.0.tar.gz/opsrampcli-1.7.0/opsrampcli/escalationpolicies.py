import json
import copy
from opsrampcli import opsrampenv

def do_cmd_getalertescalations(ops, args):
    if args.details:
        details = []
        policies = ops.get_alertescalations(args.query)
        for policy in policies:
            params = {}
            allClients = False
            if "allClients" in policy and policy["allClients"]:
                allClients = True
            policydetails = ops.get_alertescalation(allClients, policy["id"], params)
            details.append(policydetails)
        print(json.dumps(details, indent=2, sort_keys=False))
    else:
        print(json.dumps(ops.get_alertescalations(args.query), indent=2, sort_keys=False))


def prepare_policy_for_create(object, idmap, parentkey=""):
    removable_set = {"scope", "id", "uniqueId", "createdDate", "updatedDate", "createdTime", "updatedTime", "createdBy", "updatedBy", "priorityRules"}
    objectcopy = copy.deepcopy(object)
    if isinstance(object, dict):
        for key, val in object.items():
            if key in removable_set:
                del objectcopy[key]
            # API missing incident update details workaround
            elif key == "updateIncident" and val == {}:
                objectcopy[key] = {"none": True}
            # API Resource Type validation defect workaround
            elif (key == "key") and (val == "Resource : Resource Type") and ("operator" in object):
                objectcopy["value"] = "DEVICE"
                print("Had to substitute DEVICE for Resource Type %s to prevent create failure." % (object["value"]))
            elif isinstance(val, dict) or isinstance(val, list):
                objectcopy[key] = prepare_policy_for_create(val, idmap, key)
        for key in idmap:
            obtype = key
            if idmap[obtype]['objcheck'](object, parentkey):
                if obtype == "clients":
                    objectcopy["id"] = idmap[obtype]["map"]["dest"]["uniqueId"]
                    objectcopy["name"] = idmap[obtype]["map"]["dest"]["name"]
                else:
                    if object[idmap[obtype]["nameattr"]] in idmap[obtype]["map"] and idmap[obtype]["map"][object[idmap[obtype]["nameattr"]]]["has_dest"]:
                        if obtype == "urgencies":
                            objectcopy["uniqueId"] = idmap[obtype]["map"][object[idmap[obtype]["nameattr"]]]["destid"]
                        else:
                            objectcopy["id"] = idmap[obtype]["map"][object[idmap[obtype]["nameattr"]]]["destid"]
                        if "destname" in idmap[obtype]["map"][object[idmap[obtype]["nameattr"]]]:
                            objectcopy["name"] = idmap[obtype]["map"][object[idmap[obtype]["nameattr"]]]["destname"]
                    else:
                        print("WARNING: %s named %s does not exist on destination instance!" % (obtype, object["name"]))
    elif isinstance(object, list):
        objectcopy = list(map(lambda obj: prepare_policy_for_create(obj, idmap), object))
    return objectcopy

def build_map_of_obj_ids(obj_lookup):
    idmap = {
        "clients": {
            "idattr": "uniqueId",
            "objcheck": lambda obj,parentkey : ("type" in obj and obj['type']=='CLIENT') or ("isClient" in obj and obj['isClient']),
            "changename": True,
            "nameattr": "name"
        },
        "incidentCustomFields": {
            "type": "CLIENT",
            "idattr": "id",
            "objcheck": lambda obj,parentkey : "customField" in obj and obj['customField'],
            "changename": False,
            "nameattr": "displayLabel"
        },
        "deviceGroups": {
            "type": "DEVICEGROUP",
            "idattr": "id",
            "objcheck": lambda obj,parentkey : "type" in obj and obj['type']=='DEVICEGROUP',
            "changename": False,
            "nameattr": "name"
        },
        "userGroups": {
            "type": "CLIENT",
            "idattr": "uniqueId",
            "objcheck": lambda obj,parentkey : "type" in obj and obj['type']=='USERGROUP_DL',
            "changename": False,
            "nameattr": "name"
        },
        "urgencies": {
            "type": "URGENCY",
            "idattr": "uniqueId",
            "objcheck": lambda obj,parentkey : parentkey == "urgency",
            "changename": False,
            "nameattr": "name"
        }
    }

    for key in idmap:
        obtype = key
        map = {}
        if obtype != "clients":
            for srcrec in obj_lookup["source"][obtype]:
                name = srcrec[idmap[obtype]["nameattr"]]
                map[name] = {}
                map[name]["sourceid"] = srcrec[idmap[obtype]["idattr"]]
                map[name]["has_dest"] = False
                for destrec in obj_lookup["dest"][obtype]:
                    if destrec[idmap[obtype]["nameattr"]] == name:
                        map[name]["has_dest"] = True
                        map[name]["destid"] = destrec[idmap[obtype]["idattr"]]
                        if idmap[obtype]["nameattr"] != "name":
                            map[name]["srcname"] = srcrec["name"]
                            map[name]["destname"] = destrec["name"]
                        break
        else:
            map["source"] = obj_lookup["source"][obtype]
            map["dest"] = obj_lookup["dest"][obtype]

        idmap[obtype]["map"] = map

    return idmap




def do_cmd_migratealertescalations(ops, args):
    '''
    routing = {}
    with open('mappingfile.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            routing[row["RuleName"]] = row
    '''

    ops_env = {}
    ops_env["source"] = ops
    ops_env["dest"] = opsrampenv.OpsRampEnv(args.to_env, args.envfile, args.secure)
  

    obj_lookup = {}
    for env in ["source", "dest"]:
        obj_lookup[env] = {}
        for obtype in ["clients", "incidentCustomFields", "deviceGroups", "userGroups", "urgencies"]:
            obj_lookup[env][obtype] = ops_env[env].get_objects(obtype=obtype)
    
    idmap = build_map_of_obj_ids(obj_lookup)
    policies = ops_env["source"].get_alertescalations(args.query)

    printarr = []
    for policy in policies:
        '''
        if policy['name'] not in routing:
            print("Skipping create of policy %s on %s as it is not on the spreadsheet." % (policy["name"], args.to_env))
            continue
        '''

        params = {}
        allClients = False
        if "allClients" in policy and policy["allClients"]:
            allClients = True
        policydetails = ops_env["source"].get_alertescalation(allClients, policy["id"], params)

        if "message" in policydetails and "code" in policydetails:
            print("Unable to get policy %s details from %s  - you may need to migrate this one manually.\n%s" % (policy["name"], args.env, repr(policydetails)))
            continue

        if args.filter:
            try:
                if not eval(args.filter):
                    print("Skipping policy %s as it does not match filter criteria" % (policy["name"]))
                    continue
            except Exception as e:
                print("Failed to run filter expression for policy %s.  Treating as false:\n%s" % (policy['name'], repr(e)))
                continue         

        if args.preexec:
            try:
                exec(args.preexec)
            except Exception as e:
                print("Failed to run preexec for policy %s:\n%s" % (policy['name'], repr(e)))    

        print("Performing prep and id mapping for policy %s" % (policy["name"]))
        newpolicy = prepare_policy_for_create(policydetails, idmap)

        if args.postexec:
            try:
                exec(args.postexec)
            except Exception as e:
                print("Failed to run postexec for policy %s:\n%s" % (newpolicy['name'], repr(e)))      

        if args.setactive:
            if args.setactive == "ON":
                newpolicy['enabledMode'] = "ON"
                newpolicy['active'] = True
            elif args.setactive == "OFF":
                newpolicy['enabledMode'] = "OFF"
                newpolicy['active'] = False

        # CSV mapping stuff - not usually needed
        '''
        if "escalations" in newpolicy and "incident" in newpolicy["escalations"][0] and "customFields" in newpolicy["escalations"][0]['incident']:
            if newpolicy['name'] in routing:
                cfield1 = {
                            "classCode": "INCIDENT",
                            "displayLabel": "Cherwell Assignment Group",
                            "name": "cherwell_assignment_group_853",
                            "fieldType": "TYPE_TEXT",
                            "mandatory": False,
                            "editable": True,
                            "description": "",
                            "value": routing[newpolicy['name']]["CherwellAssignedGroup"],
                            "defaultValue": "",
                            "customField": True,
                            "id": "UDF0000000853"
                        }
                cfield2 = {
                            "classCode": "INCIDENT",
                            "displayLabel": "Cherwell Category",
                            "name": "resource_type_858",
                            "fieldType": "TYPE_TEXT",
                            "mandatory": False,
                            "editable": True,
                            "description": "",
                            "value": routing[newpolicy['name']]["CherwellClassificationCategory"],
                            "defaultValue": "",
                            "customField": True,
                            "id": "UDF0000000858"
                        }
                cfield3 = {
                            "classCode": "INCIDENT",
                            "displayLabel": "Cherwell Subcategory",
                            "name": "cherwell_subcategory_868",
                            "fieldType": "TYPE_TEXT",
                            "mandatory": False,
                            "editable": True,
                            "description": "",
                            "value": routing[newpolicy['name']]["CherwellClassificationSubcategory"],
                            "defaultValue": "",
                            "customField": True,
                            "id": "UDF0000000868"
                        }
                newpolicy["escalations"][0]['incident']["customFields"].append(cfield1)
                newpolicy["escalations"][0]['incident']["customFields"].append(cfield2)
                newpolicy["escalations"][0]['incident']["customFields"].append(cfield3)
        '''

        printarr.append(newpolicy)

        # Workaround for missing resources attr when all client devices are included in policy def
        if "resources" not in newpolicy:
            newpolicy["resources"] = [
                                        {
                                            "id": ops_env["dest"].get_env()["client_id"],
                                            "type": "CLIENT"
                                        }
            ]
        if not args.test:
            #if newpolicy['name'] in routing:
                print("Creating policy %s on %s" % (policy["name"], args.to_env))
                result = ""
                if args.update:
                    result = ops_env["dest"].update_alertescalation(newpolicy, policy["id"])
                else:
                    result = ops_env["dest"].create_alertescalation(newpolicy)
                if "id" in result:
                    print("Created or modified policy %s on %s with id: %s" % (policy["name"], args.to_env, result["id"]))
                else:
                    print(repr(result))
            #else:
            #    print("Skipping create of policy %s on %s as it is not on the spreadsheet." % (policy["name"], args.to_env))

    if args.test:
        print(json.dumps(printarr, indent=2, sort_keys=False))