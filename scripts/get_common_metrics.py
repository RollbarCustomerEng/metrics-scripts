import json
import logging
import math
import requests
import os

import datetime, time

from metrics_base import Project
from metrics_base import ItemMetrics
import metrics_base as mb

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


def get_item_metrics(proj: Project, start_time_unix, end_time_unix):

    query = query_data = {
            # epoch time in seconds
            'start_time': start_time_unix,
            'end_time':  end_time_unix,
            'group_by': ['environment', 'item_id', 'item_counter', 'item_level', 'item_status'],
             'aggregates': [
                {
                    'field': 'ip_address',
                    'function': 'count_distinct',
                    'alias': 'ip_address_count'
                }
                ],
             'filters': [
              {
                'field': 'item_level',
                'values': ['error', 'critical', 'warning', 'info'],
                'operator': 'eq'
              }
              ]
            }
    result = mb.make_occ_metrics_api_call(proj, query_data)
    metrics_list = get_metrics_from_response(proj, result, start_time_unix, end_time_unix)

    # Add title and assigned_user_id - by calling Rollbar get_item API
    for im in metrics_list:
        mb.add_extra_info_to_metrics(proj, im)

    return metrics_list


def get_metrics_from_response(proj, result, start_time_unix, end_time_unix):

    metric_rows = result['timepoints'][0]['metrics_rows']

    if len(metric_rows) == 0:
        msg = 'No rows for the time range from {} to {}'.format(start_time_unix, end_time_unix)
        logging.info(msg)
    
    item_metrics_list = []
    for row_group in metric_rows:
        
        im = ItemMetrics()
        im.project_id = proj.id
        im.project_name = proj.name
        im.start_time_unix = start_time_unix
        im.end_time_unix = end_time_unix

        for row in row_group:

            if row['field'] == 'item_id':
                im.id = row['value']

            if row['field'] == 'item_counter':
                im.counter = row['value']

            if row['field'] == 'environment':
                im.environment = row['value']

            if row['field'] == 'item_level':
                im.level = row['value']

            if row['field'] == 'item_status':
                im.status = row['value']

            if row['field'] == 'occurrence_count':
                im.occurrence_count = row['value']

            if row['field'] == 'ip_address_count':
                im.ip_address_count = row['value']

        print(im.id, im.counter, im.environment, im.status, im.level, im.occurrence_count)
        item_metrics_list.append(im)

    return item_metrics_list

def aggregate_metrics(item_metrics_list: list[ItemMetrics], environment):

    # Print additional aggregations as needed
    im: ItemMetrics
    env_occs = sum(im.occurrence_count for im in item_metrics_list if im.environment == environment)
    env_occs = '{} occurrences {}'.format(environment, env_occs)
    print(env_occs)

    error_occs = sum(im.occurrence_count for im in item_metrics_list \
                        if im.environment == environment and im.level in ['error', 'critical'])

    error_occs = 'error/critical occurrences {}'.format(error_occs)
    print(error_occs)
    return


def process_all():

    final_time = datetime.datetime.now()
    # Get metrics for last x days
    start_time = final_time - datetime.timedelta(days=1)

    # convert times to unix epoch integers
    final_time_unix = math.floor(time.mktime(final_time.timetuple()))   
    start_time_unix = math.floor(time.mktime(start_time.timetuple()))

    proj_list = get_all_projects(ACCOUNT_READ_TOKEN)
    add_read_token_to_projects(proj_list, ACCOUNT_READ_TOKEN, ALLOWED_PROJECT_TOKEN_NAMES)

    for proj in proj_list:
        item_metrics_list = get_item_metrics(proj, start_time_unix, final_time_unix)
        aggregate_metrics(item_metrics_list, 'production')

    print('Finished')


if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO,
                    format='%(process)d-%(levelname)s-%(message)s',
                    handlers=[logging.StreamHandler()]
                    )
    process_all()
