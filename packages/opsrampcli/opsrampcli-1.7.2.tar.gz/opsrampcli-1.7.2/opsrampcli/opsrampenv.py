from genericpath import exists
import aiohttp.client_exceptions
import aiohttp.http_exceptions
import yaml
import sys
import requests
from requests.exceptions import HTTPError
import json
import time
from http import HTTPStatus
from datetime import datetime
import logging
import aiohttp
import asyncio
import copy

logger = logging.getLogger(__name__)

class OpsRampEnvException(Exception):
    """Base class for exceptions in this module"""
    pass

class OpsRampApiThrottled(OpsRampEnvException):
    pass

class OpsRampApiMaxRetriesExceeded(OpsRampEnvException):
    pass

class OpsRampEnv:

    MAX_NEW_CUSTOM_ATTR_VALUES = 50

    OPS_ALERT_SEARCH_ATTRIBUTES = [
        'states',
        'startDate',
        'endDate',
        'priority',
        'uniqueId',
        'deviceStatus',
        'resourceType',
        'resourceIds',
        'actions',
        'alertTypes',
        'metrics',
        'duration',
        'alertTimeBase',
        'clientIds',
        'ticketId',
        'apps'
    ]


    def __init__(self, env, isSecure=True):
        self.env = env
        self.isSecure = True
        if isinstance(isSecure, str) and (isSecure.lower() == 'false' or isSecure.lower() == 'no' or isSecure == '0'):
            self.isSecure = False
        self.token:str = None
        self.token_expire_time:float = 0
        self._session:aiohttp.ClientSession = None
        self._queue:asyncio.Queue = None

    def async_session(self):
        if not self._session:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def close_async_session(self):
        logger.debug('OpsRampEnv.close_async_session called')
        if self._session:
            logger.debug('Attempting to close async session...')
            await self._session.close()
            logger.debug('Async session closed.')
        else:
            logger.debug('No async session was created, no need to close.')

    def async_queue(self):
        if not self._queue:
            self._queue = asyncio.Queue()
        return self._queue


    async def post_object_async(self, path, obj, no_retry_on_code=None):
        logger.debug(f'OpsRampEnv.post_object_async called - path:{path} obj:{obj}')

        url = self.env['url'] + path
        retry_codes = [
            HTTPStatus.TOO_MANY_REQUESTS,
            HTTPStatus.INTERNAL_SERVER_ERROR,
            HTTPStatus.BAD_GATEWAY,
            HTTPStatus.SERVICE_UNAVAILABLE,
            HTTPStatus.GATEWAY_TIMEOUT,
        ]
        max_retries = 10
        sleep_interval = 5

        for attempt in range(max_retries):
            try:
                token = await self.get_token_async()
                headers = {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'Authorization': f'Bearer {token}',
                    'user-agent': 'opsrampcli'
                }
                async with self.async_session().post(url, headers=headers, json=obj, ssl=self.isSecure) as response:
                    response_text = await response.text()
                    logger.debug(f'OpsRampEnv.post_object POST response - response: {response} response.text: {response_text} response.headers: {response.headers}')
                    
                    if response.status not in retry_codes:
                        response.raise_for_status()
                        return await response.json()

                    if no_retry_on_code and response.status in no_retry_on_code:
                        logger.warning(f'OpsRampEnv.post_object returning no_retry_on_code_occurred response due to {response.status} response.')
                        return {
                            "no_retry_on_code_occurred": response.status,
                            "exception": f"HTTP status code {response.status}"
                        }

            except aiohttp.ClientError as exc:
                if no_retry_on_code and response and response.status and response.status in no_retry_on_code:
                    logger.warning(f'OpsRampEnv.post_object returning no_retry_on_code_occurred response due to {response.status} response.')
                    return {
                        "no_retry_on_code_occurred": response.status,
                        "exception": f"HTTP status code {response.status}"
                    }
                logger.warning(f'OpsRampEnv.post_object POST Exception on attempt {attempt + 1}. Retry in {sleep_interval} sec...', exc_info=exc)
                await asyncio.sleep(sleep_interval)

                # Raise an exception if all retries fail
                if attempt >= max_retries:
                    logger.error(f'OpsRampEnv.post_object failed after maximum retries.')
                    raise OpsRampApiMaxRetriesExceeded('Failed to post object after {max_retries} retries.')

        if 'x-ratelimit-remaining' in response.headers and int(response.headers['x-ratelimit-remaining']) < 2:
            reset_time = int(response.headers['x-ratelimit-reset'])
            current_time = int(datetime.now().timestamp())
            sleeptime = abs(reset_time - current_time + 3)
            if sleeptime > 60:
                sleeptime %= 60

            logger.warning(f'Sleeping for {sleeptime} sec to wait for API throttling limit to reset..')
            await asyncio.sleep(sleeptime)

        try:
            return await response.json()
        except aiohttp.ContentTypeError:
            return {'success': response.ok, 'text': response_text}

    async def close(self):
        await self.async_session().close()




    def post_object(self, path, obj, no_retry_on_code=None):
        logger.debug(f'OpsRampEnv.post_object called - path:{path} obj:{obj}')

        url = self.env['url'] + path

        retries = 3
        retry_codes = [
            HTTPStatus.TOO_MANY_REQUESTS,
            HTTPStatus.INTERNAL_SERVER_ERROR,
            HTTPStatus.BAD_GATEWAY,
            HTTPStatus.SERVICE_UNAVAILABLE,
            HTTPStatus.GATEWAY_TIMEOUT,
        ]
        response:requests.Response
        tries = 0
        while tries < 5:
            tries += 1
            try:
                token = self.get_token()
                headers = {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'Authorization': 'Bearer ' + token,
                    'user-agent': 'opsrampcli'
                }
                response = requests.request("POST", url, headers=headers, data=json.dumps(obj), verify=self.isSecure)
                logger.debug(f'OpsRampEnv.post_object POST response - response:{response} response.text:{response.text} response.headers:{response.headers}')
                response.raise_for_status()
                break
            except Exception as exc:
                if no_retry_on_code and hasattr(exc, 'response') and hasattr(exc.response, 'status_code') and exc.response.status_code in no_retry_on_code:
                    logger.warn(f'OpsRampEnv.post_object returning no_retry_on_code_occurred response due to {exc.response.status_code} response: {exc.response.text}.')
                    return {
                        "no_retry_on_code_occurred": exc.response.status_code,
                        "exception": exc
                    }
                logger.warning(f'OpsRampEnv.post_object POST Exception on try #{tries} .  Retry in 5 sec...', exc_info=exc)
                time.sleep(5)
                continue

        if 'x-ratelimit-remaining' in response.headers and int(response.headers['x-ratelimit-remaining']) < 2 :
            sleeptime = abs(int(response.headers['x-ratelimit-reset']) - int(datetime.now().timestamp()) + 3)
            if sleeptime > 60:
                sleeptime = sleeptime % 60

            logger.warning(f'Sleeping for {str(sleeptime)} sec to wait for API throttling limit to reset..')
            time.sleep(sleeptime)
        try:    
            return response.json()
        except Exception as e:
            return {'success': response.ok, 'text': response.text}

    def put_object(self, path, obj):
        logger.debug(f'OpsRampEnv.put_object called - path:{path} obj:{obj}')
        token = self.get_token()
        url = self.env['url'] + path
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + token,
            'user-agent': 'opsrampcli'
        }
        response = requests.request("PUT", url, headers=headers, data=json.dumps(obj), verify=self.isSecure)
        logger.debug(f'OpsRampEnv.put_object POST response - response:{response} response.text:{response.text} response.headers:{response.headers}')

        if 'x-ratelimit-remaining' in response.headers and int(response.headers['x-ratelimit-remaining']) < 2 :
            sleeptime = abs(int(response.headers['x-ratelimit-reset']) - int(datetime.now().timestamp()) + 3)
            if sleeptime > 60:
                sleeptime = sleeptime % 60
            logger.warning(f'Sleeping for {str(sleeptime)} sec to wait for API throttling limit to reset..')
            time.sleep(sleeptime)
        try:    
            return response.json()
        except Exception as e:
            return {'success': response.ok, 'text': response.text}
        
    def get_with_pagination(self, path:str, result_array_key:str='results', params:dict={}, page_no:int=1, page_size:int=500):
        logger.debug(f'OpsRampEnv.get_with_pagination called - path:{path} result_array_key:{result_array_key} params:{params} page_no:{page_no} page_size:{page_size}')
        token = self.get_token()
        url = self.env['url'] + path
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + token,
            'user-agent': 'opsrampcli'
        }

        params['pageSize'] =  page_size
        params['pageNo'] = page_no

        
        response = requests.request("GET", url, headers=headers, params=params, verify=self.isSecure)
        logger.debug(f'OpsRampEnv.get_with_pagination GET response - response:{response} response.text:{response.text} response.headers:{response.headers}')

        if 'x-ratelimit-remaining' in response.headers and int(response.headers['x-ratelimit-remaining']) < 2 :
            sleeptime = abs(int(response.headers['x-ratelimit-reset']) - int(datetime.now().timestamp()) + 3)
            if sleeptime > 60:
                sleeptime = sleeptime % 60
            logger.warning(f'Sleeping for {str(sleeptime)} sec to wait for API throttling limit to reset..')
            time.sleep(sleeptime)
        bodydict = response.json()
        results = []
        if result_array_key in bodydict:
            results = bodydict[result_array_key]
        if 'nextPage' in bodydict and bodydict['nextPage']:
            return results + self.get_with_pagination(path=path, result_array_key=result_array_key, params=params, page_no=page_no+1, page_size=page_size)
        else:
            return results

    async def do_opsql_query_async(self, object_type:str, fields:list=None, filter_criteria:str=None, aggregate:str=None, group_by:list=None, sort_by:str=None, page_no:int=1, page_size:int=1000):
        logger.info(f'Getting page {page_no}...')
        url = f'/opsql/api/v3/tenants/{self.env["tenant"]}/queries'
        payload = {}
        payload['objectType'] = object_type
        if fields:
            payload['fields'] = fields
        if filter_criteria: 
            payload['filterCriteria'] = filter_criteria
        if aggregate:
            payload['aggregateFunction'] = aggregate
        if group_by or (group_by == []):
            payload['groupBy'] = group_by
        if sort_by:
            payload['sortBy'] = sort_by
        if page_no:
            payload['pageNo'] = page_no
        if page_size:
            payload['pageSize'] = page_size

        bodydict = await self.post_object_async(url, payload)
        results = []
        if 'results' in bodydict:
            results = bodydict['results']
            logger.info(f'Got {len(results)} records for page {page_no}.')
        if 'nextPage' in bodydict and bodydict['nextPage']:
            results = results + await self.do_opsql_query_async(object_type, fields, filter_criteria, aggregate, group_by, sort_by, page_no+1, page_size)
        return results 

    def do_opsql_query(self, object_type:str, fields:list=None, filter_criteria:str=None, aggregate:str=None, group_by:list=None, sort_by:str=None, page_no:int=1, page_size:int=1000):
        url = f'/opsql/api/v3/tenants/{self.env["tenant"]}/queries'
        payload = {}
        payload['objectType'] = object_type
        if fields:
            payload['fields'] = fields
        if filter_criteria: 
            payload['filterCriteria'] = filter_criteria
        if aggregate:
            payload['aggregateFunction'] = aggregate
        if group_by or (group_by == []):
            payload['groupBy'] = group_by
        if sort_by:
            payload['sortBy'] = sort_by
        if page_no:
            payload['pageNo'] = page_no
        if page_size:
            payload['pageSize'] = page_size

        bodydict = self.post_object(url, payload)
        results = []
        if 'results' in bodydict:
            results = bodydict['results']
        if 'nextPage' in bodydict and bodydict['nextPage']:
            results = results + self.do_opsql_query(object_type, fields, filter_criteria, aggregate, group_by, sort_by, page_no+1, page_size)
        return results
            



    def do_instant_metric_query(self, query):
        url = f'/metricsql/api/v7/tenants/{self.env["tenant"]}/metrics/latest'
        payload = {
            "query": query 
        }
        metrics_instant_query_response = self.post_object(url, payload)
        if 'status' in metrics_instant_query_response and metrics_instant_query_response['status'] == 'success':
            return metrics_instant_query_response['data']['result']
        else:
            raise Exception(json.stringify(metrics_instant_query_response))
        
    def do_resource_threshold_assign_multi(self, resource_id, object):
        url = f'/api/v3/tenants/{self.env["tenant"]}/resource/{resource_id}/thresholds'
        return self.put_object(url, object)
    
    def get_device_management_policies(self):
        return self.get_objects("deviceManagementPolicies")

    async def get_objects_async(self, obtype, page=1, queryString=None, searchQuery=None,countonly=False, itemId=None, filter=None, no_retry_on_code:list=None):
        logger.debug(f'OpsRampEnv.get_objects called - obtype:{obtype} page:{page} queryString:{queryString} searchQuery:{searchQuery} countonly:{countonly} itemId:{itemId} filter:{filter}')
   
        # Moved to v3 API
        if obtype == "customAttributes":
            return self.get_tags(filter_criteria=searchQuery)


        endpoints = {
            "clients": self.env['partner'] + "/clients/" + self.env['tenant'],
            "incidentCustomFields": self.env['tenant'] + "/customFields/INCIDENT",
            "deviceGroups": self.env['tenant'] + "/deviceGroups/minimal",
            "userGroups": self.env['tenant'] + "/userGroups",
            "urgencies": self.env['tenant'] + "/incidents/urgencies",
            "customAttributes": self.env['tenant'] + "/customAttributes/search",
            "resources": self.env['tenant'] + "/resources/search",
            "resourcesNewSearch": self.env['tenant'] + "/query/execute",
            "assignedAttributeEntities": self.env['tenant'] + "/customAttributes/" + str(itemId) + "/assignedEntities/search",
            "serviceMaps": self.env['tenant'] + "/serviceGroups/search",
            "childServiceGroups": self.env['tenant'] + "/serviceGroups/" + str(itemId) + "/childs/search",
            "serviceGroup": self.env['tenant'] + "/serviceGroups/" + str(itemId),
            "templates": self.env['tenant'] + "/monitoring/templates/search",
            "integration": self.env['tenant'] + "/integrations/installed/" + str(itemId),
            "integrations": self.env['tenant'] + "/integrations/installed/search",
            "incident": f'{self.env["tenant"]}/incidents/{itemId}',
            "deviceManagementPolicies": f'{self.env["tenant"]}/policies/management'
        }

        url = self.env['url'] + "/api/v2/tenants/" + endpoints[obtype]
 
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + token,
            'user-agent': 'opsrampcli'
        }

        params = {
            'pageSize': 500,
            'pageNo': page
        }

        if countonly:
            params['pageSize'] = 1

        if queryString:
            params['queryString'] = queryString

        if searchQuery:
            params['searchQuery'] = searchQuery
            params['type'] = "resources"

        if obtype in ['userGroups', 'serviceMaps', 'integrations']:
            params['pageSize'] = 100

