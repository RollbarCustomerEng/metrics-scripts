"""
Use this script to get teh Item metrics for all your Rollbar Projects for the last 1 day

Usage:
python3 get_account_item_metrics.py

Output:
A CSV file with the metrics

Requirements:
1. 
The following environment variable needs to be set
ACCOUNT_READ_ACCESS_TOKEN_FOR_METRICS - An account level token with Read scope
Example:
export ACCOUNT_READ_ACCESS_TOKEN_FOR_METRICS=**********


2. 
For each Rollbar Project you want nmetrics for there must 
be a Read (ONLY) scope token with 1 of the following names

['read', 'metrics_api_token']

"""
import json
import logging
import requests
import os
import datetime, time

from metrics_base import get_all_projects
from metrics_base import add_read_token_to_projects


#
# Get/Create your ACCOUNT_READ_SCOPE_ACCESS_TOKEN here
# https://rollbar.com/settings/accounts/YOUR_ACCOUNT_SLUG/access_tokens/
#
# Execute these from a terminal to create an environment variable with you access tokem
# export ACCOUNT_READ_ACCESS_TOKEN_FOR_METRICS=**********
#
ACCOUNT_READ_TOKEN = os.environ['ACCOUNT_READ_ACCESS_TOKEN_FOR_METRICS']

#
# We only look for project_access_tokens with these names
# The project_access_tokens MUST be 'read' scope ONLY
#
ALLOWED_PROJECT_TOKEN_NAMES = ['read', 'metrics_api_token']


class Project:
    def __init__(self):
        self.id = None
        self.name = None
        self.token = None

def write_occurrence_metrics_to_csv(proj_list, start_unixtime, end_unixtime):
    #
    # Write the occurrences for all projects to 
    # results.csv in the current working directory
    #

    f = open('results.csv', 'w')
    line = 'Name,Id,Environment,Level,OccurrenceCount,StartTime,EndTime\n'
    f.write(line)
    f.close()

    proj: Project
    for proj in proj_list:
        result = make_occ_metrics_api_call(start_unixtime, end_unixtime, proj)
        try:
            process_result(proj, result, start_unixtime, end_unixtime)
        except Exception as ex:
            msg = 'Exception caclulating metrics for {}'.format(proj.name)
            logging.exception(msg, exc_info=ex)


def process_result(proj: Project, result, start_unixtime, end_unixtime):
    #
    # Write ccurrence data to results.csv for this project
    #
    
    metric_rows = result['timepoints'][0]['metrics_rows']
    
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
                           occ_count, int(start_unixtime), int(end_unixtime))

        f = open('results.csv', 'a')
        f.writelines([line])
        f.close()


def make_occ_metrics_api_call(start_time, end_time, proj: Project):
    """
    Call Rollbar Metrics API. 
    """
    try:
        
        url = 'https://api.rollbar.com/api/1/metrics/occurrences'
        headers = {'X-Rollbar-Access-Token': proj.token, 'Content-Type': 'application/json'}

        # Filter by environment and item_level
        data = {
            # epoch time in seconds
            'start_time': start_time,
            'end_time':  end_time,
            'group_by': ['environment', 'item_level'],
             'filters': [
              {
                'field': 'item_level',
                'values': ['error', 'critical', 'warning', 'info'],
                'operator': 'eq'
              }
              ]
            }

        # POST request
        resp = requests.post(url, json=data, headers=headers)
        log = '/api/1/metrics/occurrences proj={} status={}'.format(proj.name, resp.status_code)
        logging.info(log)

        result = json.loads(resp.text)['result']
        return result

    except Exception as ex:
        msg = 'Error making request to Rollbar Metrics API project={}'.format(proj.name)
        logging.error(msg, exc_info=ex)


def create_csv_for_all_projects(start_unixtime, end_unixtime):
    
    proj_list = get_all_projects(ACCOUNT_READ_TOKEN)
    add_read_token_to_projects(proj_list, ACCOUNT_READ_TOKEN, ALLOWED_PROJECT_TOKEN_NAMES)

    write_occurrence_metrics_to_csv(proj_list, start_unixtime, end_unixtime)


if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO,
                    format='%(process)d-%(levelname)s-%(message)s',
                    handlers=[logging.StreamHandler()]
                    )

    now = datetime.datetime.now() 
    last_week = now - datetime.timedelta(days=1)

    now_unix = time.mktime(now.timetuple())   
    last_week_unix = time.mktime(last_week.timetuple()) 

    create_csv_for_all_projects(last_week_unix, now_unix)

    


