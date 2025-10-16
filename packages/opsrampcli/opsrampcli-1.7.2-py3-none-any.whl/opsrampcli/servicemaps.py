import re
import sys
from datetime import datetime
import json
import os

SERVICEMAP_CREATION_EXCLUDE_ATTRS = ['id', 'createdDate', 'updatedDate', 'client', 'parent', 'linkedService']

def do_cmd_export_service(ops, id):
    service = {}
    svc = ops.get_service_group(id)
    print(f'Getting service {svc["name"]}...')
    children = ops.get_child_service_groups(id)
    service['_service'] = svc
    service['_children'] = children
    if 'childType' in svc and svc['childType'] == 'SERVICE' and 'totalResults' not in children:
        service['_child_services'] = {}
        for childsvc in children:
            service['_child_services'][childsvc['name']] = do_cmd_export_service(ops, childsvc['id'])
    return service


def do_cmd_export_service_maps(ops, args):
    qstring = None
    if args.name:
        qstring = f'name:{args.name}'
    services = ops.get_service_maps(qstring)
    if len(services) >= 1 and "totalResults" not in services and "id" in services[0]:
        ts = str(int(datetime.now().timestamp()))
        for service in services:
            exportfile = f'{args.outdir}{os.path.sep}servicemap_{service["name"]}.json'
            if args.timestamp:
                exportfile = f'{args.outdir}{os.path.sep}servicemap_{ts}_{service["name"]}.json'
            if not args.clobber:
                if os.path.exists(exportfile):
                    print(f'Export file {exportfile} already exists.  If you want to overwrite it use the --clobber option.')
                    print(f'Skipping export of Service Map {service["name"]}.')
                    continue
            servicejson = json.dumps(do_cmd_export_service(ops, service["id"]), indent=2, sort_keys=False)
            with open(exportfile, 'w') as f:
                print(f'Writing export file {exportfile}')
                f.write(servicejson)
                f.close()
    else:
        print(f'No matching Service Maps found.  Cannot perform export.')
        sys.exit(1)
    print("Done")

def transform_svcmap_content(replacers, full_service_map):
    full_service_map_json = json.dumps(full_service_map)
    for replacer in replacers:
        full_service_map_json = re.sub(replacer[0], replacer[1], full_service_map_json)
    full_service_map = json.loads(full_service_map_json)
    return full_service_map

def do_cmd_transform_service_map(args):
    print(f'Reading export file {args.src}...')
    f = open(args.src)
    full_service_map = json.load(f)
    f.close()
    full_service_map = transform_svcmap_content(args.replace, full_service_map)
    if not args.clobber:
        if os.path.exists(args.dest):
            print(f'Dest file {args.dest} already exists.  If you want to overwrite it use the --clobber option.')
            print('New file not written - Exiting.')
            sys.exit(0)
    with open(args.dest, 'w') as f:
        f.write(json.dumps(full_service_map, indent=2, sort_keys=False))
        f.close()
        print(f'Transformed export written to {args.dest}.')

    print("Done")

def import_service_map(ops, args, map, parent=None):
    if '_service' not in map:
        print('Invalid export content, skipping this service.')
        return None
    svcgroup = {}
    for key, value in map['_service'].items():
        if key not in SERVICEMAP_CREATION_EXCLUDE_ATTRS:
            svcgroup[key] = value
    if parent:
        svcgroup['parent'] = {"id": parent}
    if args.replace:
        svcgroup = transform_svcmap_content(args.replace, svcgroup)
    result = ops.create_or_update_service_group(svcgroup)
    if result:
        parentsvc = result['id']
        print(f'Imported service {svcgroup["name"]}')

    if not parent and args.parentlink and 'parent' in map['_service'] and 'id' in map['_service']['parent'] and map['_service']['linkedService']:
        linkresult = ops.link_service_group(parent=map['_service']['parent']['id'], child=result["id"])


    if '_child_services' in map:
        for name, childsvc in map['_child_services'].items():
            print(f'Importing service group {name}')
            import_service_map(ops, args, childsvc, parentsvc)

def do_cmd_import_service_maps(ops, args):
    print(f'Reading export file {args.src}...')
    f = open(args.src)
    service_map_export = json.load(f)
    f.close()
    if type(service_map_export) == list:
        for map in service_map_export:
            import_service_map(ops, args, map)
    else:
        import_service_map(ops, args, service_map_export)

def do_cmd_clone_service_maps(ops, args):
    qstring = f'name:{args.name}'
    services = ops.get_service_maps(qstring)
    if len(services) > 1:
        print(f'More than one service matching name {args.name} found.  Cannot proceed, exiting.')
        sys.exit(-1)
    if "totalResults" in services:
        print(f'No service with name {args.name} found.  Cannot proceed, exiting')
        sys.exit(-1)

    service = do_cmd_export_service(ops, services[0]["id"])
    import_service_map(ops, args, service)
    print("Done")