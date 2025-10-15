import argparse
from datetime import datetime, timedelta

# Calculate 1 hr ago datetime string for use in default --query arg value
one_hour_ago = (datetime.now() - timedelta(hours = 1)).astimezone().strftime("%Y-%m-%dT%H:%M:%S%z")
one_hour_ago = one_hour_ago.replace('+', ' ')
getalerts_default_query = f'startDate:{one_hour_ago}'

def setup_env_parser():
    # Parser with env-related options that are shared across most of the commands
    env_parser = argparse.ArgumentParser(add_help=False, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    env_file = env_parser.add_argument_group(title="Specify credentials via YAML file")
    env_file.add_argument('--env', help='Name of environment to use, as defined in your environments.yml file')
    env_file.add_argument('--envfile', default='environments.yml', help='Location of environments YAML file')

    env_cli = env_parser.add_argument_group(title="Specify credentials via command line")
    env_cli.add_argument('--url', help='OpsRamp API URL')
    env_cli.add_argument('--client_id', metavar='KEY', help='OpsRamp API Key')
    env_cli.add_argument('--client_secret', metavar='SCRT', help='OpsRamp API Secret')
    env_cli.add_argument('--tenant', help='OpsRamp tenant ID')
    env_cli.add_argument('--partner', help='OpsRamp partner ID (usually unnecessary - only needed for partner-level API calls)')

    env_other = env_parser.add_argument_group(title="Other common options")
    env_other.add_argument('--secure', default=True, help='Whether or not to verify SSL cert')
    env_other.add_argument('--loglevel', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], default='INFO', help='Set the logging level')
 
    return env_parser

