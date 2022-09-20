"""
Use this script to get Muted Item Occurrence counts for a Rollbar Project in the last 1 day

Usage:
python3 get_muted_items.py

Output:
Prints the output to screen

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

import metrics_base as mb
from metrics_base import Project


#
# Get/Create your ROLLBAR_PROJECT_READ_ACCESS_TOKEN here
# https://rollbar.com/YOUR_ACCOUNT_SLUG/PROJECT_SLUG/settings/access_tokens/
#
# Execute this command from a terminal to create an environment variable with your access tokem
# export ROLLBAR_PROJECT_READ_ACCESS_TOKEN=**********
#
PROJECT_READ_TOKEN = os.environ['ROLLBAR_PROJECT_READ_ACCESS_TOKEN']

                

def get_start_and_final_time():

    # datetime.datetime.now(datetime.timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    final_time = datetime.datetime.now()
    start_time = final_time - datetime.timedelta(days=30)

    finaltime_unix = math.floor(time.mktime(final_time.timetuple()))   
    starttime_unix = math.floor(time.mktime(start_time.timetuple()))

    if starttime_unix >= finaltime_unix:
        raise ValueError('Start time needs to be less than the final time')

    return starttime_unix, finaltime_unix



def get_muted_items_by_env(proj, starttime_unix, endtime_unix):

    query_data = {
            # epoch time in seconds
            'start_time': starttime_unix,
            'end_time':  endtime_unix,
            'group_by': ['environment', 'item_level', 'item_status'],
             'filters': [
              {
                'field': 'item_level',
                'values': ['error', 'critical', 'warning', 'info', 'debug'],
                'operator': 'eq'
              },
              {
                'field': 'item_status',
                'values': ['mute'],
                'operator': 'eq'
              }
              ]
            }
    result = mb.make_occ_metrics_api_call(proj, query_data)

    return result



def print_muted_items():

    starttime_unix, finaltime_unix = get_start_and_final_time() 

    proj = Project()
    proj.token = PROJECT_READ_TOKEN
    result = get_muted_items_by_env(proj, starttime_unix, finaltime_unix)

    print(result)


if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO,
                    format='%(process)d-%(levelname)s-%(message)s',
                    handlers=[logging.StreamHandler()]
                    )
    print_muted_items()

    