#########
        max_retries = 3
        sleep_interval = 5

        for attempt in range(max_retries):
            token = await self.get_token_async()
            try:
                retry_codes = [
                    HTTPStatus.TOO_MANY_REQUESTS,
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    HTTPStatus.BAD_GATEWAY,
                    HTTPStatus.SERVICE_UNAVAILABLE,
                    HTTPStatus.GATEWAY_TIMEOUT,
                ]

                async with self.async_session().get(url, headers=headers, params=params, ssl=self.isSecure) as response:
                    response_text = await response.text()
                    logger.debug(f'OpsRampEnv.get_objects GET response - response:{response} response.text:{response_text} response.headers:{response.headers}')

                    if 'x-ratelimit-remaining' in response.headers and int(response.headers['x-ratelimit-remaining']) < 2 :
                        sleeptime = abs(int(response.headers['x-ratelimit-reset']) - int(datetime.now().timestamp()) + 3)
                        if sleeptime > 60:
                            sleeptime = sleeptime % 60
                        logger.warning(f'Sleeping for {str(sleeptime)} sec to wait for API throttling limit to reset..')
                        time.sleep(sleeptime)
                    try:
                        responseobj = await response.json()
                    except Exception as e:
                        logger.error(repr(response))
                        sys.exit(1)

                    if countonly:
                        return int(responseobj['totalResults'])

                    if "results" in responseobj:
                        results = responseobj['results']
                    else:
                        results = responseobj
            
                    if filter and (type(results) == list):
                        results[:] = [record for record in results if (eval(filter))]

                    if "nextPage" in responseobj and responseobj['nextPage']:
                        return results + await self.get_objects_async(obtype=obtype, page=responseobj['nextPageNo'],queryString=queryString, searchQuery=searchQuery, itemId=itemId, filter=filter)
                    else:
                        return results

            except aiohttp.ClientError as exc:
                logger.warning(f'OpsRampEnv.get_object_async GET Exception on attempt {attempt + 1}. Retry in {sleep_interval} sec...', exc_info=exc)
                await asyncio.sleep(sleep_interval)

                # Raise an exception if all retries fail
                if attempt >= max_retries:
                    logger.error(f'OpsRampEnv.get_object_async failed after maximum retries.')
                    raise OpsRampApiMaxRetriesExceeded('Failed to post object after {max_retries} retries.')

            if 'x-ratelimit-remaining' in response.headers and int(response.headers['x-ratelimit-remaining']) < 2:
                reset_time = int(response.headers['x-ratelimit-reset'])
                current_time = int(datetime.now().timestamp())
                sleeptime = abs(reset_time - current_time + 3)
                if sleeptime > 60:
                    sleeptime %= 60

                logger.warning(f'Sleeping for {sleeptime} sec to wait for API throttling limit to reset..')
                await asyncio.sleep(sleeptime)

            try:
                return await response.json()
            except aiohttp.ContentTypeError:
                return {'success': response.ok, 'text': response_text}



