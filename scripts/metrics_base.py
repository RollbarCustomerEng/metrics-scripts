"""
A file with methods for commonly requireed functionality when working with teh Rollbar Metrics API

This file also includes stor light helper classes for storing metrics related data
"""


from http.client import HTTPException
import json
import logging
import requests


class Project:
    """
    A small class to store Rollbar Project details
    """

    def __init__(self):
        self.id = None
        self.name = None
        self.token = None


class ItemMetrics:
    """
    A class that stores matric data for an item
    """

    def __init__(self):
        
        self.project_id = None
        self.project_name = None
        self.start_time_unix = None
        self.end_time_unix = None

        self.id = None
        self.counter = None
        self.level = None
        self.status = None
        self.occurrence_count = None
        self.environment = None
        self.ip_address_count = None


def get_all_enabled_projects(account_read_token):
    """
    Arguments:
    account_read_token: An Account level acces token with Read scope
    
    Returns:
    A list with the project ids for all enabled projects in an account
    """

    url = 'https://api.rollbar.com/api/1/projects'
    headers = {'X-Rollbar-Access-Token': account_read_token}

    proj_list = []
    try:
        resp = requests.get(url, headers=headers)
        log = '/api/1/projects status={}'.format(resp.status_code)
        logging.info(log)

        dct = json.loads(resp.text)['result']

        for item in dct:
            if item['status'] == 'enabled':
                p = Project()
                p.id = item['id']
                p.name = item['name']
                proj_list.append(p)
        
    except Exception as ex:
        logging.error('Error making request to Rollbar Metrics API', exc_info=ex)

    return proj_list


def get_project_objects_with_token(proj_list, account_read_token, allowed_token_names):
    """ 


    Arguments:
    proj_list - List of partially initialized project objects
    account_read_token - An account level access token with Read scope
    allowed_token_names - List of alllowed token names. The allowed tokens must have Read scope ONLY
 
    Returns:
    proj_list: List of project objects with valid read token property
    """


    headers = {'X-Rollbar-Access-Token': account_read_token}


    proj_objs_with_token = []
    for proj in proj_list:
        url = 'https://api.rollbar.com/api/1/project/{}/access_tokens'
        url = url.format(proj.id)

        resp = requests.get(url, headers=headers)
        log = '{} /api/1/project/{}/access_tokens status={}'.format(proj.name, proj.id, resp.status_code)
        logging.info(log)

        token_list = json.loads(resp.text)['result']
        for token in token_list:
            if token['name'] in allowed_token_names and \
                 len(token['scopes']) == 1 and \
                 token['scopes'][0] == 'read':

                p = Project()
                p.id = proj.id
                p.name = proj.name
                p.token = token['access_token']
                proj_objs_with_token.append(p)
                continue

    return proj_objs_with_token


def get_project_objects(account_read_token, allowed_token_names):
    """
    Use this method to get a list of Project objects

    Arguments:
    account_read_token - An account level access token with Read scope
    allowed_token_names - Only a token with a name from the allowed list of names will be chosen
                          Note: The token will be accepted if it has Read scope ONLY

    Returns:
    List of Project objects with id, name, and read_access_token
    """

    p_list = get_all_enabled_projects(account_read_token)
    proj_list = get_project_objects_with_token(p_list, account_read_token, allowed_token_names)

    return proj_list

def make_occ_metrics_api_call(proj: Project, query_data):
    """
    Use this method to return the data for the query passed as an argument

    Arguments:
    proj - A Project object (Requires name and token properties to be set)
    query_data - A JSON object which defines the Metrics API query

    Returns:
    A dict with the Metrics API data
    """

    try:
        
        url = 'https://api.rollbar.com/api/1/metrics/occurrences'
        headers = {'X-Rollbar-Access-Token': proj.token, 'Content-Type': 'application/json'}

        # POST request
        resp = requests.post(url, json=query_data, headers=headers)
        log = '/api/1/metrics/occurrences proj={} status={}'.format(proj.name, resp.status_code)
        logging.info(log)

        result = json.loads(resp.text)['result']
        return result

    except Exception as ex:
        msg = 'Error making request to Rollbar Metrics API project={}'.format(proj.name)
        logging.error(msg, exc_info=ex)