def setup_arg_parsing():
    env_parser = setup_env_parser()
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter, prog="opcli")
    subparsers = parser.add_subparsers(dest='command', required=True)


    # Alerts - Get

    parser_getalerts = subparsers.add_parser('getalerts', parents=[env_parser], formatter_class=argparse.ArgumentDefaultsHelpFormatter, help="Search for and take action on alerts")
    parser_getalerts.add_argument('--query', default=getalerts_default_query, help='Query String to filter alerts as per https://develop.opsramp.com/resource-management/tenants-tenantid-resources-search')
    parser_getalerts.add_argument('--brief', action='store_true', help='Include only key fields in output')
    parser_getalerts.add_argument('--descr', action='store_true', help='Include the description field in results (runs *much* slower as it requires a separate api call per alert)')
    parser_getalerts.add_argument('--count', action='store_true', help='Only show the count of matching alerts')
    parser_getalerts.add_argument('--filter', required=False, help='Post-query filter on alerts.  Python expression that will evaluate to True or False such as alert["resource"]["name"].startswith("prod")')
    parser_getalerts.add_argument('--action', required=False, help='Perform an action on matching alerts (Heal, acknowledge, suppress, close, unsuppress, unAcknowledge)')
    parser_getalerts.add_argument('--heal', action='store_true', help='Heal the matching alerts (i.e. send a matching Ok)')
    
    # Alerts - Post using API (OAuth creds)
    parser_postalerts = subparsers.add_parser('postalerts', parents=[env_parser], formatter_class=argparse.ArgumentDefaultsHelpFormatter, help="Post alerts using the Alerts API")
    parser_postalerts_file = parser_postalerts.add_argument_group(title="Post alerts using alert content from a json file")
    parser_postalerts_file.add_argument('--infile', help='File containing a json array of alert payloads')
    parser_postalerts_file.add_argument('--range', help='An integer or range identifying which alert in the file to send')

    parser_postalerts_cli = parser_postalerts.add_argument_group(title="Post an alert using alert content from the command line")
    parser_postalerts_cli.add_argument('--subject', help='Alert Subject')
    parser_postalerts_cli.add_argument('--state', choices=('Critical','Warning','Info','Ok'), help='Alert Current State')
    parser_postalerts_cli.add_argument('--metric', help='Alert metric')
    parser_postalerts_cli.add_argument('--resource', help='Alert Resource name')
    parser_postalerts_cli.add_argument('--comp', help='Alert Component name')
    parser_postalerts_cli.add_argument('--desc', help='Alert Description')
    parser_postalerts_cli.add_argument('--source', help='Alert Source name')
    parser_postalerts_cli.add_argument('--prob', help='Alert Problem Area')
    parser_postalerts_cli.add_argument('--client', help='Alert Client ID (only required if posting with a partner-level tenant')
    parser_postalerts_cli.add_argument('--custom', nargs=2, metavar=('NAME','VALUE'), action='append',help='Alert custom attribute name and value (can repeat this option for multiple custom attributes)')

    # Alerts - Post to integration (vtoken creds)
    parser_webhookalerts = subparsers.add_parser('webhookalerts', formatter_class=argparse.ArgumentDefaultsHelpFormatter, help="Post alerts to a Webhook integration")
    parser_webhookalerts.add_argument('--url', help='OpsRamp API URL')
    parser_webhookalerts.add_argument('--tenant', help='OpsRamp tenant ID')
    parser_webhookalerts.add_argument('--vtoken', help='OpsRamp integration webhook token')
    parser_webhookalerts.add_argument('--infile', required=True, help='File containing an array of json alert payloads')
    parser_webhookalerts.add_argument('--range', default='all', help='An integer or range identifying which alert in the file to send')
    parser_webhookalerts.add_argument('--secure', default=True, help='Whether or not to verify SSL cert')


    # Incidents
    parser_getincidents = subparsers.add_parser('getincidents', parents=[env_parser], formatter_class=argparse.ArgumentDefaultsHelpFormatter, help="Search and take action on Incidents")
    parser_getincidents.add_argument('--query', required=True, help='Query String to filter incidents')
    parser_getincidents.add_argument('--brief', action='store_true', help='Include only key fields in output')
    parser_getincidents.add_argument('--details', action='store_true', help='Get the full details for all matched incidents - this will include custom field values')
    parser_getincidents.add_argument('--count', action='store_true', help='Only show the count of matching incidents')
    parser_getincidents.add_argument('--filter', required=False, help='Post-query filter on incidents.  Python expression that will evaluate to True or False such as incident["resource"]["name"].startswith("prod")')
    parser_getincidents.add_argument('--resolve', action='store_true', help='Resolve the matching incidents')

    parser_syncincidentfromdatasource= subparsers.add_parser('syncincidentfromdatasource', parents=[env_parser], formatter_class=argparse.ArgumentDefaultsHelpFormatter, help="Sync incident status from a data source.")
    parser_syncincidentfromdatasource.add_argument('--job', required=True, help='Name of yaml job definition file')

    # Resources/Devices
    parser_getresources = subparsers.add_parser('getresources', parents=[env_parser], formatter_class=argparse.ArgumentDefaultsHelpFormatter, help="Search for and take action on resources/devices")
    parser_getresources.add_argument('--query', required=False, help='Query String to filter resources as per https://develop.opsramp.com/resource-management/tenants-tenantid-resources-search')
    parser_getresources.add_argument('--search', required=False, help='Search String to filter resources as it would be entered under Resources -> Search')
    parser_getresources.add_argument('--count', action='store_true', help='Only show the count of matching resources')
    parser_getresources.add_argument('--delete', action='store_true', help='Delete the matching resources')
    parser_getresources.add_argument('--manage', action='store_true', help='Manage the matching resources')
    parser_getresources.add_argument('--filter', required=False, help='Post-query filter on resources.  Python expression that will evaluate to True or False such as alert["resource"]["name"].startswith("prod")')

    parser_importresources = subparsers.add_parser('importresources', parents=[env_parser], formatter_class=argparse.ArgumentDefaultsHelpFormatter, help="Import resources from a spreadsheet.  Custom attr field names should be prefixed with \"tag.\" and the custom attribute names should be created in advance via the UI.  Any resource with an Action Processing column value of Delete will be deleted.")
    parser_importresources.add_argument('--commit', action='store_true', help='Make the actual updates on the platform.  If not specified, only error checking and import simulation will occur.')
    parser_importresources.add_argument('--addnames', action='store_true', help='If new tag/custattr names are found in the data source, add the definitions on the fly.  Otherwise new tag names will be considered an error.')
    parser_importresources.add_argument('--addvalues', action='store_true', help='If new values are found in the spreadsheet, add the value definitions on the fly.  Otherwise new values will be considered an error.')
    parser_importresources.add_argument('--writeblanks', action='store_true', help='When no value is provided in the spreadsheet for a resource, remove any existing value for that resource on the platform.  If not specified then no action is taken for empty values.')
    parser_importresources.add_argument('--filename', required=False, help='Name of excel file to import (.xlsx extension will be added if not specified.)')
    parser_importresources.add_argument('--nocreate', action='store_true', help='Don\'t create new resources.')

    parser_addpropasmetriclabel = subparsers.add_parser('addpropasmetriclabel', parents=[env_parser], formatter_class=argparse.ArgumentDefaultsHelpFormatter, help="Add a resource property as a custom attribute value of the matched resources, with metric label option selected")
    parser_addpropasmetriclabel.add_argument('--query', required=False, help='Query String to filter resources as per https://develop.opsramp.com/resource-management/tenants-tenantid-resources-search')
    parser_addpropasmetriclabel.add_argument('--property', required=False, help='Resource property in dot notation to be with values to be added as a custattr values, for example attributes.accountName (Must be in content returned by getresources)')
    parser_addpropasmetriclabel.add_argument('--custattrname', required=True, help='Custom attribute name - must already be existing (i.e. defined via UI.).  This command only adds new values to it if needed.')


    # Service Maps
    parser_exportservicemaps = subparsers.add_parser('exportservicemaps', parents=[env_parser], formatter_class=argparse.ArgumentDefaultsHelpFormatter, help="Export one or more full Service Map definitions to a file which can be manipulated and re-imported")
    parser_exportservicemaps.add_argument("--name", required=False, help='Name of the root level Service Map/Group (export all if not specified)')
    parser_exportservicemaps.add_argument("--outdir", default=".", help='Directory path where export will be saved')
    parser_exportservicemaps.add_argument('--clobber', action='store_true', help='Remove/overwrite prior exports of same maps')
    parser_exportservicemaps.add_argument('--timestamp', action='store_true', help='Include a timestamp in the Service Map dir name')

    parser_importservicemaps = subparsers.add_parser('importservicemaps', parents=[env_parser], formatter_class=argparse.ArgumentDefaultsHelpFormatter, help="Import (and optionally transform while doing so) from a Service Map export file")
    parser_importservicemaps.add_argument("--src", required=True, help='Source: Path to the export file of a Service Map')
    parser_importservicemaps.add_argument('--replace', nargs=2, required=False, metavar=('REGEX','REPLACEWITH'), action='append', help='Transforming regex pattern and replacement string (option can be repeated)')
    parser_importservicemaps.add_argument('--parentlink', action='store_true', help='If root Service has a link to a parent, link the imported Service Map')
    parser_importservicemaps.add_argument('--clobber', action='store_true', help='Overwrite Service Map (i.e. with same name) if it already exists')

    parser_cloneservicemaps = subparsers.add_parser('cloneservicemaps', parents=[env_parser], formatter_class=argparse.ArgumentDefaultsHelpFormatter, help="Copy an existing Service Map, with transformations/replacements (useful when you have a template Service Map to re-use)")
    parser_cloneservicemaps.add_argument("--name", required=True, help='Name of Service Map to transform and clone')
    parser_cloneservicemaps.add_argument('--replace', nargs=2, required=True, metavar=('REGEX','REPLACEWITH'), action='append', help='Transforming regex pattern and replacement string (option can be repeated)')
    parser_cloneservicemaps.add_argument('--parentlink', action='store_true', help='If root Service has a link to a parent, link the imported Service Map')
    parser_cloneservicemaps.add_argument('--clobber', action='store_true', help='Overwrite Service Map (i.e. with same name) if it already exists')

    parser_transformsvcmap = subparsers.add_parser("transformsvcmap", formatter_class=argparse.ArgumentDefaultsHelpFormatter, help="Apply regex replacements to an exported Service Map and create a new transformed export file with the changes")
    parser_transformsvcmap.add_argument("src", help='Source: File path where a Service Map was previously exported')
    parser_transformsvcmap.add_argument("dest", help='Destination: File path where the transformed export will be saved')
    parser_transformsvcmap.add_argument('--replace', nargs=2, required=True, metavar=('REGEX','REPLACEWITH'), action='append', help='Transforming regex pattern and replacement string (option can be repeated)')
    parser_transformsvcmap.add_argument('--clobber', action='store_true', help='Overwrite dest file if it already exists')

    parser_getservicemaps = subparsers.add_parser('getservicemaps', parents=[env_parser], formatter_class=argparse.ArgumentDefaultsHelpFormatter, help="Get Service Map definitions")

    parser_getchildsvcgroups = subparsers.add_parser('getchildsvcgroups', parents=[env_parser], formatter_class=argparse.ArgumentDefaultsHelpFormatter, help="Get child Service Groups of a parent Service")
    parser_getchildsvcgroups.add_argument('--parent', required=True, help='ID of the parent Service Map/Group')

    parser_getservicegroup = subparsers.add_parser('getservicegroup', parents=[env_parser], formatter_class=argparse.ArgumentDefaultsHelpFormatter, help="Get the full definition of a Service Group")
    parser_getservicegroup.add_argument('--id', required=True, help='ID of the Service Map/Group')

    # Custom Attributes
    parser_exportcustattrfile = subparsers.add_parser('exportcustattrfile', parents=[env_parser], formatter_class=argparse.ArgumentDefaultsHelpFormatter, help="Generate an Excel or csv file from existing custom attribute values")
    parser_exportcustattrfile.add_argument('--query', required=False, help='Query String to filter resources as per https://develop.opsramp.com/resource-management/tenants-tenantid-resources-search')
    parser_exportcustattrfile.add_argument('--search', required=False, help='Search String to filter resources as it would be entered under Resources -> Search')
    parser_exportcustattrfile.add_argument('--filter', required=False, help='Post-query filter on resources.  Python expression that will evaluate to True or False such as alert["resource"]["name"].startswith("prod")')
    parser_exportcustattrfile.add_argument('--filename', required=False, help='Name of excel file to generate (.xlsx extension will be added)')
    parser_exportcustattrfile.add_argument('--attrs', required=False, help='Comma separated list of Custom Attribute names to include (no custom attrs will be exported if not specified)')
    parser_exportcustattrfile.add_argument('--props', required=False, help='Comma separated list of Resource Properties to include (Use dot-walk notation based on getresources json payload)')

    parser_importcustattrfile = subparsers.add_parser('importcustattrfile', parents=[env_parser], formatter_class=argparse.ArgumentDefaultsHelpFormatter, help="Import an Excel file containing custom attribute values")
    parser_importcustattrfile.add_argument('--commit', action='store_true', help='Make the actual updates on the platform.  If not specified, only error checking and import simulation will occur.')
    parser_importcustattrfile.add_argument('--addnames', action='store_true', help='If new tag/custattr names are found in the data source, add the definitions on the fly.  Otherwise new tag names will be considered an error.')
    parser_importcustattrfile.add_argument('--addvalues', action='store_true', help='If new values are found in the spreadsheet, add the value definitions on the fly.  Otherwise new values will be considered an error.')
    parser_importcustattrfile.add_argument('--writeblanks', action='store_true', help='When no value is provided in the spreadsheet for a resource, remove any existing value for that resource on the platform.  If not specified then no action is taken for empty values.')
    parser_importcustattrfile.add_argument('--filename', required=False, help='Name of excel file to import (.xlsx extension will be added if not specified.)')

    parser_getcustomattrs = subparsers.add_parser('getcustomattrs', parents=[env_parser], formatter_class=argparse.ArgumentDefaultsHelpFormatter, help="Get custom attribute definitions")

    parser_importfromdatasource= subparsers.add_parser('importfromdatasource', parents=[env_parser], formatter_class=argparse.ArgumentDefaultsHelpFormatter, help="Import Resources & Custom Attributes from a data source.")
    parser_importfromdatasource.add_argument('--job', required=True, help='Name of yaml job definition file')
    parser_importfromdatasource.add_argument('--commit', action='store_true', help='Make the actual updates on the platform.  If not specified, only error checking and import simulation will occur.')
    parser_importfromdatasource.add_argument('--addnames', action='store_true', help='If new tag/custattr names are found in the data source, add the definitions on the fly.  Otherwise new tag names will be considered an error.')
    parser_importfromdatasource.add_argument('--addvalues', action='store_true', help='If new values are found in the data source, add the value definitions on the fly.  Otherwise new values will be considered an error.')
    parser_importfromdatasource.add_argument('--writeblanks', action='store_true', help='When no value is provided in the data source record for a resource, remove any existing value for that resource on the platform.  If not specified then no action is taken for empty values.')
    parser_importfromdatasource.add_argument('--alertonmisssing', choices=['INFO', 'WARNING', 'CRITICAL'], help="Post alerts for resources that are in the data source but not in OpsRamp")
    #parser_importfromdatasource.add_argument('--nocreate', action='store_true', help='Don\'t create new resources.')
    #parser_importfromdatasource.add_argument('--native_attrs_update', choices=['ALL', 'NONE', 'TYPEONLY'], help='Controls if native attributes will get updated (custom attributes are always updated)')
    #parser_importfromdatasource.add_argument('--metricLabel', action='store_true', help='Add new attribute values with metricLabel=true (i.e. they will be used as metric labels).')

    parser_customattrasmetriclabel= subparsers.add_parser('customattrmetriclabel', parents=[env_parser], formatter_class=argparse.ArgumentDefaultsHelpFormatter, help="Make all values of an existing custom attribute a metric label or not a metric label")
    parser_customattrasmetriclabel.add_argument('--attrname', required=True, help="Custom attribute name")
    parser_customattrasmetriclabel.add_argument('--ismetriclabel', required=True, choices=('YES', 'NO'), help="YES makes it a metric label, NO makes it not a metric label")
    
    # Discovery Profiles
    parser_getdiscoprofile = subparsers.add_parser('getdiscoprofile', parents=[env_parser], formatter_class=argparse.ArgumentDefaultsHelpFormatter, help="Get discovery profile definition")
    parser_getdiscoprofile.add_argument('--id', required=True, help='Discovery profile ID')
    parser_getdiscoprofile.add_argument('--tenantId', required=True, help='Client ID or MSP ID of the tenant')

    # Escalation Policies
    parser_getalertesc = subparsers.add_parser('getalertesc', parents=[env_parser], formatter_class=argparse.ArgumentDefaultsHelpFormatter, help="Search and get Escalation Policy definitions")
    parser_getalertesc.add_argument('--query', required=False, help='Query String to filter alerts')
    parser_getalertesc.add_argument('--details', action='store_true', help='Get the full details for all matched policies')
    parser_getalertesc.add_argument('--count', action='store_true', help='Only show the count of matching alerts')
    parser_getalertesc.add_argument('--filter', required=False, help='Post-query filter on alerts.  Python expression that will evaluate to True or False such as alert["resource"]["name"].startswith("prod")')

    parser_migratealertesc = subparsers.add_parser('migratealertesc', parents=[env_parser], formatter_class=argparse.ArgumentDefaultsHelpFormatter, help="Migrate/copy Escalation Policies within same tenant or from one tenant to another")
    parser_migratealertesc.add_argument('--query', required=False, help='Query string to filter policies from source/from instance')
    parser_migratealertesc.add_argument('--filter', required=False, help='Filter for which policies to migrate.  Python expression that will evaluate to True or False such as alert["resource"]["name"].startswith("prod")')
    parser_migratealertesc.add_argument('--preexec', required=False, help='Pre-mapped exec command')
    parser_migratealertesc.add_argument('--postexec', required=False, help='Post-mapped exec command')
    parser_migratealertesc.add_argument('--to_env', required=True, help='Target environment to which policy definitions will be migrated.  (--env option defines the source/from environment)')
    parser_migratealertesc.add_argument('--test', action='store_true', help='Test run only.  Will check object mappings for missing items and not actually change the target instance.')
    parser_migratealertesc.add_argument('--update', action='store_true', help='Used for bulk updates, will only work if --env and --to_env are the same.  Try to update existing policies instead of creating new ones.')
    parser_migratealertesc.add_argument('--setactive', required=False, help='Specify ON or OFF.  Will force all policies created on the target to be ON or OFF.  Otherwise will be set the same as the source.')

    # Device Management Policies get_device_management_policies
    parser_getdevmgtpol = subparsers.add_parser('getdevmgtpol', parents=[env_parser], formatter_class=argparse.ArgumentDefaultsHelpFormatter, help="Search and get Escalation Policy definitions")
    parser_getdevmgtpol.add_argument('--query', required=False, help='Query String to filter alerts')
    parser_getdevmgtpol.add_argument('--details', action='store_true', help='Get the full details for all matched policies')
    parser_getdevmgtpol.add_argument('--count', action='store_true', help='Only show the count of matching alerts')
    parser_getdevmgtpol.add_argument('--filter', required=False, help='Post-query filter on alerts.  Python expression that will evaluate to True or False such as alert["resource"]["name"].startswith("prod")')


    # Templates

    parser_gettemplates = subparsers.add_parser('gettemplates', parents=[env_parser], formatter_class=argparse.ArgumentDefaultsHelpFormatter, help="Clone monitoring templates")
    parser_gettemplates.add_argument('--query', help="Query search criteria")
    parser_gettemplates.add_argument('--brief', action='store_true', help='Output only the template names not the full definitions')

    parser_clonetemplates = subparsers.add_parser('clonetemplates', parents=[env_parser], formatter_class=argparse.ArgumentDefaultsHelpFormatter, help="Clone monitoring templates")
    parser_clonetemplates_src = parser_clonetemplates.add_mutually_exclusive_group(required=True)
    parser_clonetemplates_src.add_argument('--name', help="Name of the Monitoring Template to clone")
    parser_clonetemplates_src.add_argument('--infile', help="File containing list of templates to clone (requires use of --prefix option)")
    parser_clonetemplates_target = parser_clonetemplates.add_mutually_exclusive_group(required=True)
    parser_clonetemplates_target.add_argument('--prefix', help="New template name will be same as original name but with this text prepended")
    parser_clonetemplates_target.add_argument('--copyname', help="New template will have this as its name")

    # Monitoring and Metrics

    parser_metricsql = subparsers.add_parser('metricsql', parents=[env_parser], formatter_class=argparse.ArgumentDefaultsHelpFormatter, help="Run a MetricsQL/PromQL query")
    parser_metricsql.add_argument('--instant_query', help="MetricsQL/PromQL Query")

    parser_setbaselinethreshold = subparsers.add_parser('setbaselinethreshold', parents=[env_parser], formatter_class=argparse.ArgumentDefaultsHelpFormatter, help="Set a new override threshold for a resource/component that matches a given MetricQL query")
    parser_setbaselinethreshold.add_argument('--template', required=True, help="Name of template that metric is assigned from")
    parser_setbaselinethreshold.add_argument('--metric', required=True, help="Technical metric name as listed in the template definition") 
    parser_setbaselinethreshold.add_argument('--instant_query', required=True, help="PromQL instant query returning a vector result (i.e. must aggregate over time)")
    parser_setbaselinethreshold.add_argument('--warnop', choices=('NONE', 'LESS_THAN', 'LESS_THAN_EQUAL', 'EQUAL', 'GREATER_THAN_EQUAL', 'GREATER_THAN'), help="Comparison operator for Warning")
    parser_setbaselinethreshold.add_argument('--critop', choices=('NONE', 'LESS_THAN', 'LESS_THAN_EQUAL', 'EQUAL', 'GREATER_THAN_EQUAL', 'GREATER_THAN'), help="Comparison operator for Warning")
    parser_setbaselinethreshold.add_argument('--warnthresh', type=float, help='Warning threshold value')
    parser_setbaselinethreshold.add_argument('--critthresh', type=float, help='Critical threshold value')
    parser_setbaselinethreshold.add_argument('--warnrepeat', type=int, default=1, help='Warning repeat count')
    parser_setbaselinethreshold.add_argument('--critrepeat', type=int, default=1, help='Critical repeat count')
    parser_setbaselinethreshold.add_argument('--raisealert', required=True, choices=('on', 'off'), help='Whether to raise an alert or not')
    parser_setbaselinethreshold.add_argument('--availability', action='store_true', help='Make the metric an availability metric')

    # Integrations
    parser_getintegrations = subparsers.add_parser('getintegrations', parents=[env_parser], formatter_class=argparse.ArgumentDefaultsHelpFormatter, help="Get installed Integration definitions")
    parser_getintegrations.add_argument('--query', required=False, help='Query String to filter integrations')
    parser_getintegrations.add_argument('--filter', required=False, help='Post-query filter.  Python expression that will evaluate to True or False such as record["integration"]["name"] == "JIRA"')

    parser_importintegrations = subparsers.add_parser('importintegrations', parents=[env_parser], formatter_class=argparse.ArgumentDefaultsHelpFormatter, help="Import integration definitions from a json file")
    parser_importintegrations.add_argument('--file', required=True, help='JSON file containing integration definition or array of definitions')

    # Discovery schedule options for cloud integrations
    discp_parser = argparse.ArgumentParser(add_help=False, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    discp = discp_parser.add_argument_group(title="Specify discovery schedule")
    discp.add_argument('--recurrence', default='WEEKLY', choices=('WEEKLY','DAILY','NONE'), help='Recurrence type for discovery schedule')
    discp.add_argument('--daysofweek', default='sunday,', help='Comma-separated list of days of week used for WEEKLY recurrence')
    discp.add_argument('--starthour', default=2, help='Hour of day to start discovery')
    discp.add_argument('--rules', default="ANY_CLOUD_RESOURCE", help='Comma-delimited list of rules to filter what object types are discovered and managed')

    # Azure Integrations
    parser_addazurearmintegration = subparsers.add_parser('addazurearmintegration', parents=[env_parser,discp_parser], formatter_class=argparse.ArgumentDefaultsHelpFormatter, help="Install a new Azure ARM integration")
    parser_addazurearmintegration.add_argument('--azname', required=True, help='displayName for the integration')
    parser_addazurearmintegration.add_argument('--azsub', required=True, help='Azure Subscription ID')
    parser_addazurearmintegration.add_argument('--aztenant', required=True, help='Azure Tenant ID')
    parser_addazurearmintegration.add_argument('--azclient', required=True, help='Azure Client ID')
    parser_addazurearmintegration.add_argument('--azsecret', required=True, help='Azure Secret Key')

    parser_addazureasmintegration = subparsers.add_parser('addazureasmintegration', parents=[env_parser,discp_parser], formatter_class=argparse.ArgumentDefaultsHelpFormatter, help="Install a new Azure ASM integration")
    parser_addazureasmintegration.add_argument('--azname', required=True, help='displayName for the integration')
    parser_addazureasmintegration.add_argument('--azsub', required=True, help='Azure Subscription ID')
    parser_addazureasmintegration.add_argument('--azcert', required=True, help='Azure Management Certificate')
    parser_addazureasmintegration.add_argument('--azkspw', required=True, help='Azure Keystore Password')

    # Kubernetes Integrations
    parser_addkubernetesintegration = subparsers.add_parser('addkubernetesintegration', parents=[env_parser], formatter_class=argparse.ArgumentDefaultsHelpFormatter, help="Install a new Kubernetes integration")
    parser_addkubernetesintegration.add_argument('--name', required=True, help='Name for the integration, or if prefixed with @ a text file with a list of names.')
    parser_addkubernetesintegration.add_argument('--type', choices=('cloud','onPrem'), required=True, help='Kubernetes deployment type')
    parser_addkubernetesintegration.add_argument('--engine', required=True, choices=('Docker','ContainerD','CRI-O'), help='Container engine type')

    return parser

def do_arg_parsing():
    parser = setup_arg_parsing()
    args = parser.parse_args()
    if hasattr(args, 'query') and args.query == getalerts_default_query:
        print(f'No --query option has been specified, defaulting to {getalerts_default_query} (i.e. 1 hour ago)')
    return args