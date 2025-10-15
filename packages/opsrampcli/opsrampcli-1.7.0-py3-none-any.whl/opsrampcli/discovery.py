import json

def do_cmd_getdiscoprofile(ops, args):                    
    print(json.dumps(ops.get_discoprofile(args.id, args.tenantId)))