def get_all_projects(account_read_token):
    """
    Use this method to get the list of Projects in an account

    Arguments:
    account_read_token - An Account level access token with Read scope

    Returns:
    List of Project object with id and name properties populated (Doesnt set the token property)
    """


    url = 'https://api.rollbar.com/api/1/projects'
    headers = {'X-Rollbar-Access-Token': account_read_token}

    proj_list = []
    try:
        resp = requests.get(url, headers=headers)
        log = '/api/1/projects status={}'.format(resp.status_code)
        logging.info(log)

        dct = json.loads(resp.text)['result']

        for item in dct:
            if item['status'] == 'enabled':
                p = Project()
                p.id = item['id']
                p.name = item['name']
                proj_list.append(p)
        
    except Exception as ex:
        logging.error('Error making request to Rollbar Metrics API', exc_info=ex)

    return proj_list


def add_read_token_to_projects(proj_list, account_read_token, allowed_project_token_names):
    #
    # For each project object in proj_list add the token property
    #

    headers = {'X-Rollbar-Access-Token': account_read_token}

    for proj in proj_list:
        url = 'https://api.rollbar.com/api/1/project/{}/access_tokens'
        url = url.format(proj.id)

        resp = requests.get(url, headers=headers)
        log = '{} /api/1/project/{}/access_tokens status={}'.format(proj.name, proj.id, resp.status_code)
        logging.info(log)

        token_list = json.loads(resp.text)['result']
        for token in token_list:
            if token['name'] in allowed_project_token_names and \
                 len(token['scopes']) == 1 and \
                 token['scopes'][0] == 'read':
                proj.token = token['access_token']
                continue


def add_extra_info_to_metrics(proj: Project, item_metrics: ItemMetrics):
    """
    Use this method to add additional data to the ItemMetrics object.
    This method adds teh following fields to a partially populated ItemMetrcs object:
    - title
    - assigned_user_id

    Arguments:
    proj - A Project obect (with the token and name properties set)
    item_metrics - A object with som emetrics for an Item already set
    """

    try:
        
        url = 'https://api.rollbar.com/api/1/item/{}'.format(item_metrics.id)
        headers = {'X-Rollbar-Access-Token': proj.token, 'Content-Type': 'application/json'}

        # GET request
        resp = requests.get(url, headers=headers)
        log = 'Get Item HTTP response status={}'.format(resp.status_code)
        logging.info(log)

        if resp.status_code == 200:
            result = json.loads(resp.text)['result']
            item_metrics.title = result['title']
            item_metrics.assigned_user_id = result['assigned_user_id']
        else:
            raise Exception('Error making API call response={}'.format(resp.status_code))

    except Exception as ex:
        msg = 'Error making request to Rollbar Get item API project={}'.format(proj.name)
        logging.error(msg, exc_info=ex)

        return item_metrics

    return


def process_result(proj: Project, result, output_csv_file, start_time_str, end_time_str):
    """
    Use this method to write metrics for Items in a Project to a CSV file

    Arguments:
    proj - A Project object (with name property set)
    result - A dict with metrics data for 1 or more Items
    output_csv_file - Name of teh CSV file to write results to
    start_time_str - A string that represents the start of the time window for the metrics
    end_time_str - A string that represents the end of the time window for the metrics
    """
    
    metric_rows = result['timepoints'][0]['metrics_rows']

    if len(metric_rows) == 0:
        msg = 'No rows for {} from {} to {}'.format(proj.name, start_time_str, end_time_str)
        logging.info(msg)
    
    for row_group in metric_rows:
        env = 'nothing'
        item_level = 'nothing'
        occ_count = 'nothing'
        
        for row in row_group:
            if row['field'] == 'environment':
                env = row['value']

            if row['field'] == 'item_level':
                item_level = row['value']

            if row['field'] == 'occurrence_count':
                occ_count = row['value']

        line = '{},{},{},{},{},{},{}\n'
        line = line.format(proj.name, proj.id, env, item_level,
                           occ_count, start_time_str, end_time_str)

        f = open(output_csv_file, 'a')
        f.writelines([line])
        f.close()