#########






    def get_objects(self, obtype, page=1, queryString=None, searchQuery=None,countonly=False, itemId=None, filter=None):
        logger.debug(f'OpsRampEnv.get_objects called - obtype:{obtype} page:{page} queryString:{queryString} searchQuery:{searchQuery} countonly:{countonly} itemId:{itemId} filter:{filter}')
   
        # Moved to v3 API
        if obtype == "customAttributes":
            return self.get_tags(filter_criteria=searchQuery)


        endpoints = {
            "clients": self.env['partner'] + "/clients/" + self.env['tenant'],
            "incidentCustomFields": self.env['tenant'] + "/customFields/INCIDENT",
            "deviceGroups": self.env['tenant'] + "/deviceGroups/minimal",
            "userGroups": self.env['tenant'] + "/userGroups",
            "urgencies": self.env['tenant'] + "/incidents/urgencies",
            "customAttributes": self.env['tenant'] + "/customAttributes/search",
            "resources": self.env['tenant'] + "/resources/search",
            "resourcesNewSearch": self.env['tenant'] + "/query/execute",
            "assignedAttributeEntities": self.env['tenant'] + "/customAttributes/" + str(itemId) + "/assignedEntities/search",
            "serviceMaps": self.env['tenant'] + "/serviceGroups/search",
            "childServiceGroups": self.env['tenant'] + "/serviceGroups/" + str(itemId) + "/childs/search",
            "serviceGroup": self.env['tenant'] + "/serviceGroups/" + str(itemId),
            "templates": self.env['tenant'] + "/monitoring/templates/search",
            "integration": self.env['tenant'] + "/integrations/installed/" + str(itemId),
            "integrations": self.env['tenant'] + "/integrations/installed/search",
            "incident": f'{self.env["tenant"]}/incidents/{itemId}',
            "deviceManagementPolicies": f'{self.env["tenant"]}/policies/management'
        }

        url = self.env['url'] + "/api/v2/tenants/" + endpoints[obtype]
        token = self.get_token()
 
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + token,
            'user-agent': 'opsrampcli'
        }

        params = {
            'pageSize': 500,
            'pageNo': page
        }

        if countonly:
            params['pageSize'] = 1

        if queryString:
            params['queryString'] = queryString

        if searchQuery:
            params['searchQuery'] = searchQuery
            params['type'] = "resources"

        if obtype in ['userGroups', 'serviceMaps', 'integrations']:
            params['pageSize'] = 100

        response = requests.request("GET", url, headers=headers, verify=self.isSecure, params=params)
        logger.debug(f'OpsRampEnv.get_objects GET response - response:{response} response.text:{response.text} response.headers:{response.headers}')

        if 'x-ratelimit-remaining' in response.headers and int(response.headers['x-ratelimit-remaining']) < 2 :
            sleeptime = abs(int(response.headers['x-ratelimit-reset']) - int(datetime.now().timestamp()) + 3)
            if sleeptime > 60:
                sleeptime = sleeptime % 60
            logger.warning(f'Sleeping for {str(sleeptime)} sec to wait for API throttling limit to reset..')
            time.sleep(sleeptime)
        try:
            responseobj = response.json()
        except Exception as e:
            logger.error(repr(response))
            sys.exit(1)

        if countonly:
            return int(responseobj['totalResults'])

        if "results" in responseobj:
            results = responseobj['results']
        else:
            results = responseobj
 
        if filter and (type(results) == list):
            results[:] = [record for record in results if (eval(filter))]

        if "nextPage" in responseobj and responseobj['nextPage']:
            return results + self.get_objects(obtype=obtype, page=responseobj['nextPageNo'],queryString=queryString, searchQuery=searchQuery, itemId=itemId, filter=filter)
        else:
            return results

    def get_integrations(self, queryString=None, filter=None):
        return self.get_objects("integrations", queryString=queryString, filter=filter)

    def add_integration(self, intname, obj):
        path = f'/api/v2/tenants/{self.env["tenant"]}/integrations/install/{intname}'
        return self.post_object(path, obj)


    def get_templates(self, queryString=None):
        return self.get_objects("templates", queryString=queryString)

    def clone_template(self, templateobj, newname, newdesc):
        token = self.get_token()
        url = f'{self.env["url"]}/api/v2/tenants/{self.env["tenant"]}/monitoring/templates/clone'
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + token,
            'user-agent': 'opsrampcli'
        }

        #removeattrs = ['id', 'uniqueId', 'name', 'createdDate', 'updatedDate', ]
        body = {}
        body['clonedTemplateId'] = templateobj['uniqueId']
        body['name'] = newname

        response = requests.request("POST", url, headers=headers, data=json.dumps(body), verify=self.isSecure)
        return response.json() 

    def get_service_maps(self, queryString=None):
        return self.get_objects("serviceMaps", queryString=queryString)

    def get_child_service_groups(self, sgId):
        return self.get_objects("childServiceGroups", itemId=sgId)

    def get_service_group(self, sgId):
        return self.get_objects("serviceGroup", itemId=sgId)

    def make_healing_alert(self, alert):
        newalert={}
        newalert['currentState'] = "Ok"
        newalert['device'] = alert['device']
        newalert['metric'] = alert['metric']
        newalert['component'] = alert['component']
        newalert['subject'] = "Heal via script for alert " + alert['uniqueId']
        newalert['description'] = "Healed via script"
        newalert['serviceName'] = alert['serviceName']
        newalert['problemArea'] = alert['problemArea']
        newalert['alertType'] = alert['alertType']
        newalert['app'] = alert['app']
        return newalert

    async def post_alert_bearer_async(self, alert):
        url = self.env['url'] + "/api/v2/tenants/" + self.env['tenant'] + "/alert"
        logger.debug("Sending alert: %s" % (json.dumps(alert)))
        return await self.post_object_async(url, alert)

    def post_alert_bearer(self, alert):
        url = "/api/v2/tenants/" + self.env['tenant'] + "/alert"
        logger.info("Sending: %s" % (json.dumps(alert)))
        return self.post_object(url, alert)


    def post_alert_vtoken(self, alert):
        url = self.env['url'] + "/integrations/alertsWebhook/" + self.env['tenant'] + "/alerts?vtoken=" + self.env['vtoken']
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        logger.info("Sending: %s" % (json.dumps(alert)))
        response = requests.request("POST", url, headers=headers, data=json.dumps(alert), verify=self.isSecure)
        return response.json()

    def is_in_range(self, range, i):
        ranges = range.split(",")
        for range in ranges:
            # all
            if range == 'all':
                return True
            
            # simple integer value    
            try:
                if i==(int(range)-1):
                    return True
            except:
                pass

            # from-to range
            fromto = range.split("-")
            if len(fromto) == 2:
                lower = fromto[0]
                upper = fromto[1]
                if ((lower == '') or int(lower) <= (i+1)) and  ((upper == '') or int(upper) >= (i+1)):
                    return True

        return False

    def get_alert(self,  alertid):
        token = self.get_token()
        url = self.env['url'] + "/api/v2/tenants/" + self.env['tenant'] + "/alerts/" + str(alertid)
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + token,
            'user-agent': 'opsrampcli'
        }
        params = {
        }

        response = requests.request("GET", url, headers=headers, params=params, verify=self.isSecure)
        responseobj = response.json()
        return responseobj


    def do_alert_action(self,  action, alertid):
        token = self.get_token()
        url = self.env['url'] + "/api/v2/tenants/" + self.env['tenant'] + "/alerts/" + str(alertid) + "/actions/" + action
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + token,
            'user-agent': 'opsrampcli'
        }

        data = {
            "description": action + " via script."
        }

        response = requests.request("POST", url, headers=headers, verify=self.isSecure, data = json.dumps(data))
        responseobj = { "status_code": 200}
        if response.status_code != 200:
            responseobj = response.json()
        return responseobj

    def validate_alert_query(self, query):
        invalid_search_attrs = set([a.split(":")[0] for a in query.split("+")]).difference(set(self.OPS_ALERT_SEARCH_ATTRIBUTES))
        if len(invalid_search_attrs) > 0:
            raise ValueError('Alert search query contains invalid search attributes: %s\nValid search attributes are: %s' % (invalid_search_attrs, self.OPS_ALERT_SEARCH_ATTRIBUTES))
        return True

    def get_alerts_count(self, query):
        self.validate_alert_query(query)
        token = self.get_token()
        url = self.env['url'] + "/api/v2/tenants/" + self.env['tenant'] + "/alerts/search"
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + token,
            'user-agent': 'opsrampcli'
        }

        params = {
            'queryString': query,
            'pageSize': 1
        }

        count = 0
        responseobj = {}
        try:
            response = requests.request("GET", url, headers=headers, params=params, verify=self.isSecure)
            responseobj = response.json()
            count = responseobj['totalResults']
        except Exception as e:
            logger.error(repr(responseobj))
            logger.error(repr(e))
            logger.error("Exception encountered.")
        return count



    def get_alerts(self, query, page=1, brief=False, details=False, filter=""):
        self.validate_alert_query(query)
        token = self.get_token()
        url = self.env['url'] + "/api/v2/tenants/" + self.env['tenant'] + "/alerts/search"
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + token,
            'user-agent': 'opsrampcli'
        }

        params = {
            'queryString': query,
            'pageNo': page,
            'pageSize': 500
        }

        got_result = False
        while not got_result:
            try:
                response = requests.request("GET", url, headers=headers, params=params, verify=self.isSecure)
                responseobj = response.json()
                results = responseobj['results']
                got_result = True
            except Exception as e:
                logger.error(repr(responseobj))
                logger.error(repr(e))
                logger.error("Exception on page %d.  Processing partial results." % (page))
                return []

        alerts = []
        if brief:
            for result in results:
                alerts.append({
                    'uniqueId': result['uniqueId'],
                    'createdDate': result['createdDate'],
                    'updatedTime': result['updatedTime'],
                    'app': result['app'],
                    'device': { 
                        'name': result['device']['name'],
                        'id': result['device'].get('id','NO_ID_FOUND')
                    },
                    'component': result['component'],
                    'metric': result['metric'],
                    'problemArea': result['problemArea'],
                    'subject': result['subject'],
                    'status': result['status'],
                    'eventType': result['eventType'],
                    'alertType': result['alertType'],
                    'currentState': result['currentState'],
                    'repeatCount': result['repeatCount']
                })
        else:
            alerts = results
        if details:
            for alert in alerts:
                details = self.get_alert(alert['uniqueId'])
                alert['description'] = details['description']

        if filter:
            for idx, alert in enumerate(alerts):
                if not eval(filter):
                   del alerts[idx] 

        if responseobj['nextPage']:
            return alerts + self.get_alerts(query, responseobj['nextPageNo'], brief, details, filter)
        else:
            return alerts

    def post_incident_update(self, id, update):
        path = "/api/v2/tenants/" + self.env['tenant'] + "/incidents/" + id
        logger.info("Updating %s: %s" % (id, json.dumps(update)))
        response = self.post_object(path, update, no_retry_on_code=[500])
        return response
 
    def get_incidents_count(self, query):
        token = self.get_token()
        url = self.env['url'] + "/api/v2/tenants/" + self.env['tenant'] + "/incidents/search"
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + token,
            'user-agent': 'opsrampcli'
        }

        params = {
            'queryString': query,
            'pageSize': 1
        }

        response = requests.request("GET", url, headers=headers, params=params, verify=self.isSecure)
        responseobj = response.json()
        return responseobj['totalResults']

    def get_incident(self, incidentId):
        return self.get_objects("incident", itemId=incidentId)

    def get_incidents(self, query, page=1, brief=False, details=False, filter=""):
        token = self.get_token()
        url = self.env['url'] + "/api/v2/tenants/" + self.env['tenant'] + "/incidents/search"
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + token,
            'user-agent': 'opsrampcli'
        }

        params = {
            'queryString': query,
            'pageNo': page
        }

        response = requests.request("GET", url, headers=headers, params=params, verify=self.isSecure)
        responseobj = response.json()
        results = responseobj['results']
        incidents = []
        if brief:
            for result in results:
                incidents.append({
                    'uniqueId': result['uniqueId'],
                    'createdDate': result['createdDate'],
                    'updatedTime': result['updatedTime'],
                    'device': { 
                        'name': result['device']['name'],
                        'id': result['device']['id']
                    },
                    'component': result['component'],
                    'metric': result['metric'],
                    'problemArea': result['problemArea'],
                    'subject': result['subject'],
                    'status': result['status'],
                    'eventType': result['eventType'],
                    'incidentType': result['incidentType'],
                    'currentState': result['currentState'],
                    'repeatCount': result['repeatCount']
                })
        else:
            incidents = results
        if details:
            for incident in incidents:
                details = self.get_incident(incident['id'])
                incident['description'] = details['description']
                incident['customFields'] = details['customFields']

        if filter:
            for idx, incident in enumerate(incidents):
                if not eval(filter):
                   del incidents[idx] 

        if responseobj['nextPage']:
            return incidents + self.get_incidents(query, responseobj['nextPageNo'], brief, details, filter)
        else:
            return incidents

    async def get_token_async(self):
        now_plus_30_sec = time.time() + 30
        if (not self.token) or (now_plus_30_sec >= self.token_expire_time):
            logger.debug(f'OpsRampEnv.get_token_async Token is expired, getting new one - old vals token:{self.token} expire_time:{self.token_expire_time} now_plus_30_sec:{now_plus_30_sec}')
            url = self.env['url'] + "/auth/oauth/token"

            payload = {
                'grant_type': 'client_credentials',
                'client_id': self.env['client_id'],
                'client_secret': self.env['client_secret']
            }
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json',
                'user-agent': 'opsrampcli'
            }

            async with self.async_session().post(url, headers=headers, data=payload, ssl=self.isSecure) as response:
                try:
                    response_json = await response.json()
                    self.token = response_json["access_token"]
                    self.token_expire_time = time.time() + float(response_json["expires_in"])

                except Exception as err:
                    logger.error('Exception occurred When trying to get auth token', exc_info=err)
                    sys.exit(1)
            
        else:
            logger.debug(f'OpsRampEnv.get_token Token is OK, re-using it - token:{self.token} expire_time:{self.token_expire_time} now_plus_30_sec:{now_plus_30_sec}')

        return self.token

    def get_token(self):
        now_plus_30_sec = time.time() + 30
        if (not self.token) or (now_plus_30_sec >= self.token_expire_time):
            logger.debug(f'OpsRampEnv.get_token Token is expired, getting new one - old vals token:{self.token} expire_time:{self.token_expire_time} now_plus_30_sec:{now_plus_30_sec}')
            url = self.env['url'] + "/auth/oauth/token"

            payload = {
                'grant_type': 'client_credentials',
                'client_id': self.env['client_id'],
                'client_secret': self.env['client_secret']
            }
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json',
                'user-agent': 'opsrampcli'
            }

            try:
                response = requests.request("POST", url, headers=headers, data=payload, verify=self.isSecure)
                response_json = response.json()
                self.token = response_json["access_token"]
                self.token_expire_time = time.time() + float(response_json["expires_in"])
            except requests.exceptions.ConnectionError as err:
                logger.error(f'When trying to get auth token, unable to connect to {url}: {err.response}')
                logger.error(f'Please check that this is the correct url and is resolvable/reachable!', exc_info=err)
                sys.exit(1)
            except Exception as err:
                logger.error('Exception occurred When trying to get auth token', exc_info=err)
                sys.exit(1)
            
            else:
                logger.debug(f'OpsRampEnv.get_token Token is OK, re-using it - token:{self.token} expire_time:{self.token_expire_time} now_plus_30_sec:{now_plus_30_sec}')

        return self.token

    def get_discoprofile(self, id, tenant):
        token = self.get_token()
        url = self.env['url'] + "/api/v2/tenants/" + tenant + "/policies/discovery/" + id
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + token,
            'user-agent': 'opsrampcli'
        }

        response = requests.request("GET", url, headers=headers, verify=self.isSecure)
        responseobj = response.json()
        return responseobj

    def get_alertescalations(self, query='', page=1):
        token = self.get_token()
        url = self.env['url'] + "/api/v2/tenants/" + self.env['tenant'] + "/escalations/search"
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + token,
            'user-agent': 'opsrampcli'
        }

        params = {
            "queryString": query,
            "pageSize": 500,
            "pageNo": page
        }

        response = requests.request("GET", url, headers=headers, verify=self.isSecure, params=params)
        try:
            responseobj = response.json()
        except Exception as e:
            logger.error(repr(response))
            sys.exit(1)

        if "results" in responseobj:
            results = responseobj['results']
        else:
            results = responseobj

        if "nextPage" in responseobj and responseobj['nextPage']:
            return results + self.get_alertescalations(query, responseobj['nextPageNo'])
        else:
            return results

    def get_alertescalation(self, allClients, id, params={}):
        for key, val in params.items():
            if val == True:
                params[key] = "true"
        token = self.get_token()
        tenant = self.env['tenant']
        if allClients:
            tenant = self.env['partner']
        url = self.env['url'] + "/api/v2/tenants/" + tenant + "/escalations/" + id
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + token,
            'user-agent': 'opsrampcli'
        }

        response = requests.request("GET", url, headers=headers, verify=self.isSecure, params=params)
        try:
            responseobj = response.json()
        except Exception as e:
            logger.error(repr(response))
            sys.exit(1)

        return responseobj

    
    def create_alertescalation(self, policy):
        token = self.get_token()
        url = self.env['url'] + "/api/v2/tenants/" + self.env['tenant'] + "/escalations"
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + token,
            'user-agent': 'opsrampcli'
        }

        response = requests.request("POST", url, headers=headers, data=json.dumps(policy), verify=self.isSecure)
        return response.json()

    def update_alertescalation(self, policy, id):
        token = self.get_token()
        url = self.env['url'] + "/api/v2/tenants/" + self.env['tenant'] + "/escalations/" + id
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + token,
            'user-agent': 'opsrampcli'
        }

        response = requests.request("POST", url, headers=headers, data=json.dumps(policy), verify=self.isSecure)
        return response.json()

    def get_tags(self, filter_criteria:str=None):
        return self.do_opsql_query(object_type='tag', fields=['name','id'], filter_criteria=filter_criteria)
    
    def create_tag(self, name:str, description:str=""):
        path = f'/api/v3/tenants/{self.env["tenant"]}/tags'
        newtag = self.post_object(path, [
            {
                "name": name,
                "description": description 
            }
        ])
        return newtag[0]['id']
    
    def get_tag_values(self, tag_id):
        path = f'/api/v3/tenants/{self.env["tenant"]}/tags/{tag_id}/values'
        return self.get_with_pagination(path)
    
    def update_tag_value(self, tag_id:str, value_id:str, description:str="", is_metric_label:bool=False ):
        path = f'/api/v3/tenants/{self.env["tenant"]}/tags/{tag_id}/values/{value_id}'
        obj = {
            "description": description,
            "metricLabel": is_metric_label            
        }
        resp = self.put_object(path, obj)
        return resp


    def add_custom_attr_value(self, attributeId, values, description="", is_metric_label:bool=False):
        if type(values) == str:
            values = [values]

        if len(values) > self.MAX_NEW_CUSTOM_ATTR_VALUES:
            results = []
            chunks = [values[i:i + self.MAX_NEW_CUSTOM_ATTR_VALUES] for i in range(0, len(values), self.MAX_NEW_CUSTOM_ATTR_VALUES)]
            for chunk in chunks:
                results += self.add_custom_attr_value(attributeId, chunk, description, is_metric_label)
            return results
        if type(description) == str:
            description = [description]
        if len(values) > len(description):
            for i in range(len(description), len(values)):
                description.append("")

        path = f'/api/v3/tenants/{self.env["tenant"]}/tags/{attributeId}/values'
        customAttributeValues = []
        for i,val in enumerate(values):
            customAttributeValues.append({
                    "value": val,
                    "description": description[i],
                    "metricLabel": is_metric_label
            })
        return self.post_object(path, customAttributeValues)

    async def unset_custom_attr_on_devices_async(self, attr_id, device_ids):
        url = f'/api/v3/tenants/{self.env["tenant"]}/tags/{attr_id}/untagged-entities'            
        devices = []
        if isinstance(device_ids, list):
            devices = device_ids
        elif isinstance(device_ids, str):
            devices.append(device_ids)
        else:
            raise TypeError("device_ids must be an array or a string") 
        payload = []
        for device in devices:
            payload.append({
                "entityType": "resource",
                "entityId": device})
        return await self.post_object_async(url,payload, no_retry_on_code=[404])
    
    def unset_custom_attr_on_devices(self, attr_id, device_ids):
        url = f'/api/v3/tenants/{self.env["tenant"]}/tags/{attr_id}/untagged-entities'            
        devices = []
        if isinstance(device_ids, list):
            devices = device_ids
        elif isinstance(device_ids, str):
            devices.append(device_ids)
        else:
            raise TypeError("device_ids must be an array or a string") 
        payload = []
        for device in devices:
            payload.append({
                "entityType": "resource",
                "entityId": device})
        return self.post_object(url,payload, no_retry_on_code=[404])

    async def set_custom_attr_on_devices_async(self, attr_id, value_id, device_ids, force_remove_old_value=True):
        logger.debug(f'OpsRampEnv.set_custom_attr_on_devices called:  {attr_id=} {value_id=} {device_ids=} {force_remove_old_value=}')
        devices = []
        if isinstance(device_ids, list):
            devices = device_ids
        elif isinstance(device_ids, str):
            devices.append(device_ids)
        else:
            raise TypeError("device_ids must be an array or a string") 

        payload = []
        for device in devices:
            payload.append({
                "entityType": "resource",
                "entityId": device
                })

        path = "/api/v3/tenants/" + self.env['tenant'] + "/tags/" + str(attr_id) + "/values/" + str(value_id) + "/tagged-entities"
        no_retry_on_code = None
        if force_remove_old_value:
            no_retry_on_code = [400]
        result = await self.post_object_async(path, payload, no_retry_on_code)
        if "no_retry_on_code_occurred" in result:
            logger.warn(f'OpsRampEnv.set_custom_attr_on_devices received 400 response, attempting old attribute removal.')
            await self.unset_custom_attr_on_devices_async(attr_id, device_ids)
            return await self.set_custom_attr_on_devices_async(attr_id, value_id, device_ids, force_remove_old_value)
        

    def set_custom_attr_on_devices(self, attr_id, value_id, device_ids, force_remove_old_value=True):
        logger.debug(f'OpsRampEnv.set_custom_attr_on_devices called:  {attr_id=} {value_id=} {device_ids=} {force_remove_old_value=}')
        devices = []
        if isinstance(device_ids, list):
            devices = device_ids
        elif isinstance(device_ids, str):
            devices.append(device_ids)
        else:
            raise TypeError("device_ids must be an array or a string") 

        payload = []
        for device in devices:
            payload.append({
                "entityType": "resource",
                "entityId": device
                })

        path = "/api/v3/tenants/" + self.env['tenant'] + "/tags/" + str(attr_id) + "/values/" + str(value_id) + "/tagged-entities"
        no_retry_on_code = None
        if force_remove_old_value:
            no_retry_on_code = [400]
        result = self.post_object(path, payload, no_retry_on_code)
        if "no_retry_on_code_occurred" in result:
            logger.warn(f'OpsRampEnv.set_custom_attr_on_devices received 400 response, attempting old attribute removal.')
            self.unset_custom_attr_on_devices(attr_id, device_ids)
            return self.set_custom_attr_on_devices(attr_id, value_id, device_ids, force_remove_old_value)

   

    def remove_custom_attr_from_devices(self, attr_id, value_id, device_ids):
        devices = []
        if isinstance(device_ids, list):
            devices = device_ids
        elif isinstance(device_ids, str):
            devices.append(device_ids)
        else:
            raise TypeError("device_ids must be an array or a string") 

        payload = []
        for device in devices:
            payload.append({"id": device})

        token = self.get_token()
        url = self.env['url'] + "/api/v2/tenants/" + self.env['tenant'] + "/customAttributes/" + str(attr_id) + "/values/" + str(value_id) + "/devices"
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + token,
            'user-agent': 'opsrampcli'
        }

        response = requests.request("DELETE", url, headers=headers, data=json.dumps(payload), verify=self.isSecure)
        return response.json() 

        
    def do_resource_action(self, action, resourceId):
        # Action is manage or unmanage
        token = self.get_token()
        url = f'{self.env["url"]}/api/v2/tenants/{self.env["tenant"]}/devices/{resourceId}/{action}'
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + token,
            'user-agent': 'opsrampcli'
        }

        response = requests.request("POST", url, headers=headers, verify=self.isSecure)
        responseobj = { "status_code": 200}
        if response.status_code != 200:
            responseobj = response.json()


        if int(response.headers['x-ratelimit-remaining']) < 2 :
            sleeptime = abs(int(response.headers['x-ratelimit-reset']) - int(datetime.now().timestamp()) + 3)
            if sleeptime > 60:
                sleeptime = sleeptime % 60
            logger.info(f'Sleeping for {str(sleeptime)} sec..')
            time.sleep(sleeptime)
        return responseobj

    def create_resource(self, resource_dict:dict):
        url = f'/api/v2/tenants/{self.env["tenant"]}/resources'
        return self.post_object(url, resource_dict)

    async def update_resource_async(self, resourceId:str, update_payload:dict):
        resource_dict:dict = copy.deepcopy(update_payload)
        try:
            del(resource_dict["resourceName"])
        except:
            pass
        try:
            del(resource_dict["tags"])
        except:
            pass
        path = f'/api/v2/tenants/{self.env["tenant"]}/resources/{resourceId}'
        retval = await self.post_object_async(path, resource_dict)

        return retval
    
    def update_resource(self, resourceId:str, resource_dict:dict):
        token = self.get_token()
        resourceName:str = resource_dict["resourceName"]
        try:
            del(resource_dict["resourceName"])
        except:
            pass
        try:
            del(resource_dict["tags"])
        except:
            pass
        path = f'/api/v2/tenants/{self.env["tenant"]}/resources/{resourceId}'
        retval = self.post_object(path, resource_dict)
        resource_dict["resourceName"] = resourceName
        return retval

    def delete_resource(self, resourceId):
        token = self.get_token()
        url = f'{self.env["url"]}/api/v2/tenants/{self.env["tenant"]}/resources/{resourceId}'
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + token,
            'user-agent': 'opsrampcli'
        }

        response = requests.request("DELETE", url, headers=headers, verify=self.isSecure)
        responseobj = { "status_code": 200}
        if response.status_code != 200:
            responseobj = response.json()


        if int(response.headers['x-ratelimit-remaining']) < 2 :
            sleeptime = abs(int(response.headers['x-ratelimit-reset']) - int(datetime.now().timestamp()) + 3)
            if sleeptime > 60:
                sleeptime = sleeptime % 60
            logger.info(f'Sleeping for {str(sleeptime)} sec..')
            time.sleep(sleeptime)
        return responseobj
    
    def create_or_update_service_group(self, svcgroup):
        if type(svcgroup) == list:
            for grp in svcgroup:
                self.create_or_update_service_group(grp)
        token = self.get_token()
        url = f'{self.env["url"]}/api/v2/tenants/{self.env["tenant"]}/serviceGroups/'
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + token,
            'user-agent': 'opsrampcli'
        }
        svcgrouparr = [svcgroup]
        response = requests.request("POST", url, headers=headers, verify=self.isSecure, data=json.dumps(svcgrouparr))
        responseobj = response.json()
        if type(responseobj) == list and len(responseobj) > 0:
            return responseobj[0]
        else:
            logger.error(f'Failed to import service group {svcgroup["name"]}:\n{response.json()}')
            return False

    def link_service_group(self, parent, child):
        token = self.get_token()
        url = f'{self.env["url"]}/api/v2/tenants/{self.env["tenant"]}/serviceGroups/link'
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + token,
            'user-agent': 'opsrampcli'
        }
        link = [
            {
                "id": child,
                "parent": {
                    "id": parent
                }
            }
        ]
        response = requests.request("POST", url, headers=headers, verify=self.isSecure, data=json.dumps(link))
        if response.status_code == 200:
            return True
        return False
