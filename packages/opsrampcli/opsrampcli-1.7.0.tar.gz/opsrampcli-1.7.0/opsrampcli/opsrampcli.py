import json
import yaml
import sys
import logging
from opsrampcli import argparsing, opsrampenv, alerts, incidents, resources, discovery, monitoring, escalationpolicies, customattrs, servicemaps, integrations
import signal
import asyncio
import time


def signal_handler(sig, frame):
    print('\n\nYou pressed Ctrl+C, exiting!\n')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )

logger = logging.getLogger(__name__)

def get_env_from_file(envname="", envfile=""):
    logger.debug(f'Env is {envname} envfile is {envfile}')
    envstream = open(envfile, 'r')
    envs = yaml.safe_load(envstream)
    logger.debug("Looking for environment named \"%s\" in %s." % (envname, envfile))
    filtered_envs = filter(lambda x: (x["name"] == envname), envs)
    env = next(filtered_envs)
    return env

def check_env_options():
    if len(sys.argv) < 2:
        print("\nYou need to specify a command.")
        print(f'For more info try: opcli -h\n')
        sys.exit(1)

    elif  '-h' not in sys.argv and \
        '--help' not in sys.argv and \
        'transformsvcmap' not in sys.argv and \
        'webhookalerts' not in sys.argv and \
        '--env' not in sys.argv and ( \
            '--url' not in sys.argv or \
            '--client_id' not in sys.argv or \
            '--client_secret' not in sys.argv or \
            '--tenant' not in sys.argv \
        ):
        print("\nYou need to specify url, client_id, client_secret, and tenant for this command!")
        print(f'For more info try: opcli {sys.argv[1]} -h\n')
        sys.exit(1)
      
    elif '-h' not in sys.argv and \
         '--help' not in sys.argv and \
         'webhookalerts' in sys.argv and \
         '--env' not in sys.argv and ( \
            '--url' not in sys.argv or \
            '--tenant' not in sys.argv or \
            '--vtoken' not in sys.argv \
        ):
        print("\nYou need to specify url, tenant, and vtoken for this command!")
        print(f'For more info try: opcli {sys.argv[1]} -h\n')
        sys.exit(1)

def check_postalert_options(args):
    if (args.infile or args.range) and (
        args.subject or
        args.state or
        args.metric or
        args.resource or
        args.source or
        args.comp or
        args.desc or
        args.prob or
        args.client
    ):
        print('\nYou cannot mix json file options with command line alert content options.\n')
        sys.exit(-1)
    
    if  (args.subject or
        args.state or
        args.metric or
        args.resource or
        args.source or
        args.comp or
        args.desc or
        args.prob or
        args.client) and not (
        args.subject and
        args.state and
        args.metric and
        args.resource
    ):
        print('\nWhen specifying alert content via command line, the --subject, --state, --metric, and --resource options are required.\n')
        sys.exit(-1)

    if not (
        args.subject or
        args.state or
        args.metric or
        args.resource or
        args.source or
        args.comp or
        args.desc or
        args.prob or
        args.client or
        args.infile       
    ):
        print('\nAlert content must be specified either via json file or command line options.\n')
        sys.exit(-1)   
    
def setup_logging(level):
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )

def main():
    asyncio.run(main_async())
    return 0

