import requests
from opsrampcli.DataSource import DataSource
import pandas as pd
from datetime import datetime
import pytz
import os
import logging
import json

logger = logging.getLogger(__name__)


class ServiceNowDataSource(DataSource):
    SERVICENOW_DISPLAY_VALUE = 'display_value'

    class SnowDataSourceException(DataSource.DataSourceException):
        pass

    def get_resources_df(self):
        job = self.job
        instance_url = os.getenv("SERVICENOW_URL") or job['source']['servicenow']['instance_url']
        url = instance_url + f"/api/now/table/{job['source']['servicenow']['table']}"

        auth_type = os.getenv("SERVICENOW_AUTH_TYPE") or job.get('source', {}).get('servicenow', {}).get('auth', {}).get('type', "basic")
        logger.info(f"auth_type is set to {auth_type}")

        qstrings = {}
        query_parameters = job.get('source', {}).get('servicenow', {}).get('query_parameters', {})
        for k, v in query_parameters.items():
            qstrings[f'sysparm_{k}'] = v

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        user = os.getenv("SERVICENOW_USER") or job.get('source', {}).get('servicenow', {}).get('auth', {}).get('username')
        password = os.getenv("SERVICENOW_PASSWORD") or job.get('source', {}).get('servicenow', {}).get('auth', {}).get('password')

        if 'ssl_verify' in job['source']['servicenow'] and job['source']['servicenow']['ssl_verify'] == False:
            ssl_verify = False
        else:
            ssl_verify = True

        if auth_type == 'oauth2':
            logger.info("Using oauth2 authentication")
            grant_type = os.getenv("SERVICENOW_GRANT_TYPE") or job.get('source', {}).get('servicenow', {}).get('auth', {}).get('grant_type') or "password"
            client_id = os.getenv("SERVICENOW_CLIENT_ID") or job.get('source', {}).get('servicenow', {}).get('auth', {}).get('client_id')
            client_secret = os.getenv("SERVICENOW_CLIENT_SECRET") or job.get('source', {}).get('servicenow', {}).get('auth', {}).get('client_secret')
            scope = os.getenv("SERVICENOW_SCOPE") or job.get('source', {}).get('servicenow', {}).get('auth', {}).get('scope')
            token_url = os.getenv("SERVICENOW_TOKEN_URL") or job.get('source', {}).get('servicenow', {}).get('auth', {}).get('token_url') or f"{instance_url}/oauth_token.do"

            oauth_http_method = os.getenv("SERVICENOW_OAUTH_TOKEN_HTTP_METHOD") or job.get('source', {}).get('servicenow', {}).get('auth', {}).get('token_http_method') or "POST"
            oauth_token_attribute_name = os.getenv("SERVICENOW_OAUTH_TOKEN_ATTR_NAME") or job.get('source', {}).get('servicenow', {}).get('auth', {}).get('token_attr_name') or "access_token"

            oauth_payload = {
                "grant_type": grant_type,
                "client_id": client_id,
                "client_secret": client_secret,
            }
            if user:
                oauth_payload["username"] = user
            if password:
                oauth_payload["password"] = password
            if scope:
                oauth_payload["scope"] = scope

            oauth_get_token_headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }
            logger.info("Getting oauth2 token")
            oauth_response = requests.request(method=oauth_http_method, url=token_url, headers=oauth_get_token_headers, data=oauth_payload, verify=ssl_verify)
            oauth_response.raise_for_status()
            token = json.loads(oauth_response.content)[oauth_token_attribute_name]
            logger.info("Got oauth2 token")
            headers["Authorization"] = f"Bearer {token}"
            logger.info("Executing query")
            response = requests.get(url=url, params=qstrings, headers=headers, verify=ssl_verify)
        else:
            logger.info("Using basic authentication")
            auth = requests.auth.HTTPBasicAuth(user, password)
            logger.info("Executing query")
            response = requests.get(url=url, auth=auth, params=qstrings, headers=headers, verify=ssl_verify)

        response.raise_for_status()
        try:
            responsedict = response.json()
        except Exception as e:
            msg = f'Failed to retrieve records from ServiceNow datasource: {e}, {response.text}'
            raise ServiceNowDataSource.SnowDataSourceException(msg)
        records = responsedict.get('result', [])
        processed_recs = []
        for record in records:
            newrec = {}
            for key,value in record.items():
                if isinstance(value, dict) and ServiceNowDataSource.SERVICENOW_DISPLAY_VALUE in value:
                    newrec[key] = value[ServiceNowDataSource.SERVICENOW_DISPLAY_VALUE]
                else:
                    newrec[key] = value
            processed_recs.append(newrec)

        self.df = pd.DataFrame(processed_recs)

