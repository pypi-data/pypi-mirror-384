import requests
from requests_ntlm import HttpNtlmAuth
import pandas as pd
import os
import logging
import json
from opsrampcli.DataSource import DataSource

logger = logging.getLogger(__name__)

URLSOURCE_DISPLAY_VALUE = 'display_value'


class URLDataSource(DataSource):

    class URLDataSourceException(DataSource.DataSourceException):
        pass

    def get_resources_df(self):
        job = self.job

        try:
            auth_type = job['source']['urlsource']['auth']['type'] or "basic"
        except Exception as e:
            auth_type = "basic"

        logger.info(f"auth_type is set to {auth_type}")

        try:
            url = os.getenv("URLSOURCE_URL") or job['source']['urlsource']['url']
        except Exception as e:
            raise Exception("URLSOURCE_URL env var or source.urlsource.url in job file is required.")
        
        result_key = os.getenv("URLSOURCE_RESULT_KEY") or job.get('source', {}).get('urlsource', {}).get('result_key') or 'result'

        user = os.getenv("URLSOURCE_USER") or job.get('source', {}).get('urlsource', {}).get('auth', {}).get('username')
        password = os.getenv("URLSOURCE_PASSWORD") or job.get('source', {}).get('urlsource', {}).get('auth', {}).get('password')
       
        if 'ssl_verify' in job['source']['urlsource'] and job['source']['urlsource']['ssl_verify'] == False:
            ssl_verify = False
        else:
            ssl_verify = True

        qstrings = {}
        query_parameters = job.get('source', {}).get('urlsource', {}).get('query_parameters', {})
        for k, v in query_parameters.items():
            qstrings[f'{k}'] = v
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        if 'headers' in job['source']['urlsource'] and job['source']['urlsource']['headers']:
            headers = job['source']['urlsource']['headers']

        if auth_type == 'oauth2':
            logger.info("Using oauth2 authentication")
            grant_type = os.getenv("URLSOURCE_GRANT_TYPE") or job.get('source', {}).get('urlsource', {}).get('auth', {}).get('grant_type') or "password"
            client_id = os.getenv("URLSOURCE_CLIENT_ID") or job.get('source', {}).get('urlsource', {}).get('auth', {}).get('client_id')
            client_secret = os.getenv("URLSOURCE_CLIENT_SECRET") or job.get('source', {}).get('urlsource', {}).get('auth', {}).get('client_secret')
            scope = os.getenv("URLSOURCE_SCOPE") or job.get('source', {}).get('urlsource', {}).get('auth', {}).get('scope')
            token_url = os.getenv("URLSOURCE_TOKEN_URL") or job.get('source', {}).get('urlsource', {}).get('auth', {}).get('token_url') or f"{url}/oauth_token.do"

            oauth_http_method = os.getenv("URLSOURCE_OAUTH_TOKEN_HTTP_METHOD") or job.get('source', {}).get('urlsource', {}).get('auth', {}).get('token_http_method') or "POST"
            oauth_token_attribute_name = os.getenv("URLSOURCE_OAUTH_TOKEN_ATTR_NAME") or job.get('source', {}).get('urlsource', {}).get('auth', {}).get('token_attr_name') or "access_token"

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
            oauth_response = requests.request(method=oauth_http_method, url=token_url, headers=oauth_get_token_headers, data=oauth_payload)
            oauth_response.raise_for_status()
            token = json.loads(oauth_response.content)[oauth_token_attribute_name]
            logger.info("Got oauth2 token")
            headers["Authorization"] = f"Bearer {token}"
            logger.info("Executing query")
            response = requests.get(url=url, params=qstrings, headers=headers, verify=ssl_verify)

        else:
            if auth_type == 'basic':
                auth = requests.auth.HTTPBasicAuth(user, password)
            elif auth_type == 'ntlm':
                auth = HttpNtlmAuth(user, password)

            response = requests.get(url=url, auth=auth, params=qstrings, headers=headers, verify=ssl_verify)
        try:
            response.raise_for_status()
            responsedict = response.json()
        except Exception as e:
            msg = f'Failed to retrieve records from URL datasource: {e}'
            raise URLDataSource.URLDataSourceException(msg)
        records = responsedict.get(result_key, [])
        processed_recs = []
        for record in records:
            newrec = {}
            for key,value in record.items():
                if isinstance(value, dict) and URLSOURCE_DISPLAY_VALUE in value:
                    newrec[key] = value[URLSOURCE_DISPLAY_VALUE]
                else:
                    newrec[key] = value
            processed_recs.append(newrec)

        self.df = pd.DataFrame(processed_recs)
        self.df.fillna("", inplace=True)