async def main_async():
    start_time = time.time()
    check_env_options()
    args = argparsing.do_arg_parsing()
    setup_logging(args.loglevel)
    logger = logging.getLogger(__name__)
    logger.info(f'Starting execution of opcli {args.command}')

    ops = None
    env = {}
    if hasattr(args, 'env') and args.env:
        env = get_env_from_file(args.env, args.envfile)
    elif hasattr(args, 'url') and args.url:
        env['name'] = "CommandLine"
        for attr in ['url', 'client_id', 'client_secret', 'tenant', 'partner', 'vtoken']:
            if hasattr(args, attr):
                env[attr] = getattr(args, attr)
    if 'partner' not in env:
        env['partner'] = ""
    ops = opsrampenv.OpsRampEnv(env, args.secure)
    if args.command == "getalerts":
        alerts.do_cmd_getalerts(ops, args)
    elif args.command == "postalerts":
        args.auth = "oauth"
        check_postalert_options(args)
        alerts.do_cmd_postalerts(ops, args)
    elif args.command == "webhookalerts":
        args.auth = "vtoken"
        alerts.do_cmd_postalerts(ops, args)
    elif args.command == "getincidents":
        incidents.do_cmd_getincidents(ops, args)
    elif args.command == "syncincidentfromdatasource":
        await incidents.do_cmd_sync_incidents_with_datasource(ops, args)
    elif args.command == "getdiscoprofile":
        discovery.do_cmd_getdiscoprofile(ops, args)
    elif args.command == "getalertesc":
        escalationpolicies.do_cmd_getalertescalations(ops, args)
    elif args.command == "migratealertesc":
        escalationpolicies.do_cmd_migratealertescalations(ops, args)
    elif args.command == "getcustomattrs":
        result = customattrs.do_cmd_get_custom_attributes(ops, args)
        try:
            print(json.dumps(result, indent=2, sort_keys=False))
        except Exception as e:
            pass
    elif args.command == "getresources":
        result = resources.do_cmd_get_resources(ops, args)
        try:
            print(json.dumps(result, indent=2, sort_keys=False))
        except Exception as e:
            pass
    elif args.command == "importresources":
        resources.do_cmd_import_resources(ops, args)
    elif args.command == "importfromdatasource":
        await resources.do_cmd_importfromdatasource(ops, args)
    elif args.command == "customattrmetriclabel":
        customattrs.do_cmd_customattrmetriclabel(ops, args)
    elif args.command == "exportcustattrfile":
        customattrs.do_cmd_make_custom_attr_file(ops, args)
    elif args.command == "importcustattrfile":
        customattrs.do_cmd_import_custom_attr_file(ops, args)
    elif args.command == "addpropasmetriclabel":
        customattrs.do_cmd_add_prop_as_metric_label(ops, args)
    elif args.command == "getservicemaps":
        print(json.dumps(ops.get_service_maps(), indent=2, sort_keys=False));
    elif args.command == "getchildsvcgroups":
        print(json.dumps(ops.get_child_service_groups(args.parent), indent=2, sort_keys=False));
    elif args.command == "getservicegroup":
        print(json.dumps(ops.get_service_group(args.id), indent=2, sort_keys=False));
    elif args.command == "exportservicemaps":
        servicemaps.do_cmd_export_service_maps(ops, args)
    elif args.command == "transformsvcmap":
        servicemaps.do_cmd_transform_service_map(args)
    elif args.command == "importservicemaps":
        servicemaps.do_cmd_import_service_maps(ops, args)
    elif args.command == "cloneservicemaps":
        servicemaps.do_cmd_clone_service_maps(ops, args)
    elif args.command == "gettemplates":
        monitoring.do_cmd_get_templates(ops, args)
    elif args.command == "clonetemplates":
        monitoring.do_cmd_clone_templates(ops, args)
    elif args.command == "metricsql":
        print(json.dumps(ops.do_instant_metric_query(args.instant_query), indent=2, sort_keys=False))
    elif args.command == "setbaselinethreshold":
        monitoring.do_cmd_set_baseline_threshold(ops, args)        
    elif args.command == "getintegrations":
        print(json.dumps(ops.get_integrations(args.query, filter=args.filter), indent=2, sort_keys=False))
    elif args.command == "importintegrations":
        integrations.do_import_integrations(ops, args)
    elif args.command == "addazurearmintegration":
        print(json.dumps(integrations.do_add_azure_arm(ops, args), indent=2, sort_keys=False))
    elif args.command == "addazureasmintegration":
        print(json.dumps(integrations.do_add_azure_asm(ops, args), indent=2, sort_keys=False))
    elif args.command == "addkubernetesintegration":
        integrations.do_add_kubernetes(ops, args)

    await ops.close_async_session()

    end_time = time.time()
    run_time_seconds = end_time - start_time
    hours = int(run_time_seconds // 3600)
    minutes = int((run_time_seconds % 3600) // 60)
    seconds = int(run_time_seconds % 60)
    logger.info(f"Completed execution of opcli {args.command} in {hours}:{minutes:02d}:{seconds:02d}")

if __name__ == "__main__":
    main()
