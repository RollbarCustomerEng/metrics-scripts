"""
Use this script to get common Item metrics for all single Rollbar Project for the last 1 day

Usage:
python3 get_common_item_metrics.py

Output:
A CSV file with the metrics

Requirements:
1. 
The following environment variable needs to be set
ROLLBAR_PROJECT_READ_ACCESS_TOKEN - A project level token with Read scope
Example:
export ROLLBAR_PROJECT_READ_ACCESS_TOKEN=**********

"""

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
from metrics_base import get_item_metrics


#
# Get/Create your ROLLBAR_PROJECT_READ_ACCESS_TOKEN here
# https://rollbar.com/YOUR_ACCOUNT_SLUG/PROJECT_SLUG/settings/access_tokens/
#
# Execute this command from a terminal to create an environment variable with your access tokem
# export ROLLBAR_PROJECT_READ_ACCESS_TOKEN=**********
#
PROJECT_READ_TOKEN = os.environ['ROLLBAR_PROJECT_READ_ACCESS_TOKEN']






def print_metric_aggregates(item_metrics_list, environment_list, level_list):
    """
    Use this method to print some aggregation of metics data

    Arguments:
    item_metrics_list - A list of ItemMetrics objects
    environment_list -  A list of environment names e.g. staging, production etc.
    level_list - A list of Item Levels  ['debug', 'info'. 'warning', 'error', 'critical'] 
    """

    if len(item_metrics_list) == 0:
        logging.info('The ItemMetrics list is empty')
        return

    # Print additional aggregations as needed
    im: ItemMetrics
    env_occs = sum(im.occurrence_count for im in item_metrics_list if im.environment in environment_list)
    msg = 'Environments: {}, Levels: All, Occurrences: {}'.format(environment_list, env_occs)
    print(msg)

    error_occs = sum(im.occurrence_count for im in item_metrics_list \
                        if im.environment in environment_list and im.level in level_list)

    msg = 'Environments: {}, Levels: {}, Occurrences: {}'.format(environment_list, level_list, error_occs)
    print(msg)
    return


def write_metrics_to_csv(item_metrics_list):

    im: ItemMetrics

    line_list = []
    line_list.append(ItemMetrics.get_csv_column_headers())
    for im in item_metrics_list:
        print(im)
        line_list.append(im.get_csv_line())

    output_csv_file = 'item_metrics.csv'
    f = open(output_csv_file, 'a')
    f.writelines(line_list)
    f.close()



def process_single_project():
    """
    """

    final_time = datetime.datetime.now()
    # Get metrics for last x days
    start_time = final_time - datetime.timedelta(days=60)

    # convert times to unix epoch integers
    final_time_unix = math.floor(time.mktime(final_time.timetuple()))   
    start_time_unix = math.floor(time.mktime(start_time.timetuple()))

    proj = Project()
    proj.token = PROJECT_READ_TOKEN
    item_metrics_list = get_item_metrics(proj, start_time_unix, final_time_unix, add_assigned_users=True)

    write_metrics_to_csv(item_metrics_list)

    print('')
    print('Additional metrics aggregations')
    print('')
    print_metric_aggregates(item_metrics_list, ['production', 'qa'], ['error', 'critical'])
    print_metric_aggregates(item_metrics_list, ['qa'], ['info'])
    print_metric_aggregates(item_metrics_list, ['production'], ['info', 'debug'])

    print('Finished')

if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO,
                    format='%(process)d-%(levelname)s-%(message)s',
                    handlers=[logging.StreamHandler()]
                    )
    process_single_project